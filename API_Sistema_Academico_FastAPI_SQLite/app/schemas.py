from datetime import date
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator


EstadoEstudiante = Literal["ACTIVO", "INACTIVO", "GRADUADO"]
EstadoDocente = Literal["ACTIVO", "INACTIVO"]
EstadoSeccion = Literal["ABIERTA", "CERRADA", "FINALIZADA"]
EstadoMatricula = Literal["MATRICULADA", "CANCELADA", "APROBADA", "REPROBADA"]
RolUsuario = Literal["ADMIN", "DOCENTE"]


class MensajeRespuesta(BaseModel):
    mensaje: str


class UsuarioLogin(BaseModel):
    usuario: str = Field(min_length=3, max_length=40)
    clave: str = Field(min_length=4, max_length=100)


class UsuarioRespuesta(BaseModel):
    id: int
    usuario: str
    nombre_completo: str
    rol: RolUsuario


class CarreraEntrada(BaseModel):
    codigo: str = Field(min_length=2, max_length=10)
    nombre: str = Field(min_length=4, max_length=120)
    duracion_anios: int = Field(ge=1, le=10)
    activo: bool = True


class CarreraRespuesta(CarreraEntrada):
    id: int


class EstudianteEntrada(BaseModel):
    cuenta: str = Field(min_length=5, max_length=20)
    nombres: str = Field(min_length=2, max_length=80)
    apellidos: str = Field(min_length=2, max_length=80)
    correo: EmailStr
    telefono: str | None = Field(default=None, max_length=25)
    fecha_nacimiento: date
    carrera_id: int = Field(gt=0)
    estado: EstadoEstudiante = "ACTIVO"

    @field_validator("fecha_nacimiento")
    @classmethod
    def validar_fecha_nacimiento(cls, valor: date) -> date:
        if valor >= date.today():
            raise ValueError("La fecha de nacimiento debe ser anterior a hoy")
        return valor


class EstudianteRespuesta(EstudianteEntrada):
    id: int
    carrera_codigo: str
    carrera_nombre: str


class DocenteEntrada(BaseModel):
    numero_empleado: str = Field(min_length=3, max_length=20)
    nombres: str = Field(min_length=2, max_length=80)
    apellidos: str = Field(min_length=2, max_length=80)
    correo: EmailStr
    especialidad: str = Field(min_length=3, max_length=120)
    estado: EstadoDocente = "ACTIVO"


class DocenteRespuesta(DocenteEntrada):
    id: int


class AsignaturaEntrada(BaseModel):
    codigo: str = Field(min_length=3, max_length=15)
    nombre: str = Field(min_length=3, max_length=120)
    unidades_valorativas: int = Field(ge=1, le=8)
    carrera_id: int = Field(gt=0)
    requisito_id: int | None = Field(default=None, gt=0)
    activo: bool = True


class AsignaturaRespuesta(AsignaturaEntrada):
    id: int
    carrera_nombre: str
    requisito_codigo: str | None = None


class PeriodoEntrada(BaseModel):
    anio: int = Field(ge=2020, le=2100)
    numero: int = Field(ge=1, le=3)
    fecha_inicio: date
    fecha_fin: date
    activo: bool = False

    @field_validator("fecha_fin")
    @classmethod
    def validar_fecha_fin(cls, valor: date, info):
        inicio = info.data.get("fecha_inicio")
        if inicio and valor <= inicio:
            raise ValueError("La fecha final debe ser posterior a la fecha inicial")
        return valor


class PeriodoRespuesta(PeriodoEntrada):
    id: int
    nombre: str


class AulaEntrada(BaseModel):
    codigo: str = Field(min_length=2, max_length=20)
    edificio: str = Field(min_length=2, max_length=80)
    capacidad: int = Field(ge=1, le=200)
    activo: bool = True


class AulaRespuesta(AulaEntrada):
    id: int


class SeccionEntrada(BaseModel):
    codigo: str = Field(min_length=2, max_length=10)
    asignatura_id: int = Field(gt=0)
    docente_id: int = Field(gt=0)
    periodo_id: int = Field(gt=0)
    aula_id: int | None = Field(default=None, gt=0)
    dias: str = Field(min_length=2, max_length=30, examples=["LU-MI"])
    hora_inicio: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    hora_fin: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    cupo_maximo: int = Field(ge=1, le=200)
    estado: EstadoSeccion = "ABIERTA"

    @field_validator("hora_fin")
    @classmethod
    def validar_horario(cls, valor: str, info):
        inicio = info.data.get("hora_inicio")
        if inicio and valor <= inicio:
            raise ValueError("La hora final debe ser posterior a la hora inicial")
        return valor


class SeccionRespuesta(SeccionEntrada):
    id: int
    asignatura_codigo: str
    asignatura_nombre: str
    docente_nombre: str
    periodo_nombre: str
    aula_codigo: str | None = None
    matriculados: int
    cupos_disponibles: int


class MatriculaEntrada(BaseModel):
    estudiante_id: int = Field(gt=0)
    seccion_id: int = Field(gt=0)


class MatriculaRespuesta(BaseModel):
    id: int
    estudiante_id: int
    estudiante_cuenta: str
    estudiante_nombre: str
    seccion_id: int
    asignatura_codigo: str
    asignatura_nombre: str
    seccion_codigo: str
    periodo_nombre: str
    fecha_matricula: str
    estado: EstadoMatricula


class CalificacionEntrada(BaseModel):
    primer_parcial: float = Field(ge=0, le=100)
    segundo_parcial: float = Field(ge=0, le=100)
    tercer_parcial: float = Field(ge=0, le=100)
    observacion: str | None = Field(default=None, max_length=250)


class CalificacionRespuesta(CalificacionEntrada):
    id: int
    matricula_id: int
    nota_final: float
    resultado: Literal["APROBADA", "REPROBADA"]

