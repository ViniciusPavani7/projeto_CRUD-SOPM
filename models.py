from extensions import db
from datetime import datetime
import pytz

class Produto(db.Model):
    __tablename__ = 'produtos'
    
    id_produto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    id_market = db.Column(db.String(50))
    
    pedidos = db.relationship('Pedido', backref='produto', lazy=True)

class Pedido(db.Model):
    __tablename__ = 'pedidos'
    
    id_pedido = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_produto = db.Column(db.Integer, db.ForeignKey('produtos.id_produto'), nullable=False)
    qnt_itens = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum('Novo', 'Processando', 'Enviado', 'Cancelado'), default='Novo') 