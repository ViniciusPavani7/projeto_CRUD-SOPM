from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Produto, Carrinho
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('main', __name__)


@bp.route('/')
def home():
    produtos = Produto.query.all()
    return render_template('home.html', produtos=produtos)


# Manda item para o carrinho


@bp.route('/adicionar-ao-carrinho/<int:produto_id>/', methods=['POST'])
@jwt_required()
def adicionar_ao_carrinho(produto_id):
    user_id = get_jwt_identity()
    produto = Produto.query.get_or_404(produto_id)

    # Verifica estoque
    if produto.stock <= 0:
        flash('Produto indisponível!', 'error')
        return redirect(url_for('main.home'))

    # Verifica se já existe no carrinho do usuário
    item_carrinho = Carrinho.query.filter_by(
        user_id=user_id,
        produto_id=produto.id_produto
    ).first()

    try:
        if item_carrinho:
            # Atualiza quantidade se já existir
            item_carrinho.qnt_itens += 1
        else:
            # Cria novo item no carrinho
            item_carrinho = Carrinho(
                user_id=user_id,
                produto_id=produto.id_produto,
                qnt_itens=1
            )
            db.session.add(item_carrinho)

        # Atualiza estoque
        produto.stock -= 1
        db.session.commit()

        flash('Produto adicionado ao carrinho!', 'success')

    except Exception as e:
        db.session.rollback()
        flash('Erro ao adicionar produto!', 'danger')

    return redirect(url_for('main.home'))
