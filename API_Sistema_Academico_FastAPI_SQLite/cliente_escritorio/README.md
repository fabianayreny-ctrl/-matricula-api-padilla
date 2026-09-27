# Cliente de escritorio — Login + Dashboard

Aplicación de escritorio (Tkinter) que consume la API del Sistema
Académico. Es el punto de partida del proyecto de Programación III:
tomar la API de Programación II y convertirla en una aplicación con
interfaz gráfica.

## Qué incluye

- `login.py` — ventana de inicio de sesión. Llama a `POST /api/v1/auth/login`.
- `dashboard.py` — ventana principal: tarjetas con los indicadores de
  `GET /api/v1/reportes/dashboard` y una tabla con `GET /api/v1/estudiantes`.
- `api_cliente.py` — clase `ClienteAPI` que centraliza las llamadas HTTP.
  Implementa el **patrón Singleton**: toda la aplicación comparte una sola
  instancia (y una sola sesión HTTP), sin importar cuántas ventanas la usen.
- `main.py` — punto de entrada: abre el login y, si es correcto, abre el dashboard.

## Cómo ejecutarlo

1. Primero levantar la API (desde la carpeta raíz del proyecto):

   ```bash
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. En otra terminal, ejecutar el cliente (desde esta carpeta):

   ```bash
   pip install requests
   python main.py
   ```

3. Usuarios de prueba (creados automáticamente con la base de datos):

   | Usuario   | Contraseña   | Rol     |
   |-----------|--------------|---------|
   | admin     | admin123     | ADMIN   |
   | docente   | docente123   | DOCENTE |

## Cómo sigue creciendo este proyecto (por parcial)

- **Parcial I** (este punto de partida): UML de las clases, patrón
  Singleton en `ClienteAPI`, ventana de login y dashboard.
- **Parcial II**: más pantallas (lista de secciones, matrículas),
  pruebas automáticas del cliente, mejoras de UX (validaciones,
  mensajes de error más claros, indicador de "cargando").
- **Parcial III**: usar colecciones para agrupar/ordenar datos en
  memoria, cargar el dashboard en un hilo aparte para que la ventana no
  se congele mientras espera a la API, y exportar reportes a CSV.

## Nota sobre la contraseña

La tabla `usuarios` guarda la contraseña con un hash SHA-256
(`hash_clave` en `app/database.py`), no en texto plano. Es una
simplificación con fines didácticos: en un sistema real se usaría una
librería como **passlib** o **bcrypt**, que además agrega "sal" a cada
contraseña. Es un buen tema para comentar en clase.
