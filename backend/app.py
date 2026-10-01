from flask import Flask, jsonify, request
from pymongo import MongoClient
from bson import ObjectId
import os

app = Flask(__name__)

# ============================================
# Configuración de MongoDB
# ============================================

MONGO_HOST = os.getenv("MONGO_HOST", "mongodb")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
MONGO_DATABASE = os.getenv("MONGO_DATABASE", "proyecto1_db")

mongo_client = MongoClient(
    host=MONGO_HOST,
    port=MONGO_PORT
)

db = mongo_client[MONGO_DATABASE]


# ============================================
# Función auxiliar
# ============================================

def producto_json(producto):
    return {
        "id": str(producto["_id"]),
        "nombre": producto.get("nombre"),
        "precio": producto.get("precio"),
        "stock": producto.get("stock")
    }


# ============================================
# Ruta de prueba
# ============================================

@app.route("/api/saludo", methods=["GET"])
def saludo():
    return jsonify({
        "mensaje": "Backend del Proyecto 1 funcionando correctamente"
    })


# ============================================
# READ - Obtener todos los productos
# ============================================

@app.route("/api/productos", methods=["GET"])
def obtener_productos():

    productos = []

    for producto in db.productos.find():
        productos.append(producto_json(producto))

    return jsonify(productos), 200


# ============================================
# READ - Obtener un producto
# ============================================

@app.route("/api/productos/<id>", methods=["GET"])
def obtener_producto(id):

    try:
        producto = db.productos.find_one({
            "_id": ObjectId(id)
        })

        if producto is None:
            return jsonify({
                "mensaje": "Producto no encontrado"
            }), 404

        return jsonify(producto_json(producto)), 200

    except Exception:
        return jsonify({
            "mensaje": "ID de producto inválido"
        }), 400


# ============================================
# CREATE - Crear producto
# ============================================

@app.route("/api/productos", methods=["POST"])
def crear_producto():

    datos = request.get_json()

    if not datos:
        return jsonify({
            "mensaje": "No se enviaron datos"
        }), 400

    if (
        "nombre" not in datos
        or "precio" not in datos
        or "stock" not in datos
    ):
        return jsonify({
            "mensaje": "Nombre, precio y stock son obligatorios"
        }), 400

    producto = {
        "nombre": datos["nombre"],
        "precio": datos["precio"],
        "stock": datos["stock"]
    }

    resultado = db.productos.insert_one(producto)

    producto_creado = db.productos.find_one({
        "_id": resultado.inserted_id
    })

    return jsonify(producto_json(producto_creado)), 201


# ============================================
# UPDATE - Actualizar producto
# ============================================

@app.route("/api/productos/<id>", methods=["PUT"])
def actualizar_producto(id):

    try:
        datos = request.get_json()

        if not datos:
            return jsonify({
                "mensaje": "No se enviaron datos"
            }), 400

        campos = {}

        if "nombre" in datos:
            campos["nombre"] = datos["nombre"]

        if "precio" in datos:
            campos["precio"] = datos["precio"]

        if "stock" in datos:
            campos["stock"] = datos["stock"]

        if not campos:
            return jsonify({
                "mensaje": "No hay campos válidos para actualizar"
            }), 400

        resultado = db.productos.update_one(
            {"_id": ObjectId(id)},
            {"$set": campos}
        )

        if resultado.matched_count == 0:
            return jsonify({
                "mensaje": "Producto no encontrado"
            }), 404

        producto_actualizado = db.productos.find_one({
            "_id": ObjectId(id)
        })

        return jsonify(
            producto_json(producto_actualizado)
        ), 200

    except Exception:
        return jsonify({
            "mensaje": "ID de producto inválido"
        }), 400


# ============================================
# DELETE - Eliminar producto
# ============================================

@app.route("/api/productos/<id>", methods=["DELETE"])
def eliminar_producto(id):

    try:
        resultado = db.productos.delete_one({
            "_id": ObjectId(id)
        })

        if resultado.deleted_count == 0:
            return jsonify({
                "mensaje": "Producto no encontrado"
            }), 404

        return jsonify({
            "mensaje": "Producto eliminado correctamente"
        }), 200

    except Exception:
        return jsonify({
            "mensaje": "ID de producto inválido"
        }), 400


# ============================================
# Ejecución
# ============================================

if __name__ == "__main__":
    app.run(
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=int(os.getenv("BACKEND_PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG", "false").lower()
        in ("true", "1", "yes")
    )