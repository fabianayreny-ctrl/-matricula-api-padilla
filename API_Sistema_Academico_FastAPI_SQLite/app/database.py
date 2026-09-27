from contextlib import contextmanager
from pathlib import Path
import hashlib
import sqlite3


def hash_clave(clave: str) -> str:
    """Hash simple de la contraseña (fines didácticos).

    En un sistema real se usaría una librería como passlib/bcrypt, que además
    agrega 'sal' a cada contraseña. Aquí se mantiene sencillo para que el
    estudiante pueda leer y explicar el código completo.
    """
    return hashlib.sha256(clave.encode("utf-8")).hexdigest()


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "sistema_academico.db"


def obtener_conexion() -> sqlite3.Connection:
    """Crea una conexión y hace que cada fila se comporte como diccionario."""
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


@contextmanager
def conexion_lectura():
    """Entrega una conexión de consulta y garantiza que siempre se cierre."""
    conexion = obtener_conexion()
    try:
        yield conexion
    finally:
        conexion.close()


@contextmanager
def transaccion():
    """Confirma todos los cambios o los revierte cuando ocurre un error."""
    conexion = obtener_conexion()
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def crear_tablas() -> None:
    esquema = """
    CREATE TABLE IF NOT EXISTS carreras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT NOT NULL UNIQUE,
        nombre TEXT NOT NULL UNIQUE,
        duracion_anios INTEGER NOT NULL CHECK (duracion_anios BETWEEN 1 AND 10),
        activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
        creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS estudiantes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cuenta TEXT NOT NULL UNIQUE,
        nombres TEXT NOT NULL,
        apellidos TEXT NOT NULL,
        correo TEXT NOT NULL UNIQUE,
        telefono TEXT,
        fecha_nacimiento TEXT NOT NULL,
        carrera_id INTEGER NOT NULL,
        estado TEXT NOT NULL DEFAULT 'ACTIVO'
            CHECK (estado IN ('ACTIVO', 'INACTIVO', 'GRADUADO')),
        creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (carrera_id) REFERENCES carreras(id) ON DELETE RESTRICT
    );

    CREATE TABLE IF NOT EXISTS docentes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_empleado TEXT NOT NULL UNIQUE,
        nombres TEXT NOT NULL,
        apellidos TEXT NOT NULL,
        correo TEXT NOT NULL UNIQUE,
        especialidad TEXT NOT NULL,
        estado TEXT NOT NULL DEFAULT 'ACTIVO'
            CHECK (estado IN ('ACTIVO', 'INACTIVO')),
        creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS asignaturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT NOT NULL UNIQUE,
        nombre TEXT NOT NULL,
        unidades_valorativas INTEGER NOT NULL
            CHECK (unidades_valorativas BETWEEN 1 AND 8),
        carrera_id INTEGER NOT NULL,
        requisito_id INTEGER,
        activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
        FOREIGN KEY (carrera_id) REFERENCES carreras(id) ON DELETE RESTRICT,
        FOREIGN KEY (requisito_id) REFERENCES asignaturas(id) ON DELETE SET NULL,
        CHECK (requisito_id IS NULL OR requisito_id <> id)
    );

    CREATE TABLE IF NOT EXISTS periodos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        anio INTEGER NOT NULL CHECK (anio BETWEEN 2020 AND 2100),
        numero INTEGER NOT NULL CHECK (numero BETWEEN 1 AND 3),
        fecha_inicio TEXT NOT NULL,
        fecha_fin TEXT NOT NULL,
        activo INTEGER NOT NULL DEFAULT 0 CHECK (activo IN (0, 1)),
        UNIQUE (anio, numero),
        CHECK (fecha_fin > fecha_inicio)
    );

    CREATE TABLE IF NOT EXISTS aulas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT NOT NULL UNIQUE,
        edificio TEXT NOT NULL,
        capacidad INTEGER NOT NULL CHECK (capacidad BETWEEN 1 AND 200),
        activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
    );

    CREATE TABLE IF NOT EXISTS secciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT NOT NULL,
        asignatura_id INTEGER NOT NULL,
        docente_id INTEGER NOT NULL,
        periodo_id INTEGER NOT NULL,
        aula_id INTEGER,
        dias TEXT NOT NULL,
        hora_inicio TEXT NOT NULL,
        hora_fin TEXT NOT NULL,
        cupo_maximo INTEGER NOT NULL CHECK (cupo_maximo BETWEEN 1 AND 200),
        estado TEXT NOT NULL DEFAULT 'ABIERTA'
            CHECK (estado IN ('ABIERTA', 'CERRADA', 'FINALIZADA')),
        FOREIGN KEY (asignatura_id) REFERENCES asignaturas(id) ON DELETE RESTRICT,
        FOREIGN KEY (docente_id) REFERENCES docentes(id) ON DELETE RESTRICT,
        FOREIGN KEY (periodo_id) REFERENCES periodos(id) ON DELETE RESTRICT,
        FOREIGN KEY (aula_id) REFERENCES aulas(id) ON DELETE SET NULL,
        UNIQUE (asignatura_id, periodo_id, codigo),
        CHECK (hora_fin > hora_inicio)
    );

    CREATE TABLE IF NOT EXISTS matriculas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        estudiante_id INTEGER NOT NULL,
        seccion_id INTEGER NOT NULL,
        fecha_matricula TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        estado TEXT NOT NULL DEFAULT 'MATRICULADA'
            CHECK (estado IN ('MATRICULADA', 'CANCELADA', 'APROBADA', 'REPROBADA')),
        FOREIGN KEY (estudiante_id) REFERENCES estudiantes(id) ON DELETE RESTRICT,
        FOREIGN KEY (seccion_id) REFERENCES secciones(id) ON DELETE RESTRICT,
        UNIQUE (estudiante_id, seccion_id)
    );

    CREATE TABLE IF NOT EXISTS calificaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula_id INTEGER NOT NULL UNIQUE,
        primer_parcial REAL NOT NULL CHECK (primer_parcial BETWEEN 0 AND 100),
        segundo_parcial REAL NOT NULL CHECK (segundo_parcial BETWEEN 0 AND 100),
        tercer_parcial REAL NOT NULL CHECK (tercer_parcial BETWEEN 0 AND 100),
        nota_final REAL NOT NULL CHECK (nota_final BETWEEN 0 AND 100),
        observacion TEXT,
        actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (matricula_id) REFERENCES matriculas(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT NOT NULL UNIQUE,
        nombre_completo TEXT NOT NULL,
        clave_hash TEXT NOT NULL,
        rol TEXT NOT NULL DEFAULT 'DOCENTE' CHECK (rol IN ('ADMIN', 'DOCENTE')),
        activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1)),
        creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
    );

    CREATE INDEX IF NOT EXISTS idx_estudiantes_carrera
        ON estudiantes(carrera_id);
    CREATE INDEX IF NOT EXISTS idx_secciones_periodo
        ON secciones(periodo_id);
    CREATE INDEX IF NOT EXISTS idx_matriculas_estudiante
        ON matriculas(estudiante_id);
    CREATE INDEX IF NOT EXISTS idx_matriculas_seccion
        ON matriculas(seccion_id);
    """
    with transaccion() as conexion:
        conexion.executescript(esquema)


