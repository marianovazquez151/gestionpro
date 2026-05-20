import os
import psycopg2
import psycopg2.extras
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from datetime import date

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        email TEXT,
        tel TEXT,
        saldo NUMERIC DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS insumos (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        costo NUMERIC DEFAULT 0,
        stock NUMERIC DEFAULT 0,
        minimo NUMERIC DEFAULT 0,
        unidad TEXT DEFAULT 'unidad'
    );
    CREATE TABLE IF NOT EXISTS productos (
        id SERIAL PRIMARY KEY,
        nombre TEXT NOT NULL,
        precio NUMERIC DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS producto_componentes (
        id SERIAL PRIMARY KEY,
        producto_id INTEGER REFERENCES productos(id) ON DELETE CASCADE,
        insumo_id INTEGER REFERENCES insumos(id) ON DELETE CASCADE,
        qty NUMERIC DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS pedidos (
        id SERIAL PRIMARY KEY,
        cliente_id INTEGER REFERENCES clientes(id),
        fecha TEXT,
        estado TEXT DEFAULT 'pendiente',
        notas TEXT
    );
    CREATE TABLE IF NOT EXISTS pedido_items (
        id SERIAL PRIMARY KEY,
        pedido_id INTEGER REFERENCES pedidos(id) ON DELETE CASCADE,
        producto_id INTEGER,
        nombre TEXT,
        qty NUMERIC,
        precio NUMERIC,
        marcado INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS pagos (
        id SERIAL PRIMARY KEY,
        cliente_id INTEGER REFERENCES clientes(id),
        fecha TEXT,
        monto NUMERIC,
        metodo TEXT,
        nota TEXT
    );
    """)

    cur.execute("SELECT COUNT(*) FROM clientes")
    if cur.fetchone()[0] == 0:
        cur.execute("""
        INSERT INTO clientes (nombre, email, tel, saldo) VALUES
            ('Ferretería López', 'lopez@mail.com', '3412000001', -15000),
            ('Constructora Pérez', 'perez@mail.com', '3412000002', 0),
            ('Distribuidora Norte', 'norte@mail.com', '3412000003', -8500);
        INSERT INTO insumos (nombre, costo, stock, minimo, unidad) VALUES
            ('Madera (m²)', 1200, 45, 20, 'm²'),
            ('Tornillos (caja)', 150, 80, 50, 'caja'),
            ('Pintura (lt)', 800, 12, 15, 'lt'),
            ('Tela tapiz (m)', 600, 30, 10, 'm'),
            ('Tubo acero (m)', 950, 60, 30, 'm');
        INSERT INTO productos (nombre, precio) VALUES
            ('Mesa Estándar', 12000),
            ('Silla Oficina', 5500),
            ('Estante Metálico', 8000),
            ('Mesa Grande', 18000);
        INSERT INTO producto_componentes (producto_id, insumo_id, qty) VALUES
            (1,1,4),(1,2,8),(1,3,1),
            (2,1,2),(2,2,4),(2,4,1),
            (3,5,6),(3,3,2),
            (4,1,6),(4,2,12),(4,3,2);
        INSERT INTO pedidos (cliente_id, fecha, estado, notas) VALUES
            (1, '2026-05-15', 'confirmado', 'Urgente'),
            (2, '2026-05-18', 'en_proceso', ''),
            (3, '2026-05-20', 'pendiente', '');
        INSERT INTO pedido_items (pedido_id, producto_id, nombre, qty, precio) VALUES
            (1,1,'Mesa Estándar',2,12000),(1,2,'Silla Oficina',4,5500),
            (2,3,'Estante Metálico',3,8000),
            (3,1,'Mesa Estándar',1,12000);
        INSERT INTO pagos (cliente_id, fecha, monto, metodo, nota) VALUES
            (1,'2026-05-10',5000,'Transferencia','Pago parcial'),
            (3,'2026-05-12',2000,'Efectivo','');
        """)
    conn.commit()
    cur.close()
    conn.close()

def row_to_dict(row, cursor):
    cols = [desc[0] for desc in cursor.description]
    return dict(zip(cols, row))

def rows_to_list(rows, cursor):
    cols = [desc[0] for desc in cursor.description]
    return [dict(zip(cols, r)) for r in rows]

# ── CLIENTES ──
@app.route('/api/clientes', methods=['GET'])
def get_clientes():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM clientes ORDER BY nombre")
    result = rows_to_list(cur.fetchall(), cur)
    cur.close(); conn.close()
    return jsonify(result)

@app.route('/api/clientes', methods=['POST'])
def create_cliente():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO clientes (nombre, email, tel, saldo) VALUES (%s,%s,%s,0) RETURNING *",
                (d['nombre'], d.get('email',''), d.get('tel','')))
    row = row_to_dict(cur.fetchone(), cur)
    conn.commit(); cur.close(); conn.close()
    return jsonify(row), 201

@app.route('/api/clientes/<int:cid>', methods=['PUT'])
def update_cliente(cid):
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE clientes SET nombre=%s, email=%s, tel=%s WHERE id=%s",
                (d['nombre'], d.get('email',''), d.get('tel',''), cid))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'ok': True})

# ── INSUMOS ──
@app.route('/api/insumos', methods=['GET'])
def get_insumos():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM insumos ORDER BY nombre")
    result = rows_to_list(cur.fetchall(), cur)
    cur.close(); conn.close()
    return jsonify(result)

@app.route('/api/insumos', methods=['POST'])
def create_insumo():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO insumos (nombre, costo, stock, minimo, unidad) VALUES (%s,%s,%s,%s,%s) RETURNING *",
                (d['nombre'], d.get('costo',0), d.get('stock',0), d.get('minimo',0), d.get('unidad','unidad')))
    row = row_to_dict(cur.fetchone(), cur)
    conn.commit(); cur.close(); conn.close()
    return jsonify(row), 201

@app.route('/api/insumos/<int:iid>', methods=['PUT'])
def update_insumo(iid):
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE insumos SET nombre=%s, costo=%s, stock=%s, minimo=%s, unidad=%s WHERE id=%s",
                (d['nombre'], d.get('costo',0), d.get('stock',0), d.get('minimo',0), d.get('unidad','unidad'), iid))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'ok': True})

@app.route('/api/insumos/<int:iid>/ajuste', methods=['POST'])
def ajuste_stock(iid):
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE insumos SET stock = GREATEST(0, stock + %s) WHERE id=%s RETURNING stock",
                (d['cantidad'], iid))
    row = cur.fetchone()
    conn.commit(); cur.close(); conn.close()
    return jsonify({'stock': float(row[0]) if row else 0})

# ── PRODUCTOS ──
@app.route('/api/productos', methods=['GET'])
def get_productos():
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM productos ORDER BY nombre")
    prods = rows_to_list(cur.fetchall(), cur)
    for p in prods:
        cur.execute("""
            SELECT pc.insumo_id, pc.qty, i.nombre as insumo_nombre, i.unidad, i.costo
            FROM producto_componentes pc
            JOIN insumos i ON i.id = pc.insumo_id
            WHERE pc.producto_id = %s
        """, (p['id'],))
        p['componentes'] = rows_to_list(cur.fetchall(), cur)
    cur.close(); conn.close()
    return jsonify(prods)

@app.route('/api/productos', methods=['POST'])
def create_producto():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO productos (nombre, precio) VALUES (%s,%s) RETURNING id",
                (d['nombre'], d.get('precio',0)))
    pid = cur.fetchone()[0]
    for comp in d.get('componentes', []):
        cur.execute("INSERT INTO producto_componentes (producto_id, insumo_id, qty) VALUES (%s,%s,%s)",
                    (pid, comp['insumo_id'], comp['qty']))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'id': pid}), 201

@app.route('/api/productos/<int:pid>/precio', methods=['PUT'])
def update_precio(pid):
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE productos SET precio=%s WHERE id=%s", (d['precio'], pid))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'ok': True})

# ── PEDIDOS ──
@app.route('/api/pedidos', methods=['GET'])
def get_pedidos():
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        SELECT p.*, c.nombre as cliente_nombre
        FROM pedidos p JOIN clientes c ON c.id = p.cliente_id
        ORDER BY p.id DESC
    """)
    pedidos = rows_to_list(cur.fetchall(), cur)
    for ped in pedidos:
        cur.execute("SELECT * FROM pedido_items WHERE pedido_id = %s", (ped['id'],))
        ped['items'] = rows_to_list(cur.fetchall(), cur)
    cur.close(); conn.close()
    return jsonify(pedidos)

@app.route('/api/pedidos', methods=['POST'])
def create_pedido():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO pedidos (cliente_id, fecha, estado, notas) VALUES (%s,%s,'pendiente',%s) RETURNING id",
                (d['cliente_id'], d.get('fecha', str(date.today())), d.get('notas','')))
    pid = cur.fetchone()[0]
    for it in d.get('items', []):
        cur.execute("INSERT INTO pedido_items (pedido_id, producto_id, nombre, qty, precio) VALUES (%s,%s,%s,%s,%s)",
                    (pid, it['producto_id'], it['nombre'], it['qty'], it['precio']))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'id': pid}), 201

