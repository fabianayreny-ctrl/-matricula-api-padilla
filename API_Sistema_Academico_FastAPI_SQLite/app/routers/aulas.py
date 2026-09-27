import sqlite3

from fastapi import APIRouter, HTTPException, status

from app.database import conexion_lectura, transaccion
from app.helpers import filas_a_lista, obtener_o_404
from app.schemas import AulaEntrada, AulaRespuesta, MensajeRespuesta


router = APIRouter(prefix="/aulas", tags=["Aulas"])


@router.get("", response_model=list[AulaRespuesta])
def listar_aulas(solo_activas: bool = False):
    where = "WHERE activo = 1" if solo_activas else ""
    with conexion_lectura() as conexion:
        filas = conexion.execute(
            f"SELECT id, codigo, edificio, capacidad, activo "
            f"FROM aulas {where} ORDER BY edificio, codigo"
        ).fetchall()
    return filas_a_lista(filas)


@router.get("/{aula_id}", response_model=AulaRespuesta)
def obtener_aula(aula_id: int):
    with conexion_lectura() as conexion:
        return dict(obtener_o_404(conexion, "aulas", aula_id, "Aula"))


@router.post("", response_model=AulaRespuesta, status_code=status.HTTP_201_CREATED)
def crear_aula(datos: AulaEntrada):
    try:
        with transaccion() as conexion:
            cursor = conexion.execute(
                """
                INSERT INTO aulas (codigo, edificio, capacidad, activo)
                VALUES (?, ?, ?, ?)
                """,
                (datos.codigo.upper(), datos.edificio, datos.capacidad, datos.activo),
            )
            return dict(
                conexion.execute(
                    "SELECT * FROM aulas WHERE id = ?", (cursor.lastrowid,)
                ).fetchone()
            )
    except sqlite3.IntegrityError as error:
        raise HTTPException(409, "El código del aula ya existe") from error


@router.put("/{aula_id}", response_model=AulaRespuesta)
def actualizar_aula(aula_id: int, datos: AulaEntrada):
    try:
        with transaccion() as conexion:
            obtener_o_404(conexion, "aulas", aula_id, "Aula")
            conexion.execute(
                """
                UPDATE aulas SET codigo = ?, edificio = ?, capacidad = ?, activo = ?
                WHERE id = ?
                """,
                (
                    datos.codigo.upper(),
                    datos.edificio,
                    datos.capacidad,
                    datos.activo,
                    aula_id,
                ),
            )
            return dict(
                conexion.execute(
                    "SELECT * FROM aulas WHERE id = ?", (aula_id,)
                ).fetchone()
            )
    except sqlite3.IntegrityError as error:
        raise HTTPException(409, "El código pertenece a otra aula") from error


@router.delete("/{aula_id}", response_model=MensajeRespuesta)
def eliminar_aula(aula_id: int):
    with transaccion() as conexion:
        obtener_o_404(conexion, "aulas", aula_id, "Aula")
        # ON DELETE SET NULL permite conservar la sección aunque desaparezca el aula.
        conexion.execute("DELETE FROM aulas WHERE id = ?", (aula_id,))
    return {"mensaje": "Aula eliminada; sus secciones quedaron sin aula asignada"}

