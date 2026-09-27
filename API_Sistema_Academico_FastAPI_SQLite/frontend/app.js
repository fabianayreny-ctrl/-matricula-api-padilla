// Sistema Académico — frontend (vanilla JS, sin dependencias).
// Como este archivo se sirve desde la misma API (FastAPI + StaticFiles),
// las rutas son relativas: no hay problema de CORS.

const URL_BASE_API = "/api/v1";

const vistaLogin = document.getElementById("vista-login");
const vistaDashboard = document.getElementById("vista-dashboard");

const formularioLogin = document.getElementById("formulario-login");
const campoUsuario = document.getElementById("campo-usuario");
const campoClave = document.getElementById("campo-clave");
const botonEntrar = document.getElementById("boton-entrar");
const mensajeLogin = document.getElementById("mensaje-login");

const tituloBienvenida = document.getElementById("titulo-bienvenida");
const chipUsuario = document.getElementById("chip-usuario");
const botonActualizar = document.getElementById("boton-actualizar");
const botonSalir = document.getElementById("boton-salir");
const filaTarjetas = document.getElementById("fila-tarjetas");
const textoPeriodo = document.getElementById("texto-periodo");
const campoBuscar = document.getElementById("campo-buscar");
const cuerpoTablaEstudiantes = document.getElementById("cuerpo-tabla-estudiantes");
const textoSinResultados = document.getElementById("texto-sin-resultados");

const tituloFormulario = document.getElementById("titulo-formulario");
const formularioEstudiante = document.getElementById("formulario-estudiante");
const campoEstudianteId = document.getElementById("estudiante-id");
const campoNombres = document.getElementById("estudiante-nombres");
const campoApellidos = document.getElementById("estudiante-apellidos");
const campoCuenta = document.getElementById("estudiante-cuenta");
const campoCorreo = document.getElementById("estudiante-correo");
const campoTelefono = document.getElementById("estudiante-telefono");
const campoNacimiento = document.getElementById("estudiante-nacimiento");
const campoCarrera = document.getElementById("estudiante-carrera");
const campoEstado = document.getElementById("estudiante-estado");
const botonGuardarEstudiante = document.getElementById("boton-guardar-estudiante");
const botonCancelarEdicion = document.getElementById("boton-cancelar-edicion");
const mensajeFormulario = document.getElementById("mensaje-formulario");

let usuarioActual = null;
let temporizadorBusqueda = null;

const TARJETAS_KPI = [
  { clave: "estudiantes_activos", etiqueta: "Estudiantes activos" },
  { clave: "docentes_activos", etiqueta: "Docentes activos" },
  { clave: "carreras_activas", etiqueta: "Carreras activas" },
  { clave: "asignaturas_activas", etiqueta: "Asignaturas activas" },
  { clave: "secciones_abiertas", etiqueta: "Secciones abiertas" },
  { clave: "matriculas_activas", etiqueta: "Matrículas activas" },
];

// ------------------------- Autenticación -------------------------

