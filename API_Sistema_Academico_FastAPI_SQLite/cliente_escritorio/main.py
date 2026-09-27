"""Punto de entrada del cliente de escritorio.

Flujo: Login -> (si es correcto) -> Dashboard.
Requiere que la API esté corriendo (uvicorn app.main:app --reload) en
http://127.0.0.1:8000 antes de abrir esta ventana.
"""

from login import VentanaLogin
from dashboard import VentanaDashboard


def abrir_dashboard(usuario_info: dict) -> None:
    VentanaDashboard(usuario_info).mainloop()


if __name__ == "__main__":
    VentanaLogin(al_iniciar_sesion=abrir_dashboard).mainloop()
