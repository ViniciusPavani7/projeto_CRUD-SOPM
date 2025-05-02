from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from sqlalchemy import delete
from models import Produto, Pedido, Carrinho
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_login import login_required, current_user

bp = Blueprint('cart', __name__)


@bp.route('/carrinho')
@login_required
def ver_carrinho():
    user_id = current_user.id

    itens_carrinho = Carrinho.query.filter_by(user_id=user_id).options(
        db.joinedload(Carrinho.produto)
    ).all()

    total = sum(item.produto.price *
                item.qnt_itens for item in itens_carrinho)

    return render_template('carrinho.html',
                           carrinho=itens_carrinho,
                           total=total)


@bp.route('/finalizar-carrinho', methods=['POST'])
@jwt_required()
def finalizar_carrinho():
    user_id = get_jwt_identity()
    itens_carrinho = Carrinho.query.filter_by(user_id=user_id).all()

    if not itens_carrinho:
        flash('Seu carrinho está vazio!', 'error')
        return redirect(url_for('cart.ver_carrinho'))

    try:
        for item in itens_carrinho:
            pedido = Pedido(
                id_user=user_id,  #
                id_produto=item.produto_id,
                qnt_itens=item.qnt_itens,
                status='Novo'
            )
            db.session.add(pedido)

        # Limpa o carrinho (o estoque já foi reduzido antes)
        Carrinho.query.filter_by(user_id=user_id).delete()
        db.session.commit()

        flash('Compra finalizada com sucesso!', 'success')
        return redirect(url_for('orders.meus_pedidos'))

    except Exception as e:
        db.session.rollback()
        flash('Erro ao finalizar compra.', 'danger')
        return redirect(url_for('cart.ver_carrinho'))


@bp.route('/remover_do_carrinho/<int:produto_id>', methods=['POST'])
@jwt_required()
def remover_do_carrinho(produto_id):
    user_id = get_jwt_identity()

    item = Carrinho.query.filter_by(
        user_id=user_id,
        produto_id=produto_id
    ).first_or_404()

    # Devolve o estoque
    produto = Produto.query.get(produto_id)
    if produto:
        produto.stock += item.qnt_itens
        db.session.delete(item)
        db.session.commit()

    return redirect(url_for('cart.ver_carrinho'))


@bp.route('/atualizar_quantidade/<int:produto_id>', methods=['POST'])
@jwt_required()
def atualizar_quantidade(produto_id):
    user_id = get_jwt_identity()
    nova_quantidade = int(request.form.get('quantidade', 0))

    if nova_quantidade <= 0:
        flash('Quantidade inválida!', 'error')
        return redirect(url_for('cart.ver_carrinho'))

    # Busca o item no carrinho do BD
    item = Carrinho.query.filter_by(
        user_id=user_id,
        produto_id=produto_id
    ).first_or_404()

    produto = Produto.query.get(produto_id)
    if not produto:
        flash('Produto não encontrado!', 'error')
        return redirect(url_for('cart.ver_carrinho'))

    # Calcula diferença
    diferenca = nova_quantidade - item.qnt_itens

    # Verifica estoque
    if produto.stock < diferenca:
        flash('Estoque insuficiente!', 'error')
        return redirect(url_for('cart.ver_carrinho'))

    # Atualiza
    produto.stock -= diferenca
    item.qnt_itens = nova_quantidade
    db.session.commit()

    return redirect(url_for('cart.ver_carrinho'))
