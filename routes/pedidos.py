from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from models import Produto, Pedido, Usuario
from datetime import datetime
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_login import login_required, current_user

bp = Blueprint('orders', __name__)


@bp.route('/pedidos')
def listar_pedidos():
    # Obter parâmetros de filtro
    id_filtro = request.args.get('id', '')
    nome_filtro = request.args.get('nome', '')
    data_filtro = request.args.get('data', '')
    ordenacao = request.args.get('ordenacao', 'recente')
    status_filtro = request.args.get('status', '')
    id_usuario_filtro = request.args.get('id_usuario', '')

    # Construir a query base
    query = Pedido.query.join(Produto)

    # Aplicar filtros
    if id_filtro:
        query = query.filter(Pedido.id_pedido == id_filtro)
    if nome_filtro:
        query = query.filter(Produto.nome.ilike(f'%{nome_filtro}%'))
    if id_usuario_filtro:
        query = query.filter(Pedido.id_user == id_usuario_filtro)
    if data_filtro:
        data = datetime.strptime(data_filtro, '%Y-%m-%d')
        query = query.filter(db.func.date(Pedido.date) == data.date())
    if status_filtro:
        query = query.filter(Pedido.status == status_filtro)

    # Aplicar ordenação
    if ordenacao == 'antigo':
        query = query.order_by(Pedido.date.asc())
    else:  # recente é o padrão
        query = query.order_by(Pedido.date.desc())

    pedidos = query.all()
    return render_template('pedidos/listar.html',
                           pedidos=pedidos,
                           id_filtro=id_filtro,
                           nome_filtro=nome_filtro,
                           id_usuario_filtro=id_usuario_filtro,
                           data_filtro=data_filtro,
                           ordenacao_atual=ordenacao)


@bp.route('/pedidos/atualizar-status/<int:id>/', methods=['POST'])
def atualizar_status_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    novo_status = request.form.get('status')
    if novo_status in ['Novo', 'Processando', 'Enviado', 'Cancelado']:
        # Se o pedido foi cancelado, devolve os itens ao estoque
        if novo_status == 'Cancelado' and pedido.status != 'Cancelado':
            produto = Produto.query.get(pedido.id_produto)
            if produto:
                produto.stock += pedido.qnt_itens

        pedido.status = novo_status
        db.session.commit()
    return redirect(url_for('orders.listar_pedidos'))


# Pedidos do Cliente


@bp.route('/meus-pedidos')
@login_required
def meus_pedidos():
    # Obter parâmetros de filtro
    id_filtro = request.args.get('id', '')
    nome_filtro = request.args.get('nome', '')
    data_filtro = request.args.get('data', '')
    ordenacao = request.args.get('ordenacao', 'recente')
    status_filtro = request.args.get('status', '')

    # Construir a query base
    query = Pedido.query.join(Produto)

    # Aplicar filtros
    if id_filtro:
        query = query.filter(Pedido.id_pedido == id_filtro)
    if nome_filtro:
        query = query.filter(Produto.nome.ilike(f'%{nome_filtro}%'))
    if data_filtro:
        data = datetime.strptime(data_filtro, '%Y-%m-%d')
        query = query.filter(db.func.date(Pedido.date) == data.date())
    if status_filtro:
        query = query.filter(Pedido.status == status_filtro)

    # Aplicar ordenação
    if ordenacao == 'antigo':
        query = query.order_by(Pedido.date.asc())
    else:  # recente é o padrão
        query = query.order_by(Pedido.date.desc())

    pedidos = Pedido.query.filter_by(id_user=current_user.id).all()
    # Sempre envia pedidos_vazios como True/False
    return render_template('pedidos/meus_pedidos.html',
                           pedidos=pedidos,
                           pedidos_vazios=len(pedidos) == 0)
