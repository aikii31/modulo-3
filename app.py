import os
import sys
import sqlite3
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from database import init_db, obtener_ruta_db

app = Flask(__name__)

# Asegurar que la base de datos se inicie
init_db()

# Ruta para servir el frontend (HTML, CSS, JS)
@app.route('/')
def index():
    # Busca index.html dentro de la carpeta 'web'
    return send_from_directory('web', 'index.html')

@app.route('/<path:path>')
def send_static(path):
    # Sirve los archivos como styles.css, script.js e imágenes desde la carpeta 'web'
    return send_from_directory('web', path)


# --- API ENDPOINTS (RUTAS PARA TU BASE DE DATOS) ---

@app.route('/api/productos', methods=['GET'])
def get_productos():
    conn = sqlite3.connect(obtener_ruta_db())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM productos")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/productos', methods=['POST'])
def agregar_producto():
    try:
        data = request.json
        conn = sqlite3.connect(obtener_ruta_db())
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO productos (nombre, tipo, precio, stock, stock_minimo) VALUES (?, ?, ?, ?, ?)",
            (data['nombre'], data['tipo'], float(data['precio']), int(data['stock']), int(data['stock_minimo']))
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Producto agregado con éxito."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/usuarios', methods=['GET'])
def get_usuarios():
    conn = sqlite3.connect(obtener_ruta_db())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password, rol FROM usuarios")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/ventas', methods=['GET'])
def get_ventas():
    conn = sqlite3.connect(obtener_ruta_db())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ventas ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/ventas', methods=['POST'])
def registrar_venta():
    try:
        data = request.json
        conn = sqlite3.connect(obtener_ruta_db())
        cursor = conn.cursor()
        
        fecha_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO ventas (cliente_nombre, fecha, referencia_pago, total, usuario, estado) VALUES (?, ?, ?, ?, ?, 'ACTIVA')",
            (data['cliente_nombre'], fecha_str, data['referencia_pago'], float(data['total']), data.get('usuario', 'FA'))
        )
        venta_id = cursor.lastrowid

        for item in data['carrito']:
            cursor.execute(
                "INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario) VALUES (?, ?, ?, ?)",
                (venta_id, item['producto_id'], item['cantidad'], float(item['precio_unitario']))
            )
            cursor.execute(
                "UPDATE productos SET stock = stock - ? WHERE id = ?",
                (item['cantidad'], item['producto_id'])
            )

        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": f"Venta #{venta_id} registrada."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

# Código obligatorio para que funcione tanto local como en servidores como Render
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)