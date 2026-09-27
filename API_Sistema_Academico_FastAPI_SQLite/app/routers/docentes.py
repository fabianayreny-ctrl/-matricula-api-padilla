import sqlite3

from fastapi import APIRouter, HTTPException, Query, status

from app.database import conexion_lectura, transaccion
from app.helpers import filas_a_lista, obtener_o_404
from app.schemas import DocenteEntrada, DocenteRespuesta, MensajeRespuesta


router = APIRouter(prefix="/docentes", tags=["Docentes"])


@router.get("", response_model=list[DocenteRespuesta])
def listar_docentes(
    buscar: str | None = Query(default=None, max_length=100),
    estado: str | None = Query(default=None, pattern="^(ACTIVO|INACTIVO)$"),
):
    condiciones: list[str] = []
    parametros: list[object] = []
    if buscar:
        condiciones.append(
            "(numero_empleado LIKE ? OR nombres LIKE ? OR apellidos LIKE ? "
            "OR especialidad LIKE ?)"
        )
        patron = f"%{buscar}%"
        parametros.extend([patron] * 4)
    if estado:
        condiciones.append("estado = ?")
        parametros.append(estado)

    where = f"WHERE {' AND '.join(condiciones)}" if condiciones else ""
    with conexion_lectura() as conexion:
        filas = conexion.execute(
            f"""
            SELECT id, numero_empleado, nombres, apellidos, correo,
                   especialidad, estado
            FROM docentes {where}
            ORDER BY apellidos, nombres
            """,
            parametros,
        ).fetchall()
    return filas_a_lista(filas)


@router.get("/{docente_id}", response_model=DocenteRespuesta)
def obtener_docente(docente_id: int):
    with conexion_lectura() as conexion:
        return dict(obtener_o_404(conexion, "docentes", docente_id, "Docente"))


@router.post("", response_model=DocenteRespuesta, status_code=status.HTTP_201_CREATED)
def crear_docente(datos: DocenteEntrada):
    try:
        with transaccion() as conexion:
            cursor = conexion.execute(
                """
                INSERT INTO docentes
                    (numero_empleado, nombres, apellidos, correo, especialidad, estado)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    datos.numero_empleado.upper(),
                    datos.nombres,
                    datos.apellidos,
                    str(datos.correo).lower(),
                    datos.especialidad,
                    datos.estado,
                ),
            )
            return dict(
                conexion.execute(
                    "SELECT * FROM docentes WHERE id = ?", (cursor.lastrowid,)
                ).fetchone()
            )
    except sqlite3.IntegrityError as error:
        raise HTTPException(409, "El número de empleado o correo ya existe") from error


@router.put("/{docente_id}", response_model=DocenteRespuesta)
def actualizar_docente(docente_id: int, datos: DocenteEntrada):
    try:
        with transaccion() as conexion:
            obtener_o_404(conexion, "docentes", docente_id, "Docente")
            conexion.execute(
                """
                UPDATE docentes
                SET numero_empleado = ?, nombres = ?, apellidos = ?, correo = ?,
                    especialidad = ?, estado = ?
                WHERE id = ?
                """,
                (
                    datos.numero_empleado.upper(),
                    datos.nombres,
                    datos.apellidos,
                    str(datos.correo).lower(),
                    datos.especialidad,
                    datos.estado,
                    docente_id,
                ),
            )
            return dict(
                conexion.execute(
                    "SELECT * FROM docentes WHERE id = ?", (docente_id,)
                ).fetchone()
            )
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            409, "El número de empleado o correo pertenece a otro docente"
        ) from error


@router.delete("/{docente_id}", response_model=MensajeRespuesta)
def eliminar_docente(docente_id: int):
    try:
        with transaccion() as conexion:
            obtener_o_404(conexion, "docentes", docente_id, "Docente")
            conexion.execute("DELETE FROM docentes WHERE id = ?", (docente_id,))
        return {"mensaje": "Docente eliminado correctamente"}
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            409, "No se puede eliminar: el docente tiene secciones asignadas"
        ) from error

