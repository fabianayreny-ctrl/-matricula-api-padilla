import sqlite3

from fastapi import APIRouter, HTTPException, Query, status

from app.database import conexion_lectura, transaccion
from app.helpers import filas_a_lista, obtener_o_404
from app.schemas import MensajeRespuesta, SeccionEntrada, SeccionRespuesta
from app.services.horarios import validar_choques_seccion


router = APIRouter(prefix="/secciones", tags=["Secciones"])


CONSULTA_BASE = """
    SELECT s.id, s.codigo, s.asignatura_id, s.docente_id, s.periodo_id,
           s.aula_id, s.dias, s.hora_inicio, s.hora_fin, s.cupo_maximo,
           s.estado, a.codigo AS asignatura_codigo,
           a.nombre AS asignatura_nombre,
           d.nombres || ' ' || d.apellidos AS docente_nombre,
           p.anio || '-' || p.numero AS periodo_nombre,
           au.codigo AS aula_codigo,
           COUNT(CASE WHEN m.estado <> 'CANCELADA' THEN 1 END) AS matriculados,
           s.cupo_maximo - COUNT(
               CASE WHEN m.estado <> 'CANCELADA' THEN 1 END
           ) AS cupos_disponibles
    FROM secciones s
    JOIN asignaturas a ON a.id = s.asignatura_id
    JOIN docentes d ON d.id = s.docente_id
    JOIN periodos p ON p.id = s.periodo_id
    LEFT JOIN aulas au ON au.id = s.aula_id
    LEFT JOIN matriculas m ON m.seccion_id = s.id
"""


AGRUPACION = """
    GROUP BY s.id, s.codigo, s.asignatura_id, s.docente_id, s.periodo_id,
             s.aula_id, s.dias, s.hora_inicio, s.hora_fin, s.cupo_maximo,
             s.estado, a.codigo, a.nombre, d.nombres, d.apellidos,
             p.anio, p.numero, au.codigo
"""


def _validar_relaciones(conexion, datos: SeccionEntrada, seccion_id=None) -> None:
    asignatura = obtener_o_404(
        conexion, "asignaturas", datos.asignatura_id, "Asignatura"
    )
    docente = obtener_o_404(conexion, "docentes", datos.docente_id, "Docente")
    obtener_o_404(conexion, "periodos", datos.periodo_id, "Período")

    if not asignatura["activo"]:
        raise HTTPException(409, "La asignatura está inactiva")
    if docente["estado"] != "ACTIVO":
        raise HTTPException(409, "El docente está inactivo")

    if datos.aula_id is not None:
        aula = obtener_o_404(conexion, "aulas", datos.aula_id, "Aula")
        if not aula["activo"]:
            raise HTTPException(409, "El aula está inactiva")
        if datos.cupo_maximo > aula["capacidad"]:
            raise HTTPException(
                409, f"El cupo supera la capacidad del aula ({aula['capacidad']})"
            )

    validar_choques_seccion(
        conexion,
        datos.periodo_id,
        datos.docente_id,
        datos.aula_id,
        datos.dias.upper(),
        datos.hora_inicio,
        datos.hora_fin,
        seccion_id,
    )


@router.get("", response_model=list[SeccionRespuesta])
def listar_secciones(
    periodo_id: int | None = Query(default=None, gt=0),
    asignatura_id: int | None = Query(default=None, gt=0),
    docente_id: int | None = Query(default=None, gt=0),
    estado: str | None = Query(
        default=None, pattern="^(ABIERTA|CERRADA|FINALIZADA)$"
    ),
):
    condiciones: list[str] = []
    parametros: list[object] = []
    for columna, valor in (
        ("s.periodo_id", periodo_id),
        ("s.asignatura_id", asignatura_id),
        ("s.docente_id", docente_id),
    ):
        if valor:
            condiciones.append(f"{columna} = ?")
            parametros.append(valor)
    if estado:
        condiciones.append("s.estado = ?")
        parametros.append(estado)
    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""

    with conexion_lectura() as conexion:
        filas = conexion.execute(
            f"{CONSULTA_BASE} {where} {AGRUPACION} "
            "ORDER BY p.anio DESC, p.numero DESC, a.codigo, s.codigo",
            parametros,
        ).fetchall()
    return filas_a_lista(filas)


