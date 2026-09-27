from fastapi import APIRouter, HTTPException, Query, status

from app.database import conexion_lectura, transaccion
from app.helpers import filas_a_lista, obtener_o_404
from app.schemas import MatriculaEntrada, MatriculaRespuesta, MensajeRespuesta
from app.services.matricula_service import validar_nueva_matricula


router = APIRouter(prefix="/matriculas", tags=["Matrículas"])


CONSULTA_BASE = """
    SELECT m.id, m.estudiante_id, e.cuenta AS estudiante_cuenta,
           e.nombres || ' ' || e.apellidos AS estudiante_nombre,
           m.seccion_id, a.codigo AS asignatura_codigo,
           a.nombre AS asignatura_nombre, s.codigo AS seccion_codigo,
           p.anio || '-' || p.numero AS periodo_nombre,
           m.fecha_matricula, m.estado
    FROM matriculas m
    JOIN estudiantes e ON e.id = m.estudiante_id
    JOIN secciones s ON s.id = m.seccion_id
    JOIN asignaturas a ON a.id = s.asignatura_id
    JOIN periodos p ON p.id = s.periodo_id
"""


@router.get("", response_model=list[MatriculaRespuesta])
def listar_matriculas(
    estudiante_id: int | None = Query(default=None, gt=0),
    seccion_id: int | None = Query(default=None, gt=0),
    periodo_id: int | None = Query(default=None, gt=0),
    estado: str | None = Query(
        default=None,
        pattern="^(MATRICULADA|CANCELADA|APROBADA|REPROBADA)$",
    ),
):
    condiciones: list[str] = []
    parametros: list[object] = []
    for columna, valor in (
        ("m.estudiante_id", estudiante_id),
        ("m.seccion_id", seccion_id),
        ("s.periodo_id", periodo_id),
    ):
        if valor:
            condiciones.append(f"{columna} = ?")
            parametros.append(valor)
    if estado:
        condiciones.append("m.estado = ?")
        parametros.append(estado)
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    with conexion_lectura() as conexion:
        filas = conexion.execute(
            f"{CONSULTA_BASE} {where} "
            "ORDER BY p.anio DESC, p.numero DESC, a.codigo, e.apellidos",
            parametros,
        ).fetchall()
    return filas_a_lista(filas)


@router.get("/{matricula_id}", response_model=MatriculaRespuesta)
def obtener_matricula(matricula_id: int):
    with conexion_lectura() as conexion:
        fila = conexion.execute(
            f"{CONSULTA_BASE} WHERE m.id = ?", (matricula_id,)
        ).fetchone()
    if fila is None:
        raise HTTPException(404, "Matrícula no encontrada")
    return dict(fila)


@router.post(
    "", response_model=MatriculaRespuesta, status_code=status.HTTP_201_CREATED
)
def crear_matricula(datos: MatriculaEntrada):
    with transaccion() as conexion:
        existente = conexion.execute(
            """
            SELECT * FROM matriculas
            WHERE estudiante_id = ? AND seccion_id = ?
            """,
            (datos.estudiante_id, datos.seccion_id),
        ).fetchone()
        if existente is not None and existente["estado"] != "CANCELADA":
            raise HTTPException(409, "El estudiante ya está matriculado en la sección")

        validar_nueva_matricula(conexion, datos.estudiante_id, datos.seccion_id)

        if existente is not None:
            matricula_id = existente["id"]
            conexion.execute(
                """
                UPDATE matriculas
                SET estado = 'MATRICULADA', fecha_matricula = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (matricula_id,),
            )
        else:
            cursor = conexion.execute(
                """
                INSERT INTO matriculas (estudiante_id, seccion_id)
                VALUES (?, ?)
                """,
                (datos.estudiante_id, datos.seccion_id),
            )
            matricula_id = cursor.lastrowid

        fila = conexion.execute(
            f"{CONSULTA_BASE} WHERE m.id = ?", (matricula_id,)
        ).fetchone()
        return dict(fila)


@router.patch("/{matricula_id}/cancelar", response_model=MensajeRespuesta)
def cancelar_matricula(matricula_id: int):
    with transaccion() as conexion:
        matricula = obtener_o_404(
            conexion, "matriculas", matricula_id, "Matrícula"
        )
        if matricula["estado"] != "MATRICULADA":
            raise HTTPException(
                409, "Solo se puede cancelar una matrícula que está activa"
            )
        conexion.execute(
            "UPDATE matriculas SET estado = 'CANCELADA' WHERE id = ?",
            (matricula_id,),
        )
    return {"mensaje": "Matrícula cancelada; el cupo quedó disponible"}


@router.delete("/{matricula_id}", response_model=MensajeRespuesta)
def eliminar_matricula(matricula_id: int):
    """Ruta didáctica; en producción normalmente se conservaría el historial."""
    with transaccion() as conexion:
        obtener_o_404(conexion, "matriculas", matricula_id, "Matrícula")
        conexion.execute("DELETE FROM matriculas WHERE id = ?", (matricula_id,))
    return {"mensaje": "Matrícula y su calificación fueron eliminadas"}

