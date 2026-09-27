def test_inicio_y_dashboard(cliente):
    # La raíz "/" ahora sirve el frontend (login + dashboard) desde la
    # carpeta frontend/, en vez de devolver un JSON de bienvenida.
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    assert "text/html" in respuesta.headers["content-type"]

    salud = cliente.get("/salud")
    assert salud.status_code == 200
    assert salud.json()["estado"] == "OK"

    dashboard = cliente.get("/api/v1/reportes/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["estudiantes_activos"] == 4
    assert dashboard.json()["periodo_activo"] == "2026-3"


def test_login_correcto_e_incorrecto(cliente):
    correcto = cliente.post(
        "/api/v1/auth/login", json={"usuario": "admin", "clave": "admin123"}
    )
    assert correcto.status_code == 200
    assert correcto.json()["rol"] == "ADMIN"

    incorrecto = cliente.post(
        "/api/v1/auth/login", json={"usuario": "admin", "clave": "clave-mala"}
    )
    assert incorrecto.status_code == 401


def test_datos_iniciales_y_relaciones(cliente):
    respuesta = cliente.get("/api/v1/secciones")
    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 5
    assert respuesta.json()[0]["asignatura_codigo"]
    assert "cupos_disponibles" in respuesta.json()[0]


def test_crear_y_consultar_estudiante(cliente):
    nuevo = {
        "cuenta": "20262020",
        "nombres": "Pedro",
        "apellidos": "Castillo",
        "correo": "pedro@universidad.edu",
        "telefono": "9999-2020",
        "fecha_nacimiento": "2004-06-15",
        "carrera_id": 1,
        "estado": "ACTIVO",
    }
    creada = cliente.post("/api/v1/estudiantes", json=nuevo)
    assert creada.status_code == 201
    estudiante_id = creada.json()["id"]
    assert creada.json()["carrera_codigo"] == "IS"

    consulta = cliente.get(f"/api/v1/estudiantes/{estudiante_id}")
    assert consulta.status_code == 200
    assert consulta.json()["cuenta"] == "20262020"


def test_rechazar_cuenta_duplicada(cliente):
    duplicado = {
        "cuenta": "20261001",
        "nombres": "Otra",
        "apellidos": "Persona",
        "correo": "otra@universidad.edu",
        "fecha_nacimiento": "2003-01-01",
        "carrera_id": 1,
        "estado": "ACTIVO",
    }
    respuesta = cliente.post("/api/v1/estudiantes", json=duplicado)
    assert respuesta.status_code == 409


def test_matricula_valida_y_duplicada(cliente):
    # Ana aprobó IS-110 y puede matricular Bases de Datos I, que lo exige.
    respuesta = cliente.post(
        "/api/v1/matriculas", json={"estudiante_id": 1, "seccion_id": 3}
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["asignatura_codigo"] == "IS-220"

    repetida = cliente.post(
        "/api/v1/matriculas", json={"estudiante_id": 1, "seccion_id": 3}
    )
    assert repetida.status_code == 409


def test_rechazar_requisito_pendiente(cliente):
    # Sofía no tiene aprobada Programación I.
    respuesta = cliente.post(
        "/api/v1/matriculas", json={"estudiante_id": 3, "seccion_id": 2}
    )
    assert respuesta.status_code == 409
    assert "requisito" in respuesta.json()["detail"].lower()


def test_rechazar_choque_de_horario(cliente):
    nueva_seccion = {
        "codigo": "0800",
        "asignatura_id": 1,
        "docente_id": 2,
        "periodo_id": 2,
        "aula_id": 3,
        "dias": "LU-MI",
        "hora_inicio": "08:00",
        "hora_fin": "10:00",
        "cupo_maximo": 30,
        "estado": "ABIERTA",
    }
    seccion = cliente.post("/api/v1/secciones", json=nueva_seccion)
    assert seccion.status_code == 201

    respuesta = cliente.post(
        "/api/v1/matriculas",
        json={"estudiante_id": 1, "seccion_id": seccion.json()["id"]},
    )
    assert respuesta.status_code == 409
    assert "choque" in respuesta.json()["detail"].lower()


def test_calcular_nota_y_actualizar_estado(cliente):
    respuesta = cliente.put(
        "/api/v1/calificaciones/matricula/3",
        json={
            "primer_parcial": 80,
            "segundo_parcial": 70,
            "tercer_parcial": 60,
            "observacion": "Promedio calculado por la API",
        },
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["nota_final"] == 70
    assert respuesta.json()["resultado"] == "APROBADA"

    matricula = cliente.get("/api/v1/matriculas/3")
    assert matricula.json()["estado"] == "APROBADA"


def test_cancelar_matricula_libera_cupo(cliente):
    antes = cliente.get("/api/v1/secciones/2").json()["cupos_disponibles"]
    cancelada = cliente.patch("/api/v1/matriculas/3/cancelar")
    assert cancelada.status_code == 200
    despues = cliente.get("/api/v1/secciones/2").json()["cupos_disponibles"]
    assert despues == antes + 1


def test_reportes_de_historial_y_lista(cliente):
    historial = cliente.get("/api/v1/reportes/historial-estudiante/1")
    assert historial.status_code == 200
    assert historial.json()["resumen"]["unidades_valorativas_aprobadas"] == 4

    lista = cliente.get("/api/v1/reportes/lista-seccion/2")
    assert lista.status_code == 200
    assert lista.json()["cantidad_matriculados"] == 2


def test_validacion_pydantic_devuelve_422(cliente):
    invalido = {
        "cuenta": "12345",
        "nombres": "A",
        "apellidos": "B",
        "correo": "esto-no-es-correo",
        "fecha_nacimiento": "2030-01-01",
        "carrera_id": 1,
    }
    respuesta = cliente.post("/api/v1/estudiantes", json=invalido)
    assert respuesta.status_code == 422

