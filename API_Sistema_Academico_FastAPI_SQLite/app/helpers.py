import sqlite3
from typing import Any

from fastapi import HTTPException


def fila_a_dict(fila: sqlite3.Row | None) -> dict[str, Any] | None:
    return dict(fila) if fila is not None else None


def filas_a_lista(filas: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(fila) for fila in filas]


def obtener_o_404(
    conexion: sqlite3.Connection,
    tabla: str,
    registro_id: int,
    nombre_recurso: str,
) -> sqlite3.Row:
    fila = conexion.execute(
        f"SELECT * FROM {tabla} WHERE id = ?", (registro_id,)
    ).fetchone()
    if fila is None:
        raise HTTPException(status_code=404, detail=f"{nombre_recurso} no encontrado")
    return fila


def conflicto_integridad(error: sqlite3.IntegrityError, mensaje: str) -> HTTPException:
    return HTTPException(status_code=409, detail=mensaje)

