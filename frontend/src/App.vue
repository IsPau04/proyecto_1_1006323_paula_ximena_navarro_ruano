<script setup>
import { ref, onMounted } from 'vue'

const productos = ref([])

const nombre = ref('')
const precio = ref('')
const stock = ref('')

const productoEditando = ref(null)

const mensaje = ref('')
const error = ref('')


// ============================================
// READ - Obtener productos
// ============================================

const obtenerProductos = async () => {
  try {
    error.value = ''

    const respuesta = await fetch('/api/productos')

    if (!respuesta.ok) {
      throw new Error('No fue posible obtener los productos')
    }

    productos.value = await respuesta.json()

  } catch (err) {
    error.value = 'Error al conectar con el backend'
    console.error(err)
  }
}


// ============================================
// CREATE / UPDATE
// ============================================

const guardarProducto = async () => {

  if (!nombre.value || precio.value === '' || stock.value === '') {
    error.value = 'Todos los campos son obligatorios'
    return
  }

  const producto = {
    nombre: nombre.value,
    precio: Number(precio.value),
    stock: Number(stock.value)
  }

  try {

    error.value = ''
    mensaje.value = ''

    if (productoEditando.value) {

      const respuesta = await fetch(
        `/api/productos/${productoEditando.value}`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(producto)
        }
      )

      if (!respuesta.ok) {
        throw new Error('No fue posible actualizar el producto')
      }

      mensaje.value = 'Producto actualizado correctamente'

    } else {

      const respuesta = await fetch('/api/productos', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(producto)
      })

      if (!respuesta.ok) {
        throw new Error('No fue posible crear el producto')
      }

      mensaje.value = 'Producto creado correctamente'
    }

    limpiarFormulario()
    await obtenerProductos()

  } catch (err) {
    error.value = err.message
    console.error(err)
  }
}


// ============================================
// Preparar edición
// ============================================

const editarProducto = (producto) => {

  productoEditando.value = producto.id

  nombre.value = producto.nombre
  precio.value = producto.precio
  stock.value = producto.stock

  mensaje.value = ''
  error.value = ''
}


// ============================================
// DELETE
// ============================================

const eliminarProducto = async (id) => {

  const confirmar = window.confirm(
    '¿Está seguro de eliminar este producto?'
  )

  if (!confirmar) {
    return
  }

  try {

    error.value = ''
    mensaje.value = ''

    const respuesta = await fetch(
      `/api/productos/${id}`,
      {
        method: 'DELETE'
      }
    )

    if (!respuesta.ok) {
      throw new Error('No fue posible eliminar el producto')
    }

    mensaje.value = 'Producto eliminado correctamente'

    await obtenerProductos()

  } catch (err) {
    error.value = err.message
    console.error(err)
  }
}


// ============================================
// Limpiar formulario
// ============================================

const limpiarFormulario = () => {

  nombre.value = ''
  precio.value = ''
  stock.value = ''

  productoEditando.value = null
}


// ============================================
// Cargar productos
// ============================================

onMounted(() => {
  obtenerProductos()
})
</script>


<template>

  <div class="contenedor">

    <header>
      <h1>Proyecto 1</h1>
      <p>Infraestructura Containerizada con Docker</p>
    </header>


    <main>

      <section class="formulario">

        <h2>
          {{ productoEditando ? 'Editar producto' : 'Nuevo producto' }}
        </h2>

        <form @submit.prevent="guardarProducto">

          <label>
            Nombre
            <input
              v-model="nombre"
              type="text"
              placeholder="Nombre del producto"
            >
          </label>


          <label>
            Precio
            <input
              v-model="precio"
              type="number"
              min="0"
              step="0.01"
              placeholder="Precio"
            >
          </label>


          <label>
            Stock
            <input
              v-model="stock"
              type="number"
              min="0"
              placeholder="Cantidad disponible"
            >
          </label>


          <div class="acciones-formulario">

            <button type="submit">
              {{ productoEditando ? 'Actualizar' : 'Guardar' }}
            </button>

            <button
              v-if="productoEditando"
              type="button"
              class="secundario"
              @click="limpiarFormulario"
            >
              Cancelar
            </button>

          </div>

        </form>


        <p
          v-if="mensaje"
          class="mensaje"
        >
          {{ mensaje }}
        </p>

        <p
          v-if="error"
          class="error"
        >
          {{ error }}
        </p>

      </section>


      <section class="productos">

        <div class="titulo-productos">

          <h2>Productos registrados</h2>

          <button
            class="actualizar"
            @click="obtenerProductos"
          >
            Actualizar
          </button>

        </div>


        <table>

          <thead>
            <tr>
              <th>Nombre</th>
              <th>Precio</th>
              <th>Stock</th>
              <th>Acciones</th>
            </tr>
          </thead>


          <tbody>

            <tr
              v-for="producto in productos"
              :key="producto.id"
            >

              <td>{{ producto.nombre }}</td>

              <td>
                Q{{ Number(producto.precio).toFixed(2) }}
              </td>

              <td>{{ producto.stock }}</td>

              <td class="acciones">

                <button
                  class="editar"
                  @click="editarProducto(producto)"
                >
                  Editar
                </button>

                <button
                  class="eliminar"
                  @click="eliminarProducto(producto.id)"
                >
                  Eliminar
                </button>

              </td>

            </tr>


            <tr v-if="productos.length === 0">

              <td
                colspan="4"
                class="sin-productos"
              >
                No existen productos registrados
              </td>

            </tr>

          </tbody>

        </table>

      </section>

    </main>

  </div>

</template>
