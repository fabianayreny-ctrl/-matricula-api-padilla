from pathlib import Path


RUTA_PROYECTO = Path(__file__).resolve().parent.parent
BASE_DATOS = RUTA_PROYECTO / "sistema_academico.db"


if BASE_DATOS.exists():
    BASE_DATOS.unlink()
    print("Base de datos eliminada correctamente.")
else:
    print("La base de datos todavía no existe.")

print("Inicie la API para crear nuevamente los datos de demostración.")

