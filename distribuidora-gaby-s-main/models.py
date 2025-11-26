from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Producto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    codigo = db.Column(db.String(30), unique=True, nullable=False)
    categoria = db.Column(db.String(50))
    stock = db.Column(db.Integer, default=0)
    precio = db.Column(db.Float)

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50))
    rol = db.Column(db.String(20), default="empleado")
