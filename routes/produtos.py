from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from models import Produto, Usuario
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from flask import get_flashed_messages
from flask_jwt_extended import jwt_required, get_jwt_identity

bp = Blueprint('products', __name__)


@bp.route('/produtos/')
def listar_produtos():
    # Obtém os parâmetros de filtro
    id_produto = request.args.get('id_produto', '').strip()
    nome = request.args.get('nome', '').strip()
    id_market = request.args.get('id_market', '').strip()
    ordem_preco = request.args.get('ordem_preco', '')
    ordem_estoque = request.args.get('ordem_estoque', '')

    # Query base
    query = Produto.query

    # Aplica filtros
    if id_produto:
        query = query.filter(Produto.id_produto == id_produto)
    if nome:
        query = query.filter(Produto.nome.ilike(f'%{nome}%'))
    if id_market:
        query = query.filter(Produto.id_market.ilike(f'%{id_market}%'))

    # Aplica ordenação
    if ordem_preco == 'maior':
        query = query.order_by(Produto.price.desc())
    elif ordem_preco == 'menor':
        query = query.order_by(Produto.price.asc())
    elif ordem_estoque == 'maior':
        query = query.order_by(Produto.stock.desc())
    elif ordem_estoque == 'menor':
        query = query.order_by(Produto.stock.asc())

    produtos = query.all()
    return render_template('produtos/listar.html', produtos=produtos)


@bp.route('/produtos/novo/', methods=['GET', 'POST'])
def novo_produto():
    if request.method == 'POST':
        id_market = request.form['id_market']
        produto_existente = Produto.query.filter_by(
            id_market=id_market).first()

        # Se o ID Market já existe, mostra opções
        if produto_existente:
            flash(
                f'O ID Market "{id_market}" já está em uso pelo produto "{produto_existente.nome}". '
                'Escolha uma opção abaixo:',
                'warning'
            )
            return render_template(
                'produtos/novo.html',
                produto_existente=produto_existente,
                form_data=request.form  # Mantém os dados do formulário
            )

        # Se não existe, cria o produto
        try:
            produto = Produto(
                nome=request.form['nome'],
                descricao=request.form['descricao'],
                price=request.form['price'],
                stock=request.form['stock'],
                id_market=id_market
            )
            db.session.add(produto)
            db.session.commit()
            flash('Produto criado com sucesso!', 'success')
            return redirect(url_for('products.listar_produtos'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar produto: {str(e)}', 'danger')

    return render_template('produtos/novo.html')


@bp.route('/produtos/adicionar-estoque', methods=['POST'])
def adicionar_estoque():
    produto = Produto.query.get_or_404(request.form['id_produto'])
    produto.stock += int(request.form['quantidade'])
    db.session.commit()
    flash(
        f'Estoque de {produto.nome} atualizado! Total: {produto.stock} unidades',
        'success'
    )
    return redirect(url_for('products.listar_produtos'))


@bp.route('/produtos/editar/<int:id>/', methods=['GET', 'POST'])
def editar_produto(id):
    produto = Produto.query.get_or_404(id)
    if request.method == 'POST':
        produto.nome = request.form['nome']
        produto.descricao = request.form['descricao']
        produto.price = request.form['price']
        produto.stock = request.form['stock']
        produto.id_market = request.form['id_market']
        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('products.listar_produtos'))
    return render_template('produtos/editar.html', produto=produto)


@bp.route('/produtos/excluir/<int:id>/')
def excluir_produto(id):
    produto = Produto.query.get_or_404(id)
    produto.stock = 0
    db.session.commit()
    flash('Estoque do produto foi zerado com sucesso!', 'success')
    return redirect(url_for('products.listar_produtos'))
