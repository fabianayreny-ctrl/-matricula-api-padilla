import sqlite3

from fastapi import APIRouter, HTTPException, Query, status

from app.database import conexion_lectura, transaccion
from app.helpers import filas_a_lista, obtener_o_404
from app.schemas import CarreraEntrada, CarreraRespuesta, MensajeRespuesta


router = APIRouter(prefix="/carreras", tags=["Carreras"])


@router.get("", response_model=list[CarreraRespuesta])
def listar_carreras(
    buscar: str | None = Query(default=None, max_length=100),
    solo_activas: bool = False,
):
    condiciones: list[str] = []
    parametros: list[object] = []
    if buscar:
        condiciones.append("(codigo LIKE ? OR nombre LIKE ?)")
        patron = f"%{buscar}%"
        parametros.extend([patron, patron])
    if solo_activas:
        condiciones.append("activo = 1")

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    with conexion_lectura() as conexion:
        filas = conexion.execute(
            f"SELECT id, codigo, nombre, duracion_anios, activo "
            f"FROM carreras {where} ORDER BY nombre",
            parametros,
        ).fetchall()
    return filas_a_lista(filas)


@router.get("/{carrera_id}", response_model=CarreraRespuesta)
def obtener_carrera(carrera_id: int):
    with conexion_lectura() as conexion:
        return dict(obtener_o_404(conexion, "carreras", carrera_id, "Carrera"))


@router.post("", response_model=CarreraRespuesta, status_code=status.HTTP_201_CREATED)
def crear_carrera(datos: CarreraEntrada):
    try:
        with transaccion() as conexion:
            cursor = conexion.execute(
                """
                INSERT INTO carreras (codigo, nombre, duracion_anios, activo)
                VALUES (?, ?, ?, ?)
                """,
                (datos.codigo.upper(), datos.nombre, datos.duracion_anios, datos.activo),
            )
            fila = conexion.execute(
                "SELECT * FROM carreras WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            return dict(fila)
    except sqlite3.IntegrityError as error:
        raise HTTPException(409, "El código o nombre de la carrera ya existe") from error


@router.put("/{carrera_id}", response_model=CarreraRespuesta)
def actualizar_carrera(carrera_id: int, datos: CarreraEntrada):
    try:
        with transaccion() as conexion:
            obtener_o_404(conexion, "carreras", carrera_id, "Carrera")
            conexion.execute(
                """
                UPDATE carreras
                SET codigo = ?, nombre = ?, duracion_anios = ?, activo = ?
                WHERE id = ?
                """,
                (
                    datos.codigo.upper(),
                    datos.nombre,
                    datos.duracion_anios,
                    datos.activo,
                    carrera_id,
                ),
            )
            return dict(
                conexion.execute(
                    "SELECT * FROM carreras WHERE id = ?", (carrera_id,)
                ).fetchone()
            )
    except sqlite3.IntegrityError as error:
        raise HTTPException(409, "El código o nombre pertenece a otra carrera") from error


@router.delete("/{carrera_id}", response_model=MensajeRespuesta)
def eliminar_carrera(carrera_id: int):
    try:
        with transaccion() as conexion:
            obtener_o_404(conexion, "carreras", carrera_id, "Carrera")
            conexion.execute("DELETE FROM carreras WHERE id = ?", (carrera_id,))
        return {"mensaje": "Carrera eliminada correctamente"}
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            409, "No se puede eliminar: la carrera tiene estudiantes o asignaturas"
        ) from error

