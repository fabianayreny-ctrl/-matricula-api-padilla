import sqlite3

from fastapi import APIRouter, HTTPException, Query, status

from app.database import conexion_lectura, transaccion
from app.helpers import filas_a_lista, obtener_o_404
from app.schemas import EstudianteEntrada, EstudianteRespuesta, MensajeRespuesta


router = APIRouter(prefix="/estudiantes", tags=["Estudiantes"])


CONSULTA_BASE = """
    SELECT e.id, e.cuenta, e.nombres, e.apellidos, e.correo, e.telefono,
           e.fecha_nacimiento, e.carrera_id, e.estado,
           c.codigo AS carrera_codigo, c.nombre AS carrera_nombre
    FROM estudiantes e
    JOIN carreras c ON c.id = e.carrera_id
"""


def _validar_carrera(conexion, carrera_id: int) -> None:
    carrera = obtener_o_404(conexion, "carreras", carrera_id, "Carrera")
    if not carrera["activo"]:
        raise HTTPException(409, "No se puede asignar una carrera inactiva")


@router.get("", response_model=list[EstudianteRespuesta])
def listar_estudiantes(
    buscar: str | None = Query(default=None, max_length=100),
    carrera_id: int | None = Query(default=None, gt=0),
    estado: str | None = Query(
        default=None, pattern="^(ACTIVO|INACTIVO|GRADUADO)$"
    ),
    limite: int = Query(default=50, ge=1, le=100),
    desplazamiento: int = Query(default=0, ge=0),
):
    condiciones: list[str] = []
    parametros: list[object] = []
    if buscar:
        condiciones.append(
            "(e.cuenta LIKE ? OR e.nombres LIKE ? OR e.apellidos LIKE ? "
            "OR e.correo LIKE ?)"
        )
        patron = f"%{buscar}%"
        parametros.extend([patron] * 4)
    if carrera_id:
        condiciones.append("e.carrera_id = ?")
        parametros.append(carrera_id)
    if estado:
        condiciones.append("e.estado = ?")
        parametros.append(estado)

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    parametros.extend([limite, desplazamiento])
    with conexion_lectura() as conexion:
        filas = conexion.execute(
            f"{CONSULTA_BASE} {where} "
            "ORDER BY e.apellidos, e.nombres LIMIT ? OFFSET ?",
            parametros,
        ).fetchall()
    return filas_a_lista(filas)


@router.get("/{estudiante_id}", response_model=EstudianteRespuesta)
def obtener_estudiante(estudiante_id: int):
    with conexion_lectura() as conexion:
        fila = conexion.execute(
            f"{CONSULTA_BASE} WHERE e.id = ?", (estudiante_id,)
        ).fetchone()
    if fila is None:
        raise HTTPException(404, "Estudiante no encontrado")
    return dict(fila)


@router.post(
    "", response_model=EstudianteRespuesta, status_code=status.HTTP_201_CREATED
)
def crear_estudiante(datos: EstudianteEntrada):
    try:
        with transaccion() as conexion:
            _validar_carrera(conexion, datos.carrera_id)
            cursor = conexion.execute(
                """
                INSERT INTO estudiantes
                    (cuenta, nombres, apellidos, correo, telefono,
                     fecha_nacimiento, carrera_id, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datos.cuenta,
                    datos.nombres,
                    datos.apellidos,
                    str(datos.correo).lower(),
                    datos.telefono,
                    datos.fecha_nacimiento.isoformat(),
                    datos.carrera_id,
                    datos.estado,
                ),
            )
            fila = conexion.execute(
                f"{CONSULTA_BASE} WHERE e.id = ?", (cursor.lastrowid,)
            ).fetchone()
            return dict(fila)
    except sqlite3.IntegrityError as error:
        raise HTTPException(409, "La cuenta o el correo ya están registrados") from error

@router.get("/{estudiante_id}/matriculas")
def listar_matriculas_estudiante(estudiante_id: int):
    with conexion_lectura() as conexion:
        # Verificar que el estudiante exista
        estudiante = conexion.execute(
            "SELECT id, cuenta, nombres, apellidos "
            "FROM estudiantes WHERE id = ?",
            (estudiante_id,),
        ).fetchone()

        if estudiante is None:
            raise HTTPException(404, "Estudiante no encontrado")

        # Obtener las asignaturas en las que está matriculado
        filas = conexion.execute(
            """
            SELECT
                m.id AS matricula_id,
                a.id AS asignatura_id,
                a.codigo AS asignatura_codigo,
                a.nombre AS asignatura_nombre,
                m.fecha_matricula,
                m.estado
            FROM matriculas m
            JOIN secciones s ON s.id = m.seccion_id
            JOIN asignaturas a ON a.id = s.asignatura_id
            WHERE m.estudiante_id = ?
            ORDER BY a.codigo
            """,
            (estudiante_id,),
        ).fetchall()

    return {
        "estudiante": dict(estudiante),
        "matriculas": [dict(fila) for fila in filas],
    } 

@router.put("/{estudiante_id}", response_model=EstudianteRespuesta)
def actualizar_estudiante(estudiante_id: int, datos: EstudianteEntrada):
    try:
        with transaccion() as conexion:
            obtener_o_404(conexion, "estudiantes", estudiante_id, "Estudiante")
            _validar_carrera(conexion, datos.carrera_id)
            conexion.execute(
                """
                UPDATE estudiantes
                SET cuenta = ?, nombres = ?, apellidos = ?, correo = ?,
                    telefono = ?, fecha_nacimiento = ?, carrera_id = ?, estado = ?
                WHERE id = ?
                """,
                (
                    datos.cuenta,
                    datos.nombres,
                    datos.apellidos,
                    str(datos.correo).lower(),
                    datos.telefono,
                    datos.fecha_nacimiento.isoformat(),
                    datos.carrera_id,
                    datos.estado,
                    estudiante_id,
                ),
            )
            fila = conexion.execute(
                f"{CONSULTA_BASE} WHERE e.id = ?", (estudiante_id,)
            ).fetchone()
            return dict(fila)
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            409, "La cuenta o el correo pertenecen a otro estudiante"
        ) from error


@router.delete("/{estudiante_id}", response_model=MensajeRespuesta)
def eliminar_estudiante(estudiante_id: int):
    try:
        with transaccion() as conexion:
            obtener_o_404(conexion, "estudiantes", estudiante_id, "Estudiante")
            conexion.execute("DELETE FROM estudiantes WHERE id = ?", (estudiante_id,))
        return {"mensaje": "Estudiante eliminado correctamente"}
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            409,
            "No se puede eliminar: el estudiante tiene historial de matrículas. "
            "Puede cambiar su estado a INACTIVO.",
        ) from error