@router.get("/disponibles", response_model=list[SeccionRespuesta])
def listar_secciones_disponibles(periodo_id: int | None = Query(default=None, gt=0)):
    condiciones = ["s.estado = 'ABIERTA'", "p.activo = 1"]
    parametros: list[object] = []
    if periodo_id:
        condiciones.append("s.periodo_id = ?")
        parametros.append(periodo_id)
    where = f"WHERE {' AND '.join(condiciones)}"
    with conexion_lectura() as conexion:
        filas = conexion.execute(
            f"{CONSULTA_BASE} {where} {AGRUPACION} "
            "HAVING cupos_disponibles > 0 ORDER BY a.codigo, s.codigo",
            parametros,
        ).fetchall()
    return filas_a_lista(filas)


@router.get("/{seccion_id}", response_model=SeccionRespuesta)
def obtener_seccion(seccion_id: int):
    with conexion_lectura() as conexion:
        fila = conexion.execute(
            f"{CONSULTA_BASE} WHERE s.id = ? {AGRUPACION}", (seccion_id,)
        ).fetchone()
    if fila is None:
        raise HTTPException(404, "Sección no encontrada")
    return dict(fila)


@router.post("", response_model=SeccionRespuesta, status_code=status.HTTP_201_CREATED)
def crear_seccion(datos: SeccionEntrada):
    try:
        with transaccion() as conexion:
            _validar_relaciones(conexion, datos)
            cursor = conexion.execute(
                """
                INSERT INTO secciones
                    (codigo, asignatura_id, docente_id, periodo_id, aula_id,
                     dias, hora_inicio, hora_fin, cupo_maximo, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datos.codigo.upper(),
                    datos.asignatura_id,
                    datos.docente_id,
                    datos.periodo_id,
                    datos.aula_id,
                    datos.dias.upper(),
                    datos.hora_inicio,
                    datos.hora_fin,
                    datos.cupo_maximo,
                    datos.estado,
                ),
            )
            fila = conexion.execute(
                f"{CONSULTA_BASE} WHERE s.id = ? {AGRUPACION}",
                (cursor.lastrowid,),
            ).fetchone()
            return dict(fila)
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            409, "Ya existe esa sección de la asignatura en el período"
        ) from error


@router.put("/{seccion_id}", response_model=SeccionRespuesta)
def actualizar_seccion(seccion_id: int, datos: SeccionEntrada):
    try:
        with transaccion() as conexion:
            obtener_o_404(conexion, "secciones", seccion_id, "Sección")
            matriculados = conexion.execute(
                """
                SELECT COUNT(*) FROM matriculas
                WHERE seccion_id = ? AND estado <> 'CANCELADA'
                """,
                (seccion_id,),
            ).fetchone()[0]
            if datos.cupo_maximo < matriculados:
                raise HTTPException(
                    409, f"El cupo no puede ser menor que los {matriculados} matriculados"
                )
            _validar_relaciones(conexion, datos, seccion_id)
            conexion.execute(
                """
                UPDATE secciones
                SET codigo = ?, asignatura_id = ?, docente_id = ?, periodo_id = ?,
                    aula_id = ?, dias = ?, hora_inicio = ?, hora_fin = ?,
                    cupo_maximo = ?, estado = ?
                WHERE id = ?
                """,
                (
                    datos.codigo.upper(),
                    datos.asignatura_id,
                    datos.docente_id,
                    datos.periodo_id,
                    datos.aula_id,
                    datos.dias.upper(),
                    datos.hora_inicio,
                    datos.hora_fin,
                    datos.cupo_maximo,
                    datos.estado,
                    seccion_id,
                ),
            )
            fila = conexion.execute(
                f"{CONSULTA_BASE} WHERE s.id = ? {AGRUPACION}", (seccion_id,)
            ).fetchone()
            return dict(fila)
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            409, "Ya existe esa sección de la asignatura en el período"
        ) from error


@router.delete("/{seccion_id}", response_model=MensajeRespuesta)
def eliminar_seccion(seccion_id: int):
    try:
        with transaccion() as conexion:
            obtener_o_404(conexion, "secciones", seccion_id, "Sección")
            conexion.execute("DELETE FROM secciones WHERE id = ?", (seccion_id,))
        return {"mensaje": "Sección eliminada correctamente"}
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            409, "No se puede eliminar: la sección tiene estudiantes matriculados"
        ) from error

