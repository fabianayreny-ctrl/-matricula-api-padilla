from fastapi import APIRouter, HTTPException, Query

from app.database import conexion_lectura
from app.helpers import filas_a_lista, obtener_o_404


router = APIRouter(prefix="/reportes", tags=["Reportes y consultas avanzadas"])


@router.get("/dashboard")
def obtener_dashboard():
    with conexion_lectura() as conexion:
        periodo = conexion.execute(
            """
            SELECT id, anio, numero FROM periodos
            WHERE activo = 1 ORDER BY anio DESC, numero DESC LIMIT 1
            """
        ).fetchone()
        resumen = {
            "estudiantes_activos": conexion.execute(
                "SELECT COUNT(*) FROM estudiantes WHERE estado = 'ACTIVO'"
            ).fetchone()[0],
            "docentes_activos": conexion.execute(
                "SELECT COUNT(*) FROM docentes WHERE estado = 'ACTIVO'"
            ).fetchone()[0],
            "carreras_activas": conexion.execute(
                "SELECT COUNT(*) FROM carreras WHERE activo = 1"
            ).fetchone()[0],
            "asignaturas_activas": conexion.execute(
                "SELECT COUNT(*) FROM asignaturas WHERE activo = 1"
            ).fetchone()[0],
            "periodo_activo": (
                f"{periodo['anio']}-{periodo['numero']}" if periodo else None
            ),
            "secciones_abiertas": 0,
            "matriculas_activas": 0,
        }
        if periodo:
            resumen["secciones_abiertas"] = conexion.execute(
                """
                SELECT COUNT(*) FROM secciones
                WHERE periodo_id = ? AND estado = 'ABIERTA'
                """,
                (periodo["id"],),
            ).fetchone()[0]
            resumen["matriculas_activas"] = conexion.execute(
                """
                SELECT COUNT(*)
                FROM matriculas m
                JOIN secciones s ON s.id = m.seccion_id
                WHERE s.periodo_id = ? AND m.estado = 'MATRICULADA'
                """,
                (periodo["id"],),
            ).fetchone()[0]
    return resumen


@router.get("/historial-estudiante/{estudiante_id}")
def historial_estudiante(estudiante_id: int):
    with conexion_lectura() as conexion:
        estudiante = conexion.execute(
            """
            SELECT e.id, e.cuenta, e.nombres, e.apellidos, e.estado,
                   c.codigo AS carrera_codigo, c.nombre AS carrera_nombre
            FROM estudiantes e
            JOIN carreras c ON c.id = e.carrera_id
            WHERE e.id = ?
            """,
            (estudiante_id,),
        ).fetchone()
        if estudiante is None:
            raise HTTPException(404, "Estudiante no encontrado")

        historial = conexion.execute(
            """
            SELECT p.anio || '-' || p.numero AS periodo,
                   a.codigo AS asignatura_codigo, a.nombre AS asignatura,
                   a.unidades_valorativas, s.codigo AS seccion,
                   m.estado, cal.nota_final
            FROM matriculas m
            JOIN secciones s ON s.id = m.seccion_id
            JOIN asignaturas a ON a.id = s.asignatura_id
            JOIN periodos p ON p.id = s.periodo_id
            LEFT JOIN calificaciones cal ON cal.matricula_id = m.id
            WHERE m.estudiante_id = ?
            ORDER BY p.anio, p.numero, a.codigo
            """,
            (estudiante_id,),
        ).fetchall()

        uv_aprobadas = sum(
            fila["unidades_valorativas"]
            for fila in historial
            if fila["estado"] == "APROBADA"
        )
    return {
        "estudiante": dict(estudiante),
        "resumen": {
            "asignaturas_cursadas": len(historial),
            "unidades_valorativas_aprobadas": uv_aprobadas,
        },
        "historial": filas_a_lista(historial),
    }


@router.get("/lista-seccion/{seccion_id}")
def lista_seccion(seccion_id: int):
    with conexion_lectura() as conexion:
        seccion = conexion.execute(
            """
            SELECT s.id, a.codigo AS asignatura_codigo, a.nombre AS asignatura,
                   s.codigo AS seccion, p.anio || '-' || p.numero AS periodo,
                   d.nombres || ' ' || d.apellidos AS docente,
                   s.cupo_maximo
            FROM secciones s
            JOIN asignaturas a ON a.id = s.asignatura_id
            JOIN periodos p ON p.id = s.periodo_id
            JOIN docentes d ON d.id = s.docente_id
            WHERE s.id = ?
            """,
            (seccion_id,),
        ).fetchone()
        if seccion is None:
            raise HTTPException(404, "Sección no encontrada")

        estudiantes = conexion.execute(
            """
            SELECT m.id AS matricula_id, e.cuenta,
                   e.nombres || ' ' || e.apellidos AS estudiante,
                   e.correo, m.estado, c.nota_final
            FROM matriculas m
            JOIN estudiantes e ON e.id = m.estudiante_id
            LEFT JOIN calificaciones c ON c.matricula_id = m.id
            WHERE m.seccion_id = ? AND m.estado <> 'CANCELADA'
            ORDER BY e.apellidos, e.nombres
            """,
            (seccion_id,),
        ).fetchall()
    return {
        "seccion": dict(seccion),
        "cantidad_matriculados": len(estudiantes),
        "cupos_disponibles": seccion["cupo_maximo"] - len(estudiantes),
        "estudiantes": filas_a_lista(estudiantes),
    }


@router.get("/carga-docente/{docente_id}")
def carga_docente(
    docente_id: int,
    periodo_id: int | None = Query(default=None, gt=0),
):
    with conexion_lectura() as conexion:
        docente = obtener_o_404(conexion, "docentes", docente_id, "Docente")
        parametros: list[object] = [docente_id]
        filtro = ""
        if periodo_id:
            filtro = "AND s.periodo_id = ?"
            parametros.append(periodo_id)
        secciones = conexion.execute(
            f"""
            SELECT s.id, a.codigo AS asignatura_codigo, a.nombre AS asignatura,
                   s.codigo AS seccion, p.anio || '-' || p.numero AS periodo,
                   s.dias, s.hora_inicio, s.hora_fin,
                   COUNT(CASE WHEN m.estado <> 'CANCELADA' THEN 1 END) AS estudiantes
            FROM secciones s
            JOIN asignaturas a ON a.id = s.asignatura_id
            JOIN periodos p ON p.id = s.periodo_id
            LEFT JOIN matriculas m ON m.seccion_id = s.id
            WHERE s.docente_id = ? {filtro}
            GROUP BY s.id, a.codigo, a.nombre, s.codigo, p.anio, p.numero,
                     s.dias, s.hora_inicio, s.hora_fin
            ORDER BY p.anio DESC, p.numero DESC, s.hora_inicio
            """,
            parametros,
        ).fetchall()
    return {
        "docente": {
            "id": docente["id"],
            "numero_empleado": docente["numero_empleado"],
            "nombre": f"{docente['nombres']} {docente['apellidos']}",
        },
        "total_secciones": len(secciones),
        "secciones": filas_a_lista(secciones),
    }

