from flask import Flask, render_template, request, redirect, url_for, session, flash
import json, os

app = Flask(__name__)
app.secret_key = "distribuidora_gabys_2025"

BASE_DIR = os.path.join(os.path.dirname(__file__), "data")

# ------------------------------
# Funciones auxiliares
# ------------------------------

def cargar_json(nombre_archivo):
    ruta = os.path.join(BASE_DIR, nombre_archivo)
    if not os.path.exists(ruta):
        return []
    with open(ruta, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def guardar_json(nombre_archivo, data):
    ruta = os.path.join(BASE_DIR, nombre_archivo)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# ------------------------------
# Rutas principales
# ------------------------------

@app.route("/")
def index():
    if "usuario" in session:
        return redirect(url_for("menu"))
    return redirect(url_for("login"))

@app.route("/menu")
def menu():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("index.html", usuario=session["usuario"])

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuarios = cargar_json("usuarios.json")
        user = request.form["usuario"]
        pwd = request.form["password"]

        for u in usuarios:
            if u["usuario"] == user and u["password"] == pwd:
                session["usuario"] = user
                flash("Inicio de sesión exitoso", "success")
                # Redirige a /menu según lo que espera el test
                return redirect(url_for("menu"))

        # Mensaje exacto esperado por el test
        flash("Credenciales incorrectas", "danger")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    session.pop("carrito", None)
    flash("Has cerrado sesión correctamente", "info")
    return redirect(url_for("login"))

# ------------------------------
# Gestión de productos
# ------------------------------

@app.route("/productos")
def productos():
    if "usuario" not in session:
        return redirect(url_for("login"))
    productos = cargar_json("productos.json")

    query = request.args.get("q", "").strip().lower()
    tipo_filtro = request.args.get("tipo", "").strip().lower()
    if query or tipo_filtro:
        productos = [
            p for p in productos
            if (not query or query in p["nombre"].lower() or query in p["codigo"].lower())
            and (not tipo_filtro or p["tipo"].lower() == tipo_filtro)
        ]

    return render_template("productos.html", productos=productos)

@app.route("/productos/nuevo", methods=["GET", "POST"])
def nuevo_producto():
    if "usuario" not in session:
        return redirect(url_for("login"))

    tipos = ["aseo personal", "hogar", "otros"]

    if request.method == "POST":
        productos = cargar_json("productos.json")

        nuevo = {
            "nombre": request.form["nombre"],
            "codigo": request.form["codigo"],
            "cantidad": int(request.form["cantidad"]),
            "precio": float(request.form["precio"]),
            "tipo": request.form["tipo"]
        }

        if any(p["codigo"] == nuevo["codigo"] for p in productos):
            flash("Ya existe un producto con ese código.", "danger")
            return redirect(url_for("nuevo_producto"))

        productos.append(nuevo)
        guardar_json("productos.json", productos)
        flash("Producto agregado correctamente.", "success")
        return redirect(url_for("productos"))

    return render_template("nuevo_producto.html", tipos=tipos)

@app.route("/productos/editar/<codigo>", methods=["GET", "POST"])
def editar_producto(codigo):
    if "usuario" not in session:
        return redirect(url_for("login"))

    productos = cargar_json("productos.json")
    producto = next((p for p in productos if p["codigo"] == codigo), None)

    if not producto:
        flash("Producto no encontrado.", "danger")
        return redirect(url_for("productos"))

    tipos = ["aseo personal", "hogar", "otros"]

    if request.method == "POST":
        nuevo_codigo = request.form["codigo"]
        if nuevo_codigo != codigo and any(p["codigo"] == nuevo_codigo for p in productos):
            flash("Ya existe otro producto con ese código.", "danger")
            return redirect(url_for("editar_producto", codigo=codigo))

        producto["nombre"] = request.form["nombre"]
        producto["codigo"] = nuevo_codigo
        producto["cantidad"] = int(request.form["cantidad"])
        producto["precio"] = float(request.form["precio"])
        producto["tipo"] = request.form["tipo"]

        guardar_json("productos.json", productos)
        flash("Producto actualizado correctamente.", "success")
        return redirect(url_for("productos"))

    return render_template("editar_producto.html", producto=producto, tipos=tipos)

@app.route("/productos/eliminar/<codigo>", methods=["POST"])
def eliminar_producto(codigo):
    if "usuario" not in session:
        return redirect(url_for("login"))

    productos = cargar_json("productos.json")
    producto = next((p for p in productos if p["codigo"] == codigo), None)

    if not producto:
        flash("Producto no encontrado.", "danger")
    else:
        productos = [p for p in productos if p["codigo"] != codigo]
        guardar_json("productos.json", productos)
        flash(f"Producto '{producto['nombre']}' eliminado correctamente.", "success")

    return redirect(url_for("productos"))

# ------------------------------
# Flujo de productos (ventas, compras, devoluciones)
# ------------------------------

@app.route("/flujo")
def flujo_productos():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("flujo_menu.html")

@app.route("/flujo/<accion>", methods=["GET", "POST"])
def flujo_accion(accion):
    if "usuario" not in session:
        return redirect(url_for("login"))

    productos = cargar_json("productos.json")
    devoluciones = cargar_json("devoluciones.json")

    if "carrito" not in session:
        session["carrito"] = []

    carrito = session["carrito"]
    tipos = ["aseo personal", "hogar", "otros"]

    query = request.args.get("q", "").strip().lower()
    tipo_filtro = request.args.get("tipo", "").strip().lower()

    filtrados = [
        p for p in productos
        if (not query or query in p["nombre"].lower() or query in p["codigo"].lower())
        and (not tipo_filtro or p["tipo"].lower() == tipo_filtro)
    ]

    if request.method == "POST":
        if "finalizar" in request.form:
            if not carrito:
                flash("No hay productos en la lista para procesar.", "warning")
                return redirect(url_for("flujo_accion", accion=accion))

            total = 0
            for item in carrito:
                producto = next((p for p in productos if p["codigo"] == item["codigo"]), None)
                if not producto:
                    continue
                if accion == "venta":
                    if producto["cantidad"] < item["cantidad"]:
                        flash(f"Stock insuficiente para {producto['nombre']}.", "danger")
                        continue
                    producto["cantidad"] -= item["cantidad"]
                elif accion == "compra":
                    producto["cantidad"] += item["cantidad"]
                elif accion == "devolucion":
                    producto["cantidad"] += item["cantidad"]
                    devoluciones.append({
                        "nombre": producto["nombre"],
                        "codigo": producto["codigo"],
                        "cantidad": item["cantidad"],
                        "tipo": producto["tipo"],
                        "descripcion": item.get("descripcion", "")
                    })
                total += producto["precio"] * item["cantidad"]

            guardar_json("productos.json", productos)
            guardar_json("devoluciones.json", devoluciones)
            session["carrito"] = []
            flash(f"{accion.capitalize()} finalizada correctamente. Total ${total:.2f}", "success")
            return redirect(url_for("flujo_accion", accion=accion))

        elif "codigo" in request.form:
            codigo = request.form["codigo"]
            cantidad = int(request.form["cantidad"])
            producto = next((p for p in productos if p["codigo"] == codigo), None)
            if not producto:
                flash("Producto no encontrado.", "danger")
            else:
                if accion == "venta" and producto["cantidad"] < cantidad:
                    flash("Stock insuficiente para la venta.", "danger")
                else:
                    item = {
                        "nombre": producto["nombre"],
                        "codigo": producto["codigo"],
                        "cantidad": cantidad,
                        "precio": producto["precio"],
                        "tipo": producto["tipo"]
                    }
                    if accion == "devolucion":
                        item["descripcion"] = request.form.get("descripcion", "")
                    carrito.append(item)
                    session["carrito"] = carrito
                    flash(f"{producto['nombre']} agregado al listado.", "info")
            return redirect(url_for("flujo_accion", accion=accion))

    total = sum(i["precio"] * i["cantidad"] for i in carrito)
    return render_template("flujo_accion.html", accion=accion, productos=filtrados, tipos=tipos, carrito=carrito, total=total, query=query, tipo_filtro=tipo_filtro)

# ------------------------------
# Devoluciones
# ------------------------------

@app.route("/devoluciones", methods=["GET", "POST"])
def devoluciones():
    if "usuario" not in session:
        return redirect(url_for("login"))

    devoluciones = cargar_json("devoluciones.json")

    if request.method == "POST":
        if "eliminar_todas" in request.form:
            guardar_json("devoluciones.json", [])
            flash("Todas las devoluciones fueron eliminadas.", "info")
        elif "codigo" in request.form:
            codigo = request.form["codigo"]
            devoluciones = [d for d in devoluciones if d["codigo"] != codigo]
            guardar_json("devoluciones.json", devoluciones)
            flash("Devolución eliminada correctamente.", "success")
        return redirect(url_for("devoluciones"))

    return render_template("devoluciones.html", devoluciones=devoluciones)

# ------------------------------
# Otras secciones
# ------------------------------

@app.route("/alertas")
def alertas():
    if "usuario" not in session:
        return redirect(url_for("login"))
    alertas = cargar_json("alertas.json")
    return render_template("alertas.html", alertas=alertas)

@app.route("/reportes")
def reportes():
    if "usuario" not in session:
        return redirect(url_for("login"))

    productos = cargar_json("productos.json")
    alertas = cargar_json("alertas.json")
    ventas = cargar_json("ventas.json")
    compras = cargar_json("compras.json")
    devoluciones = cargar_json("devoluciones.json")

    total_productos = len(productos)
    total_unidades = sum(p["cantidad"] for p in productos) if productos else 0
    valor_inventario = sum(p["cantidad"] * p["precio"] for p in productos) if productos else 0

    total_alertas = len(alertas)
    por_tipo = {
        "aseo personal": len([p for p in productos if p["tipo"] == "aseo personal"]),
        "hogar": len([p for p in productos if p["tipo"] == "hogar"]),
        "otros": len([p for p in productos if p["tipo"] == "otros"])
    }

    ultimas_ventas = ventas[-5:] if ventas else []
    ultimas_compras = compras[-5:] if compras else []
    ultimas_devoluciones = devoluciones[-5:] if devoluciones else []

    return render_template(
        "reportes.html",
        total_productos=total_productos,
        total_unidades=total_unidades,
        valor_inventario=valor_inventario,
        total_alertas=total_alertas,
        por_tipo=por_tipo,
        ultimas_ventas=ultimas_ventas,
        ultimas_compras=ultimas_compras,
        ultimas_devoluciones=ultimas_devoluciones
    )

# ------------------------------
# Ejecutar aplicación
# ------------------------------

if __name__ == "__main__":
    app.run(debug=True)
