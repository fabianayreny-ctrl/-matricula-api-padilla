# Guía didáctica para Programación II

## Objetivo

Que el estudiante comprenda cómo una aplicación recibe datos, los valida,
ejecuta reglas de negocio, consulta una base de datos relacional y responde en
JSON. El proyecto puede desarrollarse en cuatro clases antes de crear el
frontend.

## Clase 1: conocer el sistema y la base de datos

1. Ejecutar la API y abrir `/docs`.
2. Probar `GET /`, `GET /api/v1/estudiantes` y `GET /api/v1/secciones`.
3. Abrir `sistema_academico.db` con DB Browser for SQLite.
4. Identificar claves primarias, foráneas, valores únicos e índices.
5. Ejecutar las consultas de `sql/consultas_para_db_browser.sql`.

Preguntas para los estudiantes:

- ¿Por qué `carrera_id` se almacena en estudiantes y no el nombre de la carrera?
- ¿Por qué matrícula necesita `estudiante_id` y `seccion_id`?
- ¿Qué diferencia existe entre una asignatura y una sección?
- ¿Qué ocurre si se intenta insertar dos veces la misma cuenta?

## Clase 2: CRUD, Pydantic y códigos HTTP

1. Crear una carrera, un estudiante y un docente desde Postman.
2. Consultarlos por ID.
3. Modificarlos con PUT.
4. Intentar enviar un correo inválido para observar `422`.
5. Intentar repetir una cuenta para observar `409`.
6. Consultar un ID inexistente para observar `404`.

Códigos a explicar:

| Código | Significado dentro del proyecto |
|---|---|
| 200 | Petición procesada correctamente |
| 201 | Registro creado correctamente |
| 404 | El recurso solicitado no existe |
| 409 | Existe un conflicto con los datos o las reglas |
| 422 | El JSON no cumple el esquema Pydantic |
| 500 | Error no controlado del servidor |

## Clase 3: relaciones y reglas de negocio

1. Ver las secciones disponibles.
2. Matricular a Ana (`estudiante_id=1`) en Bases de Datos (`seccion_id=3`).
3. Repetir la petición para comprobar la matrícula duplicada.
4. Intentar matricular a Sofía (`id=3`) en Programación II (`id=2`): no ha
   aprobado el requisito.
5. Cancelar una matrícula y comprobar que aumenta el cupo disponible.
6. Explicar por qué se usa una transacción con `commit` y `rollback`.

Actividad grupal: cada grupo debe agregar una regla nueva, por ejemplo máximo de
cuatro asignaturas, bloqueo por deuda o fecha límite de matrícula.

## Clase 4: consultas avanzadas y calificaciones

1. Guardar tres notas con `PUT /calificaciones/matricula/{id}`.
2. Ver cómo cambia el estado a APROBADA o REPROBADA.
3. Consultar el historial del estudiante.
4. Consultar la lista de la sección y la carga del docente.
5. Abrir `app/routers/reportes.py` y localizar los `JOIN`, `COUNT` y `SUM`.

Actividad: modificar la ponderación de las notas. Por ejemplo, primer parcial
30 %, segundo parcial 30 % y tercer parcial 40 %.

## Puente hacia el frontend

Antes de programar Vue, pida a los grupos dibujar estas pantallas:

- Dashboard con tarjetas de resumen.
- Lista y formulario de estudiantes.
- Oferta de secciones con cupos disponibles.
- Pantalla de matrícula del estudiante.
- Lista de una sección para ingresar notas.
- Historial académico.

Luego cada llamada Postman se transforma en una llamada `fetch` o `axios`. La
URL base recomendada es `http://127.0.0.1:8000/api/v1`.

## Proyecto evaluado sugerido

Cada equipo puede elegir otro dominio —clínica, biblioteca, inventario o
ventas— y reproducir el mismo patrón:

1. Mínimo seis tablas relacionadas.
2. CRUD de tres catálogos.
3. Una relación muchos a muchos.
4. Cinco reglas de negocio.
5. Tres reportes con JOIN y agregaciones.
6. Colección Postman.
7. Pruebas automáticas de al menos cinco casos.
8. Frontend en la siguiente etapa.