@app.route('/api/pedidos/<int:pid>/estado', methods=['PUT'])
def update_estado(pid):
    d = request.json
    nuevo = d['estado']
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM pedidos WHERE id=%s", (pid,))
    ped_row = cur.fetchone()
    if not ped_row:
        cur.close(); conn.close()
        return jsonify({'error': 'No encontrado'}), 404

    cur.execute("UPDATE pedidos SET estado=%s WHERE id=%s", (nuevo, pid))

    if nuevo == 'confirmado':
        cur.execute("SELECT qty, precio, producto_id FROM pedido_items WHERE pedido_id=%s", (pid,))
        items = cur.fetchall()
        total = sum(float(i[0]) * float(i[1]) for i in items)
        cliente_id = ped_row[1]
        cur.execute("UPDATE clientes SET saldo = saldo - %s WHERE id=%s", (total, cliente_id))
        for it in items:
            cur.execute("""
                SELECT insumo_id, qty FROM producto_componentes WHERE producto_id=%s
            """, (it[2],))
            comps = cur.fetchall()
            for comp in comps:
                cur.execute("UPDATE insumos SET stock = GREATEST(0, stock - %s) WHERE id=%s",
                            (float(comp[1]) * float(it[0]), comp[0]))

    conn.commit(); cur.close(); conn.close()
    return jsonify({'ok': True})

