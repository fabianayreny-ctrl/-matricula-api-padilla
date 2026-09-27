"""Ventana de dashboard: KPIs generales + lista de estudiantes."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

import requests

from api_cliente import ClienteAPI

TARJETAS = [
    ("estudiantes_activos", "Estudiantes activos"),
    ("docentes_activos", "Docentes activos"),
    ("carreras_activas", "Carreras activas"),
    ("asignaturas_activas", "Asignaturas activas"),
    ("secciones_abiertas", "Secciones abiertas"),
    ("matriculas_activas", "Matrículas activas"),
]


class VentanaDashboard(tk.Tk):
    def __init__(self, usuario_info: dict):
        super().__init__()
        self.usuario_info = usuario_info
        self.cliente = ClienteAPI()

        self.title("Sistema Académico — Dashboard")
        self.geometry("820x520")
        self.minsize(700, 440)

        self._construir_encabezado()
        self._construir_tarjetas()
        self._construir_tabla_estudiantes()

        self._cargar_datos()

    # ---- Construcción de la interfaz ------------------------------------
    def _construir_encabezado(self) -> None:
        marco = tk.Frame(self, padx=16, pady=12)
        marco.pack(fill="x")
        tk.Label(
            marco,
            text=f"Bienvenido/a, {self.usuario_info['nombre_completo']}",
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left")
        tk.Label(
            marco, text=f"Rol: {self.usuario_info['rol']}", fg="#555555"
        ).pack(side="left", padx=(12, 0))
        tk.Button(marco, text="Actualizar", command=self._cargar_datos).pack(
            side="right"
        )

    def _construir_tarjetas(self) -> None:
        self.marco_tarjetas = tk.Frame(self, padx=16, pady=4)
        self.marco_tarjetas.pack(fill="x")
        self.valores_tarjetas: dict[str, tk.StringVar] = {}

        for indice, (clave, etiqueta) in enumerate(TARJETAS):
            tarjeta = tk.Frame(
                self.marco_tarjetas, relief="groove", borderwidth=1, padx=12, pady=10
            )
            tarjeta.grid(row=0, column=indice, sticky="nsew", padx=4)
            self.marco_tarjetas.columnconfigure(indice, weight=1)

            variable = tk.StringVar(value="—")
            self.valores_tarjetas[clave] = variable
            tk.Label(tarjeta, textvariable=variable, font=("Segoe UI", 18, "bold")).pack()
            tk.Label(tarjeta, text=etiqueta, fg="#555555", wraplength=110).pack()

        self.etiqueta_periodo = tk.Label(self, text="", fg="#555555", padx=16)
        self.etiqueta_periodo.pack(anchor="w")

    def _construir_tabla_estudiantes(self) -> None:
        marco = tk.Frame(self, padx=16, pady=12)
        marco.pack(fill="both", expand=True)

        encabezado = tk.Frame(marco)
        encabezado.pack(fill="x")
        tk.Label(
            encabezado, text="Estudiantes", font=("Segoe UI", 12, "bold")
        ).pack(side="left")

        columnas = ("cuenta", "nombre", "carrera", "estado")
        self.tabla = ttk.Treeview(marco, columns=columnas, show="headings", height=12)
        for columna, titulo in zip(
            columnas, ("Cuenta", "Nombre completo", "Carrera", "Estado")
        ):
            self.tabla.heading(columna, text=titulo)
        self.tabla.column("cuenta", width=100)
        self.tabla.column("nombre", width=240)
        self.tabla.column("carrera", width=220)
        self.tabla.column("estado", width=100)
        self.tabla.pack(fill="both", expand=True, pady=(8, 0))

    # ---- Carga de datos ---------------------------------------------------
    def _cargar_datos(self) -> None:
        try:
            resumen = self.cliente.obtener_dashboard()
            estudiantes = self.cliente.listar_estudiantes()
        except requests.exceptions.RequestException:
            messagebox.showerror(
                "Sin conexión", "No se pudo obtener información de la API."
            )
            return

        for clave, variable in self.valores_tarjetas.items():
            variable.set(str(resumen.get(clave, "—")))
        self.etiqueta_periodo.config(
            text=f"Período académico activo: {resumen.get('periodo_activo', 'N/D')}"
        )

        for fila in self.tabla.get_children():
            self.tabla.delete(fila)
        for estudiante in estudiantes:
            self.tabla.insert(
                "",
                "end",
                values=(
                    estudiante["cuenta"],
                    f"{estudiante['nombres']} {estudiante['apellidos']}",
                    estudiante["carrera_nombre"],
                    estudiante["estado"],
                ),
            )


if __name__ == "__main__":
    # Permite probar solo esta ventana durante el desarrollo, sin login.
    VentanaDashboard(
        {"nombre_completo": "Prueba", "rol": "ADMIN"}
    ).mainloop()
