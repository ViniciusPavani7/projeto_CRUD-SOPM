from extensions import db, bcrypt
from datetime import datetime
from enum import Enum
from flask_login import UserMixin


class Produto(db.Model):
    __tablename__ = 'produtos'

    id_produto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    id_market = db.Column(db.String(50), unique=True)

    pedidos = db.relationship('Pedido', backref='produto', lazy=True)


class Pedido(db.Model):
    __tablename__ = 'pedidos'

    id_pedido = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_user = db.Column(db.Integer, db.ForeignKey(
        'users.id'), nullable=False)
    id_produto = db.Column(db.Integer, db.ForeignKey(
        'produtos.id_produto'), nullable=False)
    qnt_itens = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.Enum('Novo', 'Processando',
                       'Enviado', 'Cancelado'), default='Novo')


class roleEnum(str, Enum):
    USER = 'user'
    ADMIN = 'admin'


class Usuario(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nome = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(roleEnum), default=roleEnum.USER, nullable=False)
    senha_hash = db.Column(db.String(60), nullable=False)

    carrinhos = db.relationship('Carrinho', backref='usuario', lazy='dynamic')

    def set_senha(self, senha):
        self.senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')

    def check_senha(self, senha):
        return bcrypt.check_password_hash(self.senha_hash, senha)


class Carrinho(db.Model):
    __tablename__ = 'carrinho'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey(
        'users.id'), nullable=False, index=True)
    produto_id = db.Column(db.Integer, db.ForeignKey(
        'produtos.id_produto'), nullable=False)
    qnt_itens = db.Column(db.Integer, default=1, nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    produto = db.relationship('Produto')
    __table_args__ = (
        db.UniqueConstraint('user_id', 'produto_id',
                            name='uq_user_produto_carrinho'),
    )