formularioLogin.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  mensajeLogin.textContent = "";
  botonEntrar.disabled = true;
  botonEntrar.textContent = "Entrando...";

  try {
    const respuesta = await fetch(`${URL_BASE_API}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        usuario: campoUsuario.value.trim(),
        clave: campoClave.value,
      }),
    });

    if (!respuesta.ok) {
      mensajeLogin.textContent =
        respuesta.status === 401
          ? "Usuario o contraseña incorrectos."
          : "No se pudo iniciar sesión.";
      return;
    }

    usuarioActual = await respuesta.json();
    mostrarDashboard();
  } catch (error) {
    mensajeLogin.textContent =
      "No se pudo conectar con la API. ¿Está corriendo uvicorn?";
  } finally {
    botonEntrar.disabled = false;
    botonEntrar.textContent = "Iniciar sesión";
  }
});

botonSalir.addEventListener("click", () => {
  usuarioActual = null;
  formularioLogin.reset();
  vistaDashboard.classList.add("oculto");
  vistaLogin.classList.remove("oculto");
});

// ------------------------- Dashboard -------------------------

function mostrarDashboard() {
  vistaLogin.classList.add("oculto");
  vistaDashboard.classList.remove("oculto");

  tituloBienvenida.textContent = `Hola, ${usuarioActual.nombre_completo}`;
  chipUsuario.textContent = `Rol: ${usuarioActual.rol}`;

  construirTarjetasVacias();
  cargarDashboard();
  cargarCarreras();
  cargarEstudiantes();
}

function construirTarjetasVacias() {
  filaTarjetas.innerHTML = "";
  TARJETAS_KPI.forEach(({ clave, etiqueta }) => {
    const tarjeta = document.createElement("article");
    tarjeta.className = "tarjeta-kpi";
    tarjeta.innerHTML = `
      <div class="valor" data-kpi="${clave}">—</div>
      <div class="etiqueta-kpi">${etiqueta}</div>
    `;
    filaTarjetas.appendChild(tarjeta);
  });
}

async function cargarDashboard() {
  try {
    const respuesta = await fetch(`${URL_BASE_API}/reportes/dashboard`);
    if (!respuesta.ok) throw new Error("dashboard no disponible");
    const resumen = await respuesta.json();

    TARJETAS_KPI.forEach(({ clave }) => {
      const nodo = filaTarjetas.querySelector(`[data-kpi="${clave}"]`);
      if (nodo) nodo.textContent = resumen[clave] ?? "—";
    });

    textoPeriodo.textContent = resumen.periodo_activo
      ? `Período académico activo: ${resumen.periodo_activo}`
      : "No hay un período académico activo.";
  } catch (error) {
    textoPeriodo.textContent = "No se pudieron cargar los indicadores.";
  }
}

// ------------------------- Carreras (para el <select>) -------------------------

async function cargarCarreras() {
  try {
    const respuesta = await fetch(`${URL_BASE_API}/carreras?solo_activas=true`);
    if (!respuesta.ok) throw new Error("carreras no disponible");
    const carreras = await respuesta.json();

    campoCarrera.innerHTML = '<option value="">Seleccione una carrera</option>';
    carreras.forEach((carrera) => {
      const opcion = document.createElement("option");
      opcion.value = carrera.id;
      opcion.textContent = `${carrera.codigo} — ${carrera.nombre}`;
      campoCarrera.appendChild(opcion);
    });
  } catch (error) {
    campoCarrera.innerHTML = '<option value="">No se pudieron cargar las carreras</option>';
  }
}

// ------------------------- Crear / editar estudiante -------------------------

formularioEstudiante.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  mensajeFormulario.textContent = "";
  mensajeFormulario.className = "mensaje-error";

  const datos = {
    nombres: campoNombres.value.trim(),
    apellidos: campoApellidos.value.trim(),
    cuenta: campoCuenta.value.trim(),
    correo: campoCorreo.value.trim(),
    telefono: campoTelefono.value.trim() || null,
    fecha_nacimiento: campoNacimiento.value,
    carrera_id: Number(campoCarrera.value),
    estado: campoEstado.value,
  };

  const idEnEdicion = campoEstudianteId.value;
  const esEdicion = Boolean(idEnEdicion);

  botonGuardarEstudiante.disabled = true;
  botonGuardarEstudiante.textContent = "Guardando...";

  try {
    const respuesta = await fetch(
      `${URL_BASE_API}/estudiantes${esEdicion ? `/${idEnEdicion}` : ""}`,
      {
        method: esEdicion ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(datos),
      }
    );

    if (!respuesta.ok) {
      const detalle = await respuesta.json().catch(() => null);
      mensajeFormulario.textContent =
        detalle?.detail ?? "No se pudo guardar el estudiante. Revise los datos.";
      return;
    }

    mensajeFormulario.textContent = esEdicion
      ? "Estudiante actualizado correctamente."
      : "Estudiante creado correctamente.";
    mensajeFormulario.className = "mensaje-exito";

    cancelarEdicion();
    cargarDashboard();
    cargarEstudiantes(campoBuscar.value.trim());
  } catch (error) {
    mensajeFormulario.textContent = "No se pudo conectar con la API.";
  } finally {
    botonGuardarEstudiante.disabled = false;
    botonGuardarEstudiante.textContent = "Guardar estudiante";
  }
});

function editarEstudiante(estudiante) {
  campoEstudianteId.value = estudiante.id;
  campoNombres.value = estudiante.nombres;
  campoApellidos.value = estudiante.apellidos;
  campoCuenta.value = estudiante.cuenta;
  campoCorreo.value = estudiante.correo;
  campoTelefono.value = estudiante.telefono ?? "";
  campoNacimiento.value = estudiante.fecha_nacimiento;
  campoCarrera.value = estudiante.carrera_id;
  campoEstado.value = estudiante.estado;

  tituloFormulario.textContent = `Editar estudiante — ${estudiante.nombres} ${estudiante.apellidos}`;
  botonGuardarEstudiante.textContent = "Guardar cambios";
  botonCancelarEdicion.classList.remove("oculto");
  mensajeFormulario.textContent = "";
  formularioEstudiante.scrollIntoView({ behavior: "smooth", block: "start" });
}

function cancelarEdicion() {
  formularioEstudiante.reset();
  campoEstudianteId.value = "";
  tituloFormulario.textContent = "Nuevo estudiante";
  botonGuardarEstudiante.textContent = "Guardar estudiante";
  botonCancelarEdicion.classList.add("oculto");
}

botonCancelarEdicion.addEventListener("click", cancelarEdicion);

async function eliminarEstudiante(estudiante) {
  const confirmado = window.confirm(
    `¿Eliminar a ${estudiante.nombres} ${estudiante.apellidos}? Esta acción no se puede deshacer.`
  );
  if (!confirmado) return;

  try {
    const respuesta = await fetch(`${URL_BASE_API}/estudiantes/${estudiante.id}`, {
      method: "DELETE",
    });
    if (!respuesta.ok) {
      const detalle = await respuesta.json().catch(() => null);
      window.alert(
        detalle?.detail ?? "No se pudo eliminar (puede tener historial de matrículas)."
      );
      return;
    }
    cargarDashboard();
    cargarEstudiantes(campoBuscar.value.trim());
  } catch (error) {
    window.alert("No se pudo conectar con la API.");
  }
}

// ------------------------- Listado de estudiantes -------------------------

async function cargarEstudiantes(buscar = "") {
  try {
    const parametros = buscar ? `?buscar=${encodeURIComponent(buscar)}` : "";
    const respuesta = await fetch(`${URL_BASE_API}/estudiantes${parametros}`);
    if (!respuesta.ok) throw new Error("estudiantes no disponible");
    const estudiantes = await respuesta.json();
    renderizarTablaEstudiantes(estudiantes);
  } catch (error) {
    cuerpoTablaEstudiantes.innerHTML = "";
    textoSinResultados.textContent = "No se pudo cargar la lista de estudiantes.";
    textoSinResultados.classList.remove("oculto");
  }
}

function renderizarTablaEstudiantes(estudiantes) {
  cuerpoTablaEstudiantes.innerHTML = "";

  if (estudiantes.length === 0) {
    textoSinResultados.textContent = "No se encontraron estudiantes con ese criterio.";
    textoSinResultados.classList.remove("oculto");
    return;
  }
  textoSinResultados.classList.add("oculto");

  estudiantes.forEach((estudiante) => {
    const fila = document.createElement("tr");
    fila.innerHTML = `
      <td>${estudiante.cuenta}</td>
      <td>${estudiante.nombres} ${estudiante.apellidos}</td>
      <td>${estudiante.correo}</td>
      <td>${estudiante.carrera_nombre}</td>
      <td>${pastillaEstado(estudiante.estado)}</td>
      <td class="acciones-fila">
        <button type="button" class="boton-icono" data-accion="editar">Editar</button>
        <button type="button" class="boton-icono peligro" data-accion="eliminar">Eliminar</button>
      </td>
    `;
    fila.querySelector('[data-accion="editar"]').addEventListener("click", () =>
      editarEstudiante(estudiante)
    );
    fila.querySelector('[data-accion="eliminar"]').addEventListener("click", () =>
      eliminarEstudiante(estudiante)
    );
    cuerpoTablaEstudiantes.appendChild(fila);
  });
}

function pastillaEstado(estado) {
  if (estado === "ACTIVO") {
    return `<span class="pastilla-estado pastilla-activo">Activo</span>`;
  }
  const etiquetas = { INACTIVO: "Inactivo", GRADUADO: "Graduado" };
  return `<span class="pastilla-estado pastilla-neutral">${etiquetas[estado] ?? estado}</span>`;
}

botonActualizar.addEventListener("click", () => {
  cargarDashboard();
  cargarEstudiantes(campoBuscar.value.trim());
});

campoBuscar.addEventListener("input", () => {
  clearTimeout(temporizadorBusqueda);
  temporizadorBusqueda = setTimeout(() => {
    cargarEstudiantes(campoBuscar.value.trim());
  }, 300);
});