@app.route('/api/pedidos/<int:pid>/marcar_item', methods=['PUT'])
def marcar_item(pid):
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("UPDATE pedido_items SET marcado=%s WHERE id=%s AND pedido_id=%s",
                (1 if d['marcado'] else 0, d['item_id'], pid))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'ok': True})

# ── PAGOS ──
@app.route('/api/pagos', methods=['GET'])
def get_pagos():
    conn = get_db(); cur = conn.cursor()
    cur.execute("""
        SELECT pg.*, c.nombre as cliente_nombre
        FROM pagos pg JOIN clientes c ON c.id = pg.cliente_id
        ORDER BY pg.id DESC
    """)
    result = rows_to_list(cur.fetchall(), cur)
    cur.close(); conn.close()
    return jsonify(result)

@app.route('/api/pagos', methods=['POST'])
def create_pago():
    d = request.json
    conn = get_db(); cur = conn.cursor()
    cur.execute("INSERT INTO pagos (cliente_id, fecha, monto, metodo, nota) VALUES (%s,%s,%s,%s,%s)",
                (d['cliente_id'], str(date.today()), d['monto'], d.get('metodo','Efectivo'), d.get('nota','')))
    cur.execute("UPDATE clientes SET saldo = saldo + %s WHERE id=%s", (d['monto'], d['cliente_id']))
    conn.commit(); cur.close(); conn.close()
    return jsonify({'ok': True}), 201

# ── CUENTA CORRIENTE ──
@app.route('/api/clientes/<int:cid>/cc', methods=['GET'])
def get_cc(cid):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT * FROM clientes WHERE id=%s", (cid,))
    cl = row_to_dict(cur.fetchone(), cur)
    movs = []
    cur.execute("""
        SELECT p.id, p.fecha, SUM(pi.qty * pi.precio) as total
        FROM pedidos p
        JOIN pedido_items pi ON pi.pedido_id = p.id
        WHERE p.cliente_id=%s AND p.estado='confirmado'
        GROUP BY p.id ORDER BY p.fecha
    """, (cid,))
    for row in cur.fetchall():
        movs.append({'fecha': row[1], 'desc': f"Pedido #{row[0]}", 'debe': float(row[2]), 'haber': 0})
    cur.execute("SELECT * FROM pagos WHERE cliente_id=%s ORDER BY fecha", (cid,))
    for row in rows_to_list(cur.fetchall(), cur):
        movs.append({'fecha': row['fecha'], 'desc': f"Pago — {row['metodo']}", 'debe': 0, 'haber': float(row['monto'])})
    movs.sort(key=lambda x: x['fecha'])
    cur.close(); conn.close()
    return jsonify({'cliente': cl, 'movimientos': movs})

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
