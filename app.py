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