def cargar_datos_demostracion() -> None:
    """Inserta datos una sola vez para que la API no aparezca vacía."""
    with transaccion() as conexion:
        cantidad = conexion.execute("SELECT COUNT(*) FROM carreras").fetchone()[0]
        if cantidad > 0:
            return

        conexion.executescript(
            """
            INSERT INTO carreras (id, codigo, nombre, duracion_anios) VALUES
                (1, 'IS', 'Ingeniería en Sistemas', 5),
                (2, 'AE', 'Administración de Empresas', 4);

            INSERT INTO estudiantes
                (id, cuenta, nombres, apellidos, correo, telefono,
                 fecha_nacimiento, carrera_id, estado)
            VALUES
                (1, '20261001', 'Ana', 'Martínez', 'ana@universidad.edu',
                 '9999-1001', '2005-04-12', 1, 'ACTIVO'),
                (2, '20261002', 'Carlos', 'López', 'carlos@universidad.edu',
                 '9999-1002', '2004-11-08', 1, 'ACTIVO'),
                (3, '20261003', 'Sofía', 'Hernández', 'sofia@universidad.edu',
                 '9999-1003', '2005-01-20', 1, 'ACTIVO'),
                (4, '20261004', 'Luis', 'Rivera', 'luis@universidad.edu',
                 '9999-1004', '2003-09-16', 2, 'ACTIVO'),
                (5, '20251015', 'María', 'Mejía', 'maria@universidad.edu',
                 NULL, '2002-07-03', 1, 'INACTIVO');

            INSERT INTO docentes
                (id, numero_empleado, nombres, apellidos, correo,
                 especialidad, estado)
            VALUES
                (1, 'DOC-001', 'Elías', 'Flores', 'elias@universidad.edu',
                 'Programación y bases de datos', 'ACTIVO'),
                (2, 'DOC-002', 'Laura', 'Gómez', 'laura@universidad.edu',
                 'Redes y seguridad', 'ACTIVO'),
                (3, 'DOC-003', 'Mario', 'Pineda', 'mario@universidad.edu',
                 'Gestión empresarial', 'ACTIVO');

            INSERT INTO asignaturas
                (id, codigo, nombre, unidades_valorativas, carrera_id,
                 requisito_id, activo)
            VALUES
                (1, 'IS-110', 'Programación I', 4, 1, NULL, 1),
                (2, 'IS-210', 'Programación II', 4, 1, 1, 1),
                (3, 'IS-310', 'Estructura de Datos', 4, 1, 2, 1),
                (4, 'IS-220', 'Bases de Datos I', 4, 1, 1, 1),
                (5, 'AE-101', 'Administración I', 4, 2, NULL, 1);

            INSERT INTO periodos
                (id, anio, numero, fecha_inicio, fecha_fin, activo)
            VALUES
                (1, 2026, 1, '2026-01-15', '2026-04-30', 0),
                (2, 2026, 3, '2026-09-01', '2026-12-15', 1);

            INSERT INTO aulas (id, codigo, edificio, capacidad, activo) VALUES
                (1, 'LAB-01', 'Edificio A', 30, 1),
                (2, 'LAB-02', 'Edificio A', 25, 1),
                (3, 'AULA-05', 'Edificio B', 40, 1);

            INSERT INTO secciones
                (id, codigo, asignatura_id, docente_id, periodo_id, aula_id,
                 dias, hora_inicio, hora_fin, cupo_maximo, estado)
            VALUES
                (1, '0700', 1, 1, 1, 1, 'LU-MI', '07:00', '09:00', 25,
                 'FINALIZADA'),
                (2, '0700', 2, 1, 2, 1, 'LU-MI', '07:00', '09:00', 25,
                 'ABIERTA'),
                (3, '0900', 4, 1, 2, 2, 'LU-MI', '09:00', '11:00', 25,
                 'ABIERTA'),
                (4, '1300', 3, 2, 2, 1, 'MA-JU', '13:00', '15:00', 25,
                 'ABIERTA'),
                (5, '1800', 5, 3, 2, 3, 'MA-JU', '18:00', '20:00', 35,
                 'ABIERTA');

            INSERT INTO matriculas
                (id, estudiante_id, seccion_id, estado)
            VALUES
                (1, 1, 1, 'APROBADA'),
                (2, 2, 1, 'APROBADA'),
                (3, 1, 2, 'MATRICULADA'),
                (4, 2, 2, 'MATRICULADA'),
                (5, 3, 3, 'MATRICULADA'),
                (6, 4, 5, 'MATRICULADA');

            INSERT INTO calificaciones
                (id, matricula_id, primer_parcial, segundo_parcial,
                 tercer_parcial, nota_final, observacion)
            VALUES
                (1, 1, 80, 75, 85, 80, 'Aprobó Programación I'),
                (2, 2, 70, 68, 72, 70, 'Aprobó Programación I');
            """
        )

        conexion.execute(
            """
            INSERT INTO usuarios (usuario, nombre_completo, clave_hash, rol)
            VALUES (?, ?, ?, ?)
            """,
            ("admin", "Administrador del Sistema", hash_clave("admin123"), "ADMIN"),
        )
        conexion.execute(
            """
            INSERT INTO usuarios (usuario, nombre_completo, clave_hash, rol)
            VALUES (?, ?, ?, ?)
            """,
            ("docente", "Elías Flores", hash_clave("docente123"), "DOCENTE"),
        )


def inicializar_base_datos() -> None:
    crear_tablas()
    cargar_datos_demostracion()
