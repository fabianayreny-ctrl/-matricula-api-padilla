from fastapi import APIRouter, HTTPException

from app.database import conexion_lectura, hash_clave
from app.schemas import UsuarioLogin, UsuarioRespuesta


router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=UsuarioRespuesta)
def iniciar_sesion(datos: UsuarioLogin):
    """Valida usuario y contraseña contra la tabla 'usuarios'.

    Este endpoint es la base de la pantalla de login del cliente de
    escritorio. No usa tokens ni sesiones (eso se puede agregar más
    adelante, por ejemplo con JWT); por ahora el cliente simplemente
    guarda en memoria los datos del usuario que inició sesión.
    """
    with conexion_lectura() as conexion:
        fila = conexion.execute(
            "SELECT * FROM usuarios WHERE usuario = ?", (datos.usuario,)
        ).fetchone()

    if fila is None or fila["clave_hash"] != hash_clave(datos.clave):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")

    if not fila["activo"]:
        raise HTTPException(status_code=403, detail="Este usuario está inactivo")

    return {
        "id": fila["id"],
        "usuario": fila["usuario"],
        "nombre_completo": fila["nombre_completo"],
        "rol": fila["rol"],
    }
