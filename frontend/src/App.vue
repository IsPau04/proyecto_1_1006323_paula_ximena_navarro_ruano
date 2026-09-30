<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'

interface Producto { id: string; nombre: string; precio: number; stock: number }
const productos = ref<Producto[]>([])
const nombre = ref('')
const precio = ref<string | number>('')
const stock = ref<string | number>('')
const productoEditando = ref<string | null>(null)
const busqueda = ref('')
const cargando = ref(false)
const guardando = ref(false)
const eliminando = ref(false)
const datosCargados = ref(false)
const error = ref('')
const errorCarga = ref(false)
const mensaje = ref('')
const ultimaConsulta = ref('')
const validacion = ref({ nombre: '', precio: '', stock: '' })
const campoNombre = ref<HTMLInputElement | null>(null)
const dialogo = ref<HTMLDialogElement | null>(null)
const productoEliminar = ref<Producto | null>(null)
const errorEliminar = ref('')
const ocupado = computed(() => cargando.value || guardando.value || eliminando.value)
const normalizar = (texto: string) => texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('es')
const filtrados = computed(() => productos.value.filter(p => normalizar(p.nombre).includes(normalizar(busqueda.value.trim()))))
const unidades = computed(() => productos.value.reduce((total, p) => total + p.stock, 0))
const valor = computed(() => productos.value.reduce((total, p) => total + Math.round(p.precio * 100) * p.stock, 0) / 100)
const moneda = (cantidad: number) => `Q${cantidad.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
const entero = (cantidad: number) => cantidad.toLocaleString('en-US')

// Se conserva el contrato del backend Flask: GET/POST y PUT/DELETE por id.
async function solicitud(ruta: string, opciones: RequestInit = {}) {
  let respuesta: Response
  try {
    respuesta = await fetch(ruta, { ...opciones, signal: AbortSignal.timeout(20000) })
  } catch {
    throw new Error(opciones.method && opciones.method !== 'GET'
      ? 'No se pudo confirmar la operación. Pulsa Actualizar para comprobar los datos antes de intentarlo de nuevo.'
      : 'No se pudo conectar. Comprueba que la aplicación esté activa e intenta actualizar.')
  }
  const datos = await respuesta.json().catch(() => null)
  if (!respuesta.ok) throw new Error(datos?.mensaje || `No se pudo completar la solicitud (${respuesta.status}).`)
  return datos
}
function esProducto(dato: unknown): dato is Producto {
  if (!dato || typeof dato !== 'object') return false
  const p = dato as Producto
  return typeof p.id === 'string' && typeof p.nombre === 'string'
    && typeof p.precio === 'number' && Number.isFinite(p.precio) && p.precio >= 0
    && Number.isSafeInteger(p.stock) && p.stock >= 0
}
const textoError = (err: unknown) => err instanceof Error ? err.message : 'No se pudo completar la operación.'

async function obtenerProductos() {
  if (ocupado.value) return
  cargando.value = true
  error.value = ''
  mensaje.value = ''
  try {
    const datos = await solicitud('/api/productos')
    if (!Array.isArray(datos) || !datos.every(esProducto)) throw new Error('La respuesta contiene productos con datos inválidos. Revisa nombre, precio y stock.')
    productos.value = datos
    datosCargados.value = true
    errorCarga.value = false
    ultimaConsulta.value = new Date().toLocaleTimeString('es-GT', { hour: '2-digit', minute: '2-digit' })
  } catch (err) {
    error.value = textoError(err)
    errorCarga.value = true
  } finally {
    cargando.value = false
  }
}
function limpiarFormulario() {
  nombre.value = ''
  precio.value = ''
  stock.value = ''
  productoEditando.value = null
  validacion.value = { nombre: '', precio: '', stock: '' }
}
async function enfocarFormulario() {
  await nextTick()
  campoNombre.value?.focus()
}
function validarFormulario() {
  const p = Number(precio.value)
  const s = Number(stock.value)
  validacion.value = {
    nombre: nombre.value.trim() ? '' : 'Escribe el nombre del producto.',
    precio: precio.value === '' || !Number.isFinite(p) || p < 0
      ? 'Ingresa un precio válido mayor o igual a cero.'
      : Math.abs(p * 100 - Math.round(p * 100)) > 0.00001 ? 'Usa un máximo de dos decimales.' : '',
    stock: stock.value === '' || !Number.isSafeInteger(s) || s < 0
      ? 'Ingresa una cantidad entera mayor o igual a cero.' : '',
  }
  return !Object.values(validacion.value).some(Boolean)
}
async function guardarProducto() {
  if (ocupado.value) return
  error.value = ''
  mensaje.value = ''
  if (!validarFormulario()) {
    await nextTick()
    document.querySelector<HTMLInputElement>('[aria-invalid="true"]')?.focus()
    return
  }
  guardando.value = true
  const id = productoEditando.value
  try {
    const guardado = await solicitud(id ? `/api/productos/${encodeURIComponent(id)}` : '/api/productos', {
      method: id ? 'PUT' : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nombre: nombre.value.trim(), precio: Number(precio.value), stock: Number(stock.value) }),
    })
    if (!esProducto(guardado)) throw new Error('El servidor respondió sin los datos esperados. Pulsa Actualizar antes de volver a guardar.')
    // El servidor devuelve el producto persistido; los indicadores usan esos datos reales.
    const posicion = productos.value.findIndex(p => p.id === guardado.id)
    if (posicion >= 0) productos.value[posicion] = guardado
    else productos.value.push(guardado)
    limpiarFormulario()
    busqueda.value = ''
    mensaje.value = id ? 'Producto actualizado correctamente.' : 'Producto registrado correctamente.'
  } catch (err) {
    error.value = textoError(err)
  } finally {
    guardando.value = false
  }
}
function editarProducto(producto: Producto) {
  if (ocupado.value) return
  productoEditando.value = producto.id
  nombre.value = producto.nombre
  precio.value = producto.precio
  stock.value = producto.stock
  validacion.value = { nombre: '', precio: '', stock: '' }
  mensaje.value = ''
  error.value = ''
  void enfocarFormulario()
}
function abrirEliminar(producto: Producto) {
  if (ocupado.value) return
  productoEliminar.value = producto
  errorEliminar.value = ''
  dialogo.value?.showModal()
}
function cerrarEliminar() {
  if (eliminando.value) return
  dialogo.value?.close()
  productoEliminar.value = null
}
function cancelarDialogo(evento: Event) {
  evento.preventDefault()
  cerrarEliminar()
}
async function eliminarProducto() {
  if (!productoEliminar.value || ocupado.value) return
  eliminando.value = true
  errorEliminar.value = ''
  mensaje.value = ''
  error.value = ''
  const id = productoEliminar.value.id
  try {
    await solicitud(`/api/productos/${encodeURIComponent(id)}`, { method: 'DELETE' })
    productos.value = productos.value.filter(p => p.id !== id)
    if (productoEditando.value === id) limpiarFormulario()
    dialogo.value?.close()
    productoEliminar.value = null
    mensaje.value = 'Producto eliminado correctamente.'
  } catch (err) {
    errorEliminar.value = textoError(err)
  } finally {
    eliminando.value = false
  }
}
onMounted(obtenerProductos)
</script>

<template>
  <!-- Iconos locales: no requieren fuentes, CDN ni paquetes adicionales. -->
  <svg class="iconos-definiciones" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <defs>
      <symbol id="i-cesta" viewBox="0 0 24 24"><path d="m8 3-5 7m13-7 5 7M2 10h20l-3 11H5L2 10Zm7 4v3m6-3v3" /></symbol>
      <symbol id="i-caja" viewBox="0 0 24 24"><path d="M3 3h18v5H3zM5 8v13h14V8M9 12h6" /></symbol>
      <symbol id="i-etiqueta" viewBox="0 0 24 24"><path d="M3 5h12l6 7-6 7H3V5Zm5 7h.01" /></symbol>
      <symbol id="i-capas" viewBox="0 0 24 24"><path d="m12 3 10 6-10 6L2 9l10-6Zm-10 12 10 6 10-6M2 12l10 6 10-6" /></symbol>
      <symbol id="i-dinero" viewBox="0 0 24 24"><path d="M5 4h17v13H5zM2 8v12h17M9 8h.01M18 13h.01" /><circle cx="13.5" cy="10.5" r="2.5" /></symbol>
      <symbol id="i-mas" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="3" /><path d="M12 7v10m-5-5h10" /></symbol>
      <symbol id="i-guardar" viewBox="0 0 24 24"><path d="M4 3h13l4 4v14H3V3h1Zm3 0v6h9V3M7 21v-8h10v8" /></symbol>
      <symbol id="i-buscar" viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5" /><path d="m16 16 5 5" /></symbol>
      <symbol id="i-actualizar" viewBox="0 0 24 24"><path d="M20 7a9 9 0 1 0 1 9M20 3v5h-5" /></symbol>
      <symbol id="i-editar" viewBox="0 0 24 24"><path d="m15 4 5 5M4 15 16 3a2 2 0 0 1 3 0l2 2a2 2 0 0 1 0 3L9 20l-6 1 1-6Z" /></symbol>
      <symbol id="i-eliminar" viewBox="0 0 24 24"><path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7" /></symbol>
      <symbol id="i-check" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="m8 12 3 3 5-6" /></symbol>
      <symbol id="i-cerrar" viewBox="0 0 24 24"><path d="m6 6 12 12M6 18 18 6" /></symbol>
      <symbol id="i-alerta" viewBox="0 0 24 24"><path d="m12 3 10 18H2L12 3Zm0 6v5m0 3h.01" /></symbol>
    </defs>
  </svg>

  <a class="saltar" href="#contenido">Saltar al inventario</a>
  <header class="cabecera">
    <div class="ancho cabecera-interior">
      <div class="marca"><span class="marca-icono"><svg class="icono"><use href="#i-cesta" /></svg></span><strong>Mi Súper</strong><span class="marca-subtitulo">Control de inventario</span></div>
      <span class="seccion-activa"><svg class="icono"><use href="#i-caja" /></svg> Inventario</span>
    </div>
  </header>

  <main id="contenido" class="ancho contenido">
    <div class="introduccion"><p class="sobretitulo"><svg class="icono"><use href="#i-caja" /></svg> MÓDULO DE ALMACÉN</p><h1>Inventario de productos</h1><p>Administra tus productos, precios y existencias en un solo lugar.</p></div>

    <div v-if="mensaje" class="aviso exito" role="status"><svg class="icono"><use href="#i-check" /></svg><span>{{ mensaje }}</span><button class="boton-icono" aria-label="Cerrar aviso" @click="mensaje = ''"><svg class="icono"><use href="#i-cerrar" /></svg></button></div>
    <div v-if="error" class="aviso fallo" role="alert"><svg class="icono"><use href="#i-alerta" /></svg><span>{{ error }}<small v-if="errorCarga && datosCargados">Se muestran los últimos datos disponibles.</small></span></div>

    <section class="resumen" aria-label="Resumen del inventario completo">
      <article class="tarjeta indicador"><div><p>Productos registrados</p><strong data-testid="total-productos">{{ datosCargados ? entero(productos.length) : '—' }}</strong><small><span class="punto"></span> Variedad en tu catálogo</small></div><span class="indicador-icono"><svg class="icono"><use href="#i-etiqueta" /></svg></span></article>
      <article class="tarjeta indicador"><div><p>Unidades disponibles</p><strong data-testid="total-unidades">{{ datosCargados ? entero(unidades) : '—' }}</strong><small><svg class="icono"><use href="#i-capas" /></svg> Existencias registradas</small></div><span class="indicador-icono"><svg class="icono"><use href="#i-capas" /></svg></span></article>
      <article class="tarjeta indicador valor"><div><p>Valor del inventario</p><strong data-testid="total-valor">{{ datosCargados ? moneda(valor) : '—' }}</strong><small><svg class="icono"><use href="#i-dinero" /></svg> Total de precio × stock</small></div><span class="indicador-icono"><svg class="icono"><use href="#i-dinero" /></svg></span></article>
    </section>

    <div class="paneles">
      <section class="tarjeta panel-formulario" aria-labelledby="titulo-formulario">
        <div class="encabezado-panel"><span class="icono-panel"><svg class="icono"><use :href="productoEditando ? '#i-editar' : '#i-mas'" /></svg></span><div><h2 id="titulo-formulario">{{ productoEditando ? 'Editar producto' : 'Agregar producto' }}</h2><p>{{ productoEditando ? 'Actualiza la información del producto' : 'Ingresa los datos para registrar' }}</p></div></div>
        <form class="formulario" novalidate @submit.prevent="guardarProducto">
          <fieldset :disabled="ocupado">
            <div class="campo"><label for="nombre">Nombre del producto <span>*</span></label><input id="nombre" ref="campoNombre" v-model="nombre" type="text" placeholder="Ej. Arroz blanco 1 lb" required :aria-invalid="!!validacion.nombre" aria-describedby="ayuda-nombre" @input="validacion.nombre = ''"><small id="ayuda-nombre" :class="{ 'texto-error': validacion.nombre }">{{ validacion.nombre || 'Nombre obligatorio y descriptivo' }}</small></div>
            <div class="campo"><label for="precio">Precio unitario <span>*</span></label><div class="campo-moneda"><span aria-hidden="true">Q</span><input id="precio" v-model="precio" type="number" min="0" step="0.01" inputmode="decimal" placeholder="0.00" required :aria-invalid="!!validacion.precio" aria-describedby="ayuda-precio" @input="validacion.precio = ''"></div><small id="ayuda-precio" :class="{ 'texto-error': validacion.precio }">{{ validacion.precio || 'Precio en quetzales, mayor o igual a cero' }}</small></div>
            <div class="campo"><label for="stock">Stock disponible <span>*</span></label><div class="campo-unidades"><input id="stock" v-model="stock" type="number" min="0" step="1" inputmode="numeric" placeholder="0" required :aria-invalid="!!validacion.stock" aria-describedby="ayuda-stock" @input="validacion.stock = ''"><span aria-hidden="true">unidades</span></div><small id="ayuda-stock" :class="{ 'texto-error': validacion.stock }">{{ validacion.stock || 'Cantidad entera mayor o igual a cero' }}</small></div>
            <button class="boton principal ancho-completo" type="submit"><span v-if="guardando" class="spinner" aria-hidden="true"></span><svg v-else class="icono"><use href="#i-guardar" /></svg>{{ guardando ? 'Guardando…' : productoEditando ? 'Guardar cambios' : 'Guardar producto' }}</button>
            <button v-if="productoEditando" class="boton secundario ancho-completo cancelar-edicion" type="button" @click="limpiarFormulario">Cancelar edición</button>
          </fieldset>
        </form>
      </section>

      <section class="tarjeta panel-productos" aria-labelledby="titulo-productos" :aria-busy="cargando">
        <div class="barra-productos"><h2 id="titulo-productos">Productos registrados</h2><div class="herramientas"><div class="buscador"><svg class="icono"><use href="#i-buscar" /></svg><input v-model="busqueda" type="search" aria-label="Buscar producto por nombre" placeholder="Buscar producto por nombre…"></div><button class="boton secundario" :disabled="ocupado" @click="obtenerProductos"><svg class="icono" :class="{ girar: cargando }"><use href="#i-actualizar" /></svg>{{ cargando ? 'Actualizando…' : 'Actualizar' }}</button></div></div>

        <div v-if="cargando && !datosCargados" class="estado" role="status"><span class="spinner grande"></span><h3>Cargando inventario…</h3><p>Consultando productos y existencias.</p></div>
        <div v-else-if="!datosCargados && errorCarga" class="estado"><span class="estado-icono"><svg class="icono"><use href="#i-alerta" /></svg></span><h3>No se pudo cargar el inventario</h3><p>Pulsa Actualizar para volver a intentarlo.</p></div>
        <div v-else-if="productos.length === 0" class="estado"><span class="estado-icono"><svg class="icono"><use href="#i-cesta" /></svg></span><h3>Todavía no hay productos registrados</h3><p>Agrega tu primer producto con su precio y existencias.</p><button class="boton principal" :disabled="ocupado" @click="enfocarFormulario">Registrar primer producto</button></div>
        <div v-else-if="filtrados.length === 0" class="estado"><span class="estado-icono"><svg class="icono"><use href="#i-buscar" /></svg></span><h3>No encontramos ese producto</h3><p>Prueba con otro nombre o limpia la búsqueda.</p><button class="boton secundario" @click="busqueda = ''">Limpiar búsqueda</button></div>
        <div v-else class="tabla-contenedor">
          <table><thead><tr><th scope="col">Producto</th><th scope="col" class="derecha">Precio unitario</th><th scope="col" class="centro">Stock</th><th scope="col" class="derecha">Acciones</th></tr></thead>
            <tbody><tr v-for="producto in filtrados" :key="producto.id" :class="{ 'fila-editando': productoEditando === producto.id }">
              <td class="celda-producto"><span class="avatar">{{ producto.nombre.trim().charAt(0).toUpperCase() || 'P' }}</span><span class="nombre-producto">{{ producto.nombre }}<small v-if="productoEditando === producto.id">Editando</small></span></td>
              <td class="precio-producto derecha" data-label="Precio unitario">{{ moneda(producto.precio) }}</td>
              <td class="centro" data-label="Stock"><span class="insignia-stock" :class="{ agotado: producto.stock === 0 }"><span class="punto"></span>{{ producto.stock === 0 ? 'Sin existencias' : `${entero(producto.stock)} ${producto.stock === 1 ? 'unidad' : 'unidades'}` }}</span></td>
              <td class="derecha acciones"><button class="boton-icono editar" :disabled="ocupado" :aria-label="`Editar ${producto.nombre}`" :title="`Editar ${producto.nombre}`" @click="editarProducto(producto)"><svg class="icono"><use href="#i-editar" /></svg><span class="etiqueta-movil">Editar</span></button><button class="boton-icono eliminar" :disabled="ocupado" :aria-label="`Eliminar ${producto.nombre}`" :title="`Eliminar ${producto.nombre}`" @click="abrirEliminar(producto)"><svg class="icono"><use href="#i-eliminar" /></svg><span class="etiqueta-movil">Eliminar</span></button></td>
            </tr></tbody>
          </table>
        </div>
        <div class="pie-tabla"><span>{{ datosCargados ? `Mostrando ${filtrados.length} de ${productos.length} productos` : 'Esperando datos' }}</span><span class="estado-consulta" :class="{ pendiente: errorCarga }"><span class="punto"></span>{{ cargando ? 'Consultando…' : errorCarga ? 'Consulta pendiente' : ultimaConsulta ? `Última consulta: ${ultimaConsulta}` : 'Conectando…' }}</span></div>
      </section>
    </div>
  </main>

  <footer class="pie"><div class="ancho"><span>Mi Súper · Control de inventario</span><span>Productos en orden, todo más simple.</span></div></footer>

  <dialog ref="dialogo" class="dialogo" aria-labelledby="titulo-eliminar" aria-describedby="descripcion-eliminar" @cancel="cancelarDialogo">
    <div class="dialogo-contenido"><span class="alerta-icono"><svg class="icono"><use href="#i-alerta" /></svg></span><h2 id="titulo-eliminar">¿Eliminar producto?</h2><p id="descripcion-eliminar">Vas a eliminar <strong>{{ productoEliminar?.nombre }}</strong> del inventario. Esta acción no se puede deshacer.</p><p v-if="errorEliminar" class="error-dialogo" role="alert">{{ errorEliminar }}</p><div class="dialogo-acciones"><button class="boton secundario" autofocus :disabled="eliminando" @click="cerrarEliminar">Cancelar</button><button class="boton peligro" :disabled="eliminando" @click="eliminarProducto"><span v-if="eliminando" class="spinner"></span><svg v-else class="icono"><use href="#i-eliminar" /></svg>{{ eliminando ? 'Eliminando…' : 'Eliminar producto' }}</button></div></div>
  </dialog>
</template>

<style>
:root { font-family: Inter, 'Segoe UI', system-ui, -apple-system, sans-serif; color: #1f2535; background: #f7f5fe; font-synthesis: none; text-rendering: optimizeLegibility; -webkit-font-smoothing: antialiased; --morado: #7022db; --morado-oscuro: #5915b8; --lila: #f1ecfc; --borde: #ece5f8; --muted: #625b70; --error: #b42332; }
* { box-sizing: border-box; }
body { margin: 0; min-width: 320px; }
#app { min-height: 100vh; display: flex; flex-direction: column; }
button, input { font: inherit; }
button { cursor: pointer; }
button:disabled, fieldset:disabled button { cursor: wait; opacity: .58; }
button, input { -webkit-tap-highlight-color: transparent; }
button:focus-visible, input:focus-visible, a:focus-visible { outline: 3px solid #b999f4; outline-offset: 3px; }
h1, h2, h3, p { margin: 0; }
.iconos-definiciones { position: absolute; width: 0; height: 0; overflow: hidden; }
.icono { width: 21px; height: 21px; flex: 0 0 auto; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; stroke-linejoin: round; vertical-align: middle; }
.ancho { width: min(1280px, 100%); padding-inline: 32px; margin-inline: auto; }
.saltar { position: fixed; top: -80px; left: 16px; z-index: 10; background: white; padding: 12px; color: var(--morado); }
.saltar:focus { top: 8px; }
.cabecera { background: #fcfbff; border-bottom: 1px solid var(--borde); }
.cabecera-interior { min-height: 74px; display: flex; align-items: center; justify-content: space-between; gap: 20px; }
.marca { display: flex; align-items: center; gap: 10px; }
.marca strong { font-size: 21px; letter-spacing: -.7px; white-space: nowrap; }
.marca-icono { width: 40px; height: 40px; border-radius: 12px; background: #eaddff; color: var(--morado); display: grid; place-items: center; }
.marca-icono .icono { width: 25px; height: 25px; }
.marca-subtitulo { font-size: 13px; color: var(--muted); margin-left: 3px; }
.seccion-activa { display: flex; align-items: center; gap: 7px; font-size: 13px; font-weight: 650; color: var(--morado); background: #f1eaff; padding: 9px 14px; border-radius: 9px; }
.seccion-activa .icono { width: 17px; height: 17px; }
.contenido { flex: 1; padding-top: 32px; padding-bottom: 38px; }
.introduccion { margin-bottom: 28px; }
.sobretitulo { display: flex; align-items: center; gap: 6px; color: var(--morado); font-size: 11px; font-weight: 650; letter-spacing: .65px; margin-bottom: 8px; }
.sobretitulo .icono { width: 17px; height: 17px; }
h1 { font-size: clamp(24px, 3vw, 30px); line-height: 1.25; letter-spacing: -1px; margin-bottom: 7px; }
.introduccion > p:last-child { color: var(--muted); font-size: 14px; line-height: 1.6; }
.tarjeta { background: white; border: 1px solid #f0ebf9; border-radius: 15px; box-shadow: 0 2px 3px #32205003; min-width: 0; }
.resumen { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 22px; margin-bottom: 28px; }
.indicador { padding: 23px; display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
.indicador > div { min-width: 0; }
.indicador p { color: var(--muted); font-size: 12px; font-weight: 500; }
.indicador strong { display: block; font-size: clamp(25px, 2.7vw, 36px); line-height: 1.25; letter-spacing: -1px; margin-top: 6px; overflow-wrap: anywhere; font-variant-numeric: tabular-nums; }
.indicador small { display: flex; align-items: center; gap: 6px; color: var(--muted); margin-top: 11px; font-size: 11px; line-height: 1.4; }
.indicador small .icono { width: 14px; height: 14px; }
.punto { display: inline-block; width: 6px; height: 6px; flex: 0 0 auto; border-radius: 50%; background: currentColor; }
.indicador .punto { color: var(--morado); }
.indicador-icono { width: 47px; height: 47px; display: grid; place-items: center; border-radius: 13px; background: #eae1f8; color: var(--morado); flex: 0 0 auto; }
.indicador-icono .icono { width: 25px; height: 25px; }
.valor strong { color: var(--morado); }
.paneles { display: grid; grid-template-columns: minmax(285px, 1fr) minmax(0, 2.06fr); gap: 22px; align-items: start; }
.encabezado-panel { display: flex; align-items: center; gap: 10px; padding: 23px; background: var(--lila); border-radius: 14px 14px 0 0; }
h2 { font-size: 16px; line-height: 1.4; letter-spacing: -.25px; }
.encabezado-panel p { font-size: 12px; color: var(--muted); margin-top: 2px; line-height: 1.5; }
.icono-panel { width: 34px; height: 34px; display: grid; place-items: center; background: #e6d8fb; color: var(--morado); border-radius: 10px; flex-shrink: 0; }
.formulario { padding: 22px 23px 24px; }
fieldset { border: 0; padding: 0; margin: 0; min-width: 0; }
.campo { margin-bottom: 20px; }
.campo label { display: block; font-size: 13px; font-weight: 650; margin-bottom: 8px; }
.campo label > span { color: var(--error); }
input { border: 1px solid transparent; border-radius: 10px; background: #f4f0fc; height: 46px; width: 100%; padding: 0 14px; color: #242033; font-size: 14px; transition: background .15s, border-color .15s; min-width: 0; }
input::placeholder { color: #787082; }
input:focus { border-color: #a079e3; background: white; }
input[aria-invalid="true"] { border-color: var(--error); }
input:disabled { opacity: .7; }
.campo small { display: block; margin-top: 7px; font-size: 11px; color: var(--muted); line-height: 1.5; }
.campo small.texto-error { color: var(--error); }
.campo-moneda, .campo-unidades { position: relative; }
.campo-moneda > span { position: absolute; inset: 1px auto 1px 1px; width: 43px; display: grid; place-items: center; border-radius: 9px 0 0 9px; background: #e9def8; color: var(--morado); font-weight: 750; font-size: 19px; }
.campo-moneda input { padding-left: 56px; font-size: 19px; font-weight: 650; }
.campo-unidades > span { position: absolute; right: 30px; top: 15px; font-size: 11px; color: var(--muted); pointer-events: none; }
.campo-unidades input { padding-right: 90px; }
.boton { min-height: 42px; padding: 10px 16px; display: inline-flex; align-items: center; justify-content: center; gap: 8px; border: 1px solid transparent; border-radius: 10px; font-size: 13px; font-weight: 650; transition: background .15s, box-shadow .15s; line-height: 1.4; }
.boton .icono { width: 18px; height: 18px; }
.principal { color: white; background: var(--morado); box-shadow: 0 3px 6px #7022db20; }
.principal:hover:not(:disabled) { background: var(--morado-oscuro); }
.secundario { background: white; color: var(--morado); border-color: var(--borde); }
.secundario:hover:not(:disabled) { background: #f2eafd; }
.ancho-completo { width: 100%; }
.cancelar-edicion { margin-top: 10px; }
.panel-productos { overflow: hidden; }
.barra-productos { padding: 20px 23px 23px; background: var(--lila); }
.barra-productos h2 { font-size: 14px; margin-bottom: 13px; }
.herramientas { display: flex; align-items: center; gap: 15px; }
.buscador { position: relative; flex: 1; min-width: 0; }
.buscador > .icono { position: absolute; top: 12px; left: 13px; width: 18px; height: 18px; color: var(--muted); }
.buscador input { height: 42px; padding-left: 40px; background: white; font-size: 13px; }
.tabla-contenedor { overflow-x: auto; min-height: 300px; }
table { width: 100%; border-collapse: collapse; font-size: 14px; }
th { padding: 13px 15px; background: #eae3f7; text-transform: uppercase; color: #544b64; font-size: 10px; font-weight: 650; letter-spacing: .45px; white-space: nowrap; }
th:first-child { padding-left: 23px; }
th:last-child { padding-right: 23px; }
td { padding: 19px 15px; border-bottom: 1px solid var(--borde); }
tr:hover td { background: #fcfaff; }
.fila-editando td { background: #f8f3ff; }
.celda-producto { display: flex; align-items: center; gap: 10px; min-height: 80px; padding-left: 23px; }
.avatar { width: 36px; height: 36px; display: grid; place-items: center; background: #e9e0f8; color: var(--morado); font-size: 14px; font-weight: 700; border-radius: 9px; flex: 0 0 auto; }
.nombre-producto { font-weight: 600; overflow-wrap: anywhere; line-height: 1.4; }
.nombre-producto small { display: block; color: var(--morado); font-size: 11px; margin-top: 3px; }
.derecha { text-align: right; }
.centro { text-align: center; }
.precio-producto { font-size: 17px; font-weight: 700; white-space: nowrap; font-variant-numeric: tabular-nums; }
.insignia-stock { display: inline-flex; align-items: center; gap: 6px; padding: 5px 10px; border-radius: 20px; background: #ece3ff; color: #5928a3; font-size: 10px; font-weight: 650; white-space: nowrap; }
.insignia-stock.agotado { color: #a22331; background: #ffe6e9; }
.acciones { white-space: nowrap; padding-right: 17px; }
.boton-icono { display: inline-flex; justify-content: center; align-items: center; gap: 6px; width: 36px; height: 38px; padding: 7px; border: 0; border-radius: 8px; background: transparent; color: inherit; }
.boton-icono .icono { width: 18px; height: 18px; }
.editar { color: var(--morado); }
.editar:hover:not(:disabled) { background: #eee4fc; }
.eliminar { color: var(--error); }
.eliminar:hover:not(:disabled) { background: #ffe8ec; }
.etiqueta-movil { display: none; }
.pie-tabla { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 9px; padding: 16px; color: var(--muted); font-size: 11px; background: var(--lila); }
.estado-consulta { display: flex; align-items: center; gap: 7px; }
.estado-consulta .punto { color: var(--morado); }
.estado-consulta.pendiente .punto { color: #b9700b; }
.estado { min-height: 300px; padding: 32px 24px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 12px; }
.estado h3 { font-size: 16px; }
.estado p { color: var(--muted); font-size: 13px; max-width: 300px; line-height: 1.65; }
.estado-icono { background: #eee4fc; color: var(--morado); padding: 17px; border-radius: 18px; }
.estado-icono .icono { width: 28px; height: 28px; }
.aviso { padding: 13px 16px; margin-bottom: 18px; display: flex; align-items: center; gap: 12px; border-radius: 12px; font-size: 13px; line-height: 1.6; }
.aviso > span { flex: 1; }
.aviso small { display: block; }
.aviso.exito { background: #edf7f1; color: #1e6543; border: 1px solid #cfebda; }
.aviso.fallo { background: #fff0f2; color: #9e2433; border: 1px solid #f7d2d9; }
.pie { background: #f0ebfa; color: var(--muted); padding-block: 22px; font-size: 11px; }
.pie > div { display: flex; justify-content: space-between; gap: 15px; }
.dialogo { border: 1px solid var(--borde); padding: 0; border-radius: 19px; width: min(440px, calc(100% - 32px)); box-shadow: 0 25px 90px #27144140; color: #242033; }
.dialogo::backdrop { background: #20132b70; backdrop-filter: blur(4px); }
.dialogo-contenido { padding: 27px; }
.alerta-icono { display: inline-grid; place-items: center; width: 44px; height: 44px; border-radius: 12px; background: #ffe5ea; color: var(--error); margin-bottom: 17px; }
.dialogo h2 { font-size: 21px; margin-bottom: 10px; }
.dialogo p { font-size: 14px; color: var(--muted); line-height: 1.7; overflow-wrap: anywhere; }
.dialogo-acciones { display: flex; justify-content: flex-end; gap: 10px; margin-top: 25px; }
.peligro { background: #b42332; color: white; }
.peligro:hover:not(:disabled) { background: #941a28; }
p.error-dialogo { background: #fff0f2; color: var(--error); padding: 10px; border-radius: 8px; margin-top: 15px; }
.spinner { display: inline-block; width: 18px; height: 18px; border: 2px solid currentColor; border-right-color: transparent; border-radius: 50%; animation: girar .8s linear infinite; }
.spinner.grande { width: 32px; height: 32px; color: var(--morado); border-width: 3px; }
.girar { animation: girar 1s linear infinite; }
@keyframes girar { to { transform: rotate(360deg); } }
@media (max-width: 1050px) { .ancho { padding-inline: 24px; } .indicador { padding: 19px; } .indicador-icono { width: 37px; height: 37px; } .indicador strong { font-size: 28px; } .paneles { grid-template-columns: minmax(270px, 1fr) minmax(0, 1.8fr); gap: 18px; } .tabla-contenedor table { min-width: 500px; } }
@media (max-width: 800px) { .paneles { grid-template-columns: 1fr; } .marca-subtitulo { display: none; } .indicador-icono { display: none; } .resumen { gap: 12px; } .indicador { padding: 17px; } .indicador strong { font-size: 25px; } .indicador small { font-size: 10px; } .tabla-contenedor table { min-width: 0; } }
@media (max-width: 540px) { .ancho { padding-inline: 18px; } .cabecera-interior { min-height: 66px; } .marca strong { font-size: 20px; } .seccion-activa { padding: 8px 10px; font-size: 11px; } .seccion-activa .icono { display: none; } .contenido { padding-top: 25px; padding-bottom: 26px; } .introduccion { margin-bottom: 22px; } .introduccion > p:last-child { font-size: 13px; } .resumen { grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 22px; } .indicador { padding: 17px; } .indicador p { font-size: 11px; } .indicador strong { font-size: 29px; } .indicador small { font-size: 10px; } .indicador.valor { grid-column: 1 / -1; } .valor .indicador-icono { display: grid; width: 45px; height: 45px; } .encabezado-panel, .formulario { padding: 20px; } .barra-productos { padding: 18px; } .herramientas { flex-wrap: wrap; gap: 10px; } .buscador { flex-basis: 100%; } .herramientas > button { width: 100%; } .tabla-contenedor { min-height: 0; } table, tbody { display: block; } thead { position: absolute; width: 1px; height: 1px; padding: 0; overflow: hidden; clip-path: inset(50%); } tbody tr { display: block; padding: 16px 18px; border-bottom: 1px solid var(--borde); } tbody tr:last-child { border-bottom: 0; } td { display: flex; align-items: center; justify-content: space-between; padding: 7px 0; border: 0; } .celda-producto { min-height: 0; padding: 0 0 13px; justify-content: flex-start; } td[data-label]::before { content: attr(data-label); color: var(--muted); font-size: 12px; font-weight: 400; } .precio-producto { font-size: 17px; } .acciones { padding: 12px 0 0; justify-content: flex-end; gap: 7px; } .acciones .boton-icono { width: auto; padding: 9px 11px; border: 1px solid var(--borde); font-size: 12px; } .etiqueta-movil { display: inline; } .pie > div { flex-direction: column; gap: 6px; } .dialogo-contenido { padding: 22px; } .dialogo-acciones { flex-direction: column-reverse; } .dialogo-acciones .boton { width: 100%; } }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition: none !important; scroll-behavior: auto !important; } }
</style>
