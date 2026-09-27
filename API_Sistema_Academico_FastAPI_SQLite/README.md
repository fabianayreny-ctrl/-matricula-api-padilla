# API del Sistema de Gestión Académica

Proyecto completo para **Programación II**, desarrollado con Python, FastAPI y
SQLite. Amplía el CRUD básico de estudiantes y permite estudiar una API con
relaciones, validaciones, consultas avanzadas y reglas de negocio reales.

La base de datos y sus datos de demostración se crean automáticamente al
iniciar. No es necesario ejecutar un archivo SQL antes de usar la API.

## Módulos incluidos

| Módulo | Función principal |
|---|---|
| Carreras | CRUD de carreras universitarias |
| Estudiantes | CRUD, búsqueda, filtros y relación con carrera |
| Docentes | CRUD y asignación a secciones |
| Asignaturas | CRUD, unidades valorativas y requisitos |
| Períodos | Control de períodos académicos; solo uno queda activo |
| Aulas | CRUD, capacidad y asignación de espacios |
| Secciones | Oferta de asignaturas, docente, aula, horario y cupos |
| Matrículas | Relación muchos a muchos entre estudiantes y secciones |
| Calificaciones | Tres parciales, promedio y resultado automático |
| Reportes | Dashboard, historial, lista de sección y carga docente |

## 1. Preparar el proyecto

Abra esta carpeta en VS Code y abra una terminal integrada.

### Windows

```bat
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```

También puede ejecutar `INSTALAR_WINDOWS.bat` con doble clic.

### Linux o macOS

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

## 2. Ejecutar la API

Con el entorno virtual activado:

```bash
uvicorn main:app --reload
```

En Windows también puede usar `INICIAR_API_WINDOWS.bat`.

- Frontend (login + dashboard): <http://127.0.0.1:8000>
- Swagger: <http://127.0.0.1:8000/docs>
- ReDoc: <http://127.0.0.1:8000/redoc>
- Rutas del sistema: `http://127.0.0.1:8000/api/v1`

Al iniciar se genera `sistema_academico.db`. Puede abrirlo con **DB Browser for
SQLite** mientras la API está detenida.

### Frontend web (login + dashboard)

La carpeta `frontend/` contiene una página web (HTML + CSS + JavaScript, sin
frameworks) que la propia API sirve en la raíz `/`. Al abrir
`http://127.0.0.1:8000` en el navegador aparece una pantalla de login;
al entrar muestra un dashboard con tarjetas de indicadores
(`/api/v1/reportes/dashboard`) y una tabla de estudiantes con buscador
(`/api/v1/estudiantes`).

Usuarios de prueba (tabla `usuarios`, creada junto con los demás datos de
demostración):

| Usuario | Contraseña | Rol     |
|---------|------------|---------|
| admin   | admin123   | ADMIN   |
| docente | docente123 | DOCENTE |

Como el frontend se sirve desde la misma API, no hay que preocuparse por CORS
ni levantar un segundo servidor: basta con `uvicorn app.main:app --reload` y
abrir el navegador.

## 3. Probar en Postman

Importe el archivo `Sistema_Academico.postman_collection.json`. La colección
incluye ejemplos correctos y casos de error. En una petición manual que envíe
datos, seleccione **Body > raw > JSON**.

Ejemplo para matricular a un estudiante:

```json
{
  "estudiante_id": 1,
  "seccion_id": 3
}
```

Ejemplo para guardar las tres calificaciones de una matrícula:

```json
{
  "primer_parcial": 80,
  "segundo_parcial": 70,
  "tercer_parcial": 90,
  "observacion": "Buen desempeño"
}
```

La API calcula la nota final. Con `65` o más cambia la matrícula a `APROBADA`;
con una nota menor cambia a `REPROBADA`.

## 4. Reglas de negocio que se pueden demostrar

- Una cuenta y un correo no pueden repetirse.
- Un estudiante inactivo no puede matricularse.
- Solo se permite matrícula en un período activo y una sección abierta.
- La asignatura debe pertenecer a la carrera del estudiante.
- El estudiante debe haber aprobado el requisito de la asignatura.
- No se permite matricular dos veces la misma sección.
- No se permite superar el cupo de la sección ni 20 unidades valorativas.
- No se permiten choques de horario del estudiante.
- Un docente o un aula no pueden ocupar dos secciones al mismo tiempo.
- El cupo de una sección no puede superar la capacidad del aula.
- Cancelar una matrícula libera el cupo sin borrar su registro.
- Las eliminaciones protegidas devuelven `409 Conflict` para conservar el historial.

## 5. Endpoints principales

Todos estos endpoints usan el prefijo `/api/v1`.

| Método | Endpoint | Acción |
|---|---|---|
| GET / POST | `/carreras` | Listar o crear carreras |
| GET / PUT / DELETE | `/carreras/{id}` | Consultar, modificar o eliminar |
| GET / POST | `/estudiantes` | Listar, buscar o crear estudiantes |
| GET / PUT / DELETE | `/estudiantes/{id}` | CRUD por ID |
| GET / POST | `/docentes` | Listar o crear docentes |
| GET / POST | `/asignaturas` | Listar o crear asignaturas |
| GET / POST | `/periodos` | Listar o crear períodos |
| GET / POST | `/aulas` | Listar o crear aulas |
| GET / POST | `/secciones` | Listar o crear secciones |
| GET | `/secciones/disponibles` | Ver oferta abierta con cupos |
| GET / POST | `/matriculas` | Listar o realizar matrículas |
| PATCH | `/matriculas/{id}/cancelar` | Cancelar sin borrar historial |
| PUT | `/calificaciones/matricula/{id}` | Crear o actualizar notas |
| GET | `/reportes/dashboard` | Resumen general |
| GET | `/reportes/historial-estudiante/{id}` | Historial académico |
| GET | `/reportes/lista-seccion/{id}` | Lista de estudiantes de una clase |
| GET | `/reportes/carga-docente/{id}` | Secciones asignadas a un docente |

Swagger muestra los demás endpoints, parámetros, esquemas JSON y códigos HTTP.

## 6. Cómo seguir la lógica del código

Para explicar una matrícula, recorra estos archivos en orden:

1. `app/main.py`: registra el router dentro de la aplicación.
2. `app/routers/matriculas.py`: recibe el JSON y define el endpoint.
3. `app/schemas.py`: valida los tipos e identificadores.
4. `app/services/matricula_service.py`: aplica las reglas de negocio.
5. `app/database.py`: abre la conexión, crea las tablas y controla transacciones.
6. SQLite devuelve filas y el router construye la respuesta JSON.

Los signos `?` en las consultas son parámetros SQL. Evitan concatenar datos del
usuario y ayudan a prevenir inyección SQL.

## 7. Restablecer los datos de demostración

Detenga Uvicorn y ejecute:

```bash
python scripts/reiniciar_bd.py
```

Luego vuelva a iniciar la API. El script borra únicamente
`sistema_academico.db`; FastAPI lo crea de nuevo con los datos iniciales.

## 8. Ejecutar las pruebas automáticas

```bash
python -m pytest -q
```

Las pruebas verifican el CRUD, las relaciones, los requisitos, los choques de
horario, el cálculo de notas, la cancelación y los reportes.

## 9. Preparación para el frontend

La API ya permite peticiones desde:

- `http://localhost:5173`
- `http://127.0.0.1:5173`

Estas son las direcciones habituales de Vite. Así, en la siguiente etapa se
puede crear un frontend en Vue o React sin cambiar el backend.

