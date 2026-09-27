"""Ventana de inicio de sesión del cliente de escritorio."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

import requests

from api_cliente import ClienteAPI


class VentanaLogin(tk.Tk):
    def __init__(self, al_iniciar_sesion):
        super().__init__()
        self.al_iniciar_sesion = al_iniciar_sesion
        self.cliente = ClienteAPI()

        self.title("Sistema Académico — Iniciar sesión")
        self.geometry("380x260")
        self.resizable(False, False)
        self.configure(padx=24, pady=24)

        tk.Label(
            self, text="Sistema Académico", font=("Segoe UI", 16, "bold")
        ).pack(pady=(0, 4))
        tk.Label(
            self, text="Programación III — Proyecto de curso", fg="#555555"
        ).pack(pady=(0, 16))

        tk.Label(self, text="Usuario").pack(anchor="w")
        self.entrada_usuario = tk.Entry(self)
        self.entrada_usuario.pack(fill="x", pady=(0, 10))
        self.entrada_usuario.insert(0, "admin")

        tk.Label(self, text="Contraseña").pack(anchor="w")
        self.entrada_clave = tk.Entry(self, show="*")
        self.entrada_clave.pack(fill="x", pady=(0, 16))

        self.boton_entrar = tk.Button(
            self, text="Iniciar sesión", command=self._intentar_login
        )
        self.boton_entrar.pack(fill="x")

        self.etiqueta_estado = tk.Label(self, text="", fg="#B00020")
        self.etiqueta_estado.pack(pady=(10, 0))

        self.bind("<Return>", lambda evento: self._intentar_login())
        self.entrada_usuario.focus_set()

    def _intentar_login(self) -> None:
        usuario = self.entrada_usuario.get().strip()
        clave = self.entrada_clave.get()

        if not usuario or not clave:
            self.etiqueta_estado.config(text="Ingrese usuario y contraseña.")
            return

        try:
            usuario_info = self.cliente.iniciar_sesion(usuario, clave)
        except requests.exceptions.ConnectionError:
            messagebox.showerror(
                "Sin conexión",
                "No se pudo conectar con la API.\n\n"
                "Verifique que esté corriendo:\n"
                "uvicorn app.main:app --reload",
            )
            return
        except requests.exceptions.HTTPError as error:
            if error.response is not None and error.response.status_code == 401:
                self.etiqueta_estado.config(text="Usuario o contraseña incorrectos.")
            else:
                self.etiqueta_estado.config(text="No se pudo iniciar sesión.")
            return

        self.destroy()
        self.al_iniciar_sesion(usuario_info)


if __name__ == "__main__":
    # Permite probar solo esta ventana durante el desarrollo.
    VentanaLogin(al_iniciar_sesion=print).mainloop()
