"""Cliente HTTP hacia la API del Sistema Académico.

Aplica el patrón de diseño Singleton: sin importar cuántas ventanas de la
aplicación necesiten hablar con la API, todas comparten la misma instancia
de ClienteAPI (y por lo tanto la misma sesión HTTP). Esto se explica en
clase junto con UML avanzado / patrones de diseño (Parcial I).
"""

from __future__ import annotations

import requests

BASE_URL = "http://127.0.0.1:8000/api/v1"


class ClienteAPI:
    _instancia: "ClienteAPI | None" = None

    def __new__(cls, *args, **kwargs):
        if cls._instancia is None:
            cls._instancia = super().__new__(cls)
            cls._instancia._inicializado = False
        return cls._instancia

    def __init__(self, base_url: str = BASE_URL):
        if self._inicializado:
            return
        self.base_url = base_url
        self.sesion = requests.Session()
        self.usuario_actual: dict | None = None
        self._inicializado = True

    # ---- Autenticación -------------------------------------------------
    def iniciar_sesion(self, usuario: str, clave: str) -> dict:
        respuesta = self.sesion.post(
            f"{self.base_url}/auth/login",
            json={"usuario": usuario, "clave": clave},
            timeout=5,
        )
        respuesta.raise_for_status()
        self.usuario_actual = respuesta.json()
        return self.usuario_actual

    # ---- Reportes / dashboard -------------------------------------------
    def obtener_dashboard(self) -> dict:
        respuesta = self.sesion.get(f"{self.base_url}/reportes/dashboard", timeout=5)
        respuesta.raise_for_status()
        return respuesta.json()

    # ---- Estudiantes -----------------------------------------------------
    def listar_estudiantes(self, buscar: str | None = None) -> list[dict]:
        parametros = {"buscar": buscar} if buscar else {}
        respuesta = self.sesion.get(
            f"{self.base_url}/estudiantes", params=parametros, timeout=5
        )
        respuesta.raise_for_status()
        return respuesta.json()
