import sqlite3

from fastapi import APIRouter, HTTPException, status

from app.database import conexion_lectura, transaccion
from app.helpers import obtener_o_404
from app.schemas import MensajeRespuesta, PeriodoEntrada, PeriodoRespuesta


router = APIRouter(prefix="/periodos", tags=["Períodos académicos"])


def _periodo_respuesta(fila) -> dict:
    datos = dict(fila)
    datos["nombre"] = f"{datos['anio']}-{datos['numero']}"
    return datos


@router.get("", response_model=list[PeriodoRespuesta])
def listar_periodos():
    with conexion_lectura() as conexion:
        filas = conexion.execute(
            "SELECT * FROM periodos ORDER BY anio DESC, numero DESC"
        ).fetchall()
    return [_periodo_respuesta(fila) for fila in filas]


@router.get("/{periodo_id}", response_model=PeriodoRespuesta)
def obtener_periodo(periodo_id: int):
    with conexion_lectura() as conexion:
        fila = obtener_o_404(conexion, "periodos", periodo_id, "Período")
        return _periodo_respuesta(fila)


def _desactivar_otros(conexion, periodo_id: int | None = None) -> None:
    if periodo_id is None:
        conexion.execute("UPDATE periodos SET activo = 0")
    else:
        conexion.execute("UPDATE periodos SET activo = 0 WHERE id <> ?", (periodo_id,))


@router.post("", response_model=PeriodoRespuesta, status_code=status.HTTP_201_CREATED)
def crear_periodo(datos: PeriodoEntrada):
    try:
        with transaccion() as conexion:
            if datos.activo:
                _desactivar_otros(conexion)
            cursor = conexion.execute(
                """
                INSERT INTO periodos
                    (anio, numero, fecha_inicio, fecha_fin, activo)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datos.anio,
                    datos.numero,
                    datos.fecha_inicio.isoformat(),
                    datos.fecha_fin.isoformat(),
                    datos.activo,
                ),
            )
            fila = conexion.execute(
                "SELECT * FROM periodos WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            return _periodo_respuesta(fila)
    except sqlite3.IntegrityError as error:
        raise HTTPException(409, "Ese período académico ya existe") from error


@router.put("/{periodo_id}", response_model=PeriodoRespuesta)
def actualizar_periodo(periodo_id: int, datos: PeriodoEntrada):
    try:
        with transaccion() as conexion:
            obtener_o_404(conexion, "periodos", periodo_id, "Período")
            if datos.activo:
                _desactivar_otros(conexion, periodo_id)
            conexion.execute(
                """
                UPDATE periodos
                SET anio = ?, numero = ?, fecha_inicio = ?, fecha_fin = ?, activo = ?
                WHERE id = ?
                """,
                (
                    datos.anio,
                    datos.numero,
                    datos.fecha_inicio.isoformat(),
                    datos.fecha_fin.isoformat(),
                    datos.activo,
                    periodo_id,
                ),
            )
            fila = conexion.execute(
                "SELECT * FROM periodos WHERE id = ?", (periodo_id,)
            ).fetchone()
            return _periodo_respuesta(fila)
    except sqlite3.IntegrityError as error:
        raise HTTPException(409, "Ese período académico ya existe") from error


@router.delete("/{periodo_id}", response_model=MensajeRespuesta)
def eliminar_periodo(periodo_id: int):
    try:
        with transaccion() as conexion:
            obtener_o_404(conexion, "periodos", periodo_id, "Período")
            conexion.execute("DELETE FROM periodos WHERE id = ?", (periodo_id,))
        return {"mensaje": "Período eliminado correctamente"}
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            409, "No se puede eliminar: el período tiene secciones"
        ) from error

