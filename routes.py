from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from extensions import db
from models import Produto, Pedido
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from flask import get_flashed_messages
import pytz

bp = Blueprint('main', __name__)

# Rota da Home
@bp.route('/')
def home():
    produtos = Produto.query.all()
    return render_template('home.html', produtos=produtos)

# Rota para adicionar ao carrinho
@bp.route('/adicionar-ao-carrinho/<int:id>/', methods=['POST'])
def adicionar_ao_carrinho(id):
    produto = Produto.query.get_or_404(id)
    
    if produto.stock <= 0:
        flash('Produto indisponível!', 'error')
        return redirect(url_for('main.home'))

    carrinho = session.get('carrinho', [])
    
    # Verifica se o produto já está no carrinho
    item_existente = next(
        (item for item in carrinho if item['id_produto'] == produto.id_produto),
        None
    )
    
    if item_existente:
        item_existente['qnt_itens'] += 1
    else:
        carrinho.append({
            'id_produto': produto.id_produto,
            'nome': produto.nome,
            'preco': float(produto.price),
            'qnt_itens': 1
        })
    
    # Diminui o estoque
    produto.stock -= 1
    db.session.commit()
    
    session['carrinho'] = carrinho
    flash('Produto adicionado ao carrinho!', 'success')
    return redirect(url_for('main.home'))

# Rota para ver o carrinho
@bp.route('/carrinho/')
def ver_carrinho():
    carrinho = session.get('carrinho', [])
    total = sum(item['preco'] * item['qnt_itens'] for item in carrinho)
    return render_template('carrinho.html', carrinho=carrinho, total=total)

# Rota para finalizar carrinho
@bp.route('/finalizar-carrinho', methods=['POST'])
def finalizar_carrinho():
    carrinho = session.get('carrinho', [])
    
    if not carrinho:
        flash('Seu carrinho está vazio!', 'error')
        return redirect(url_for('main.ver_carrinho'))
    
    # Cria os pedidos com status 'Novo'
    for item in carrinho:
        pedido = Pedido(
            id_produto=item['id_produto'],
            qnt_itens=item['qnt_itens'],
            status='Novo'
        )
        db.session.add(pedido)
    
    db.session.commit()
    session.pop('carrinho', None)  # Limpa o carrinho sem devolver ao estoque
    
    # Mensagem de agradecimento
    flash('Obrigado pela sua compra! Seus pedidos foram registrados com sucesso.', 'success')
    return redirect(url_for('main.ver_carrinho'))

# Rota para atualizar status do pedido
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
    return redirect(url_for('main.listar_pedidos'))

# Rotas para Produtos
@bp.route('/produtos/')
def listar_produtos():
    produtos = Produto.query.all()
    return render_template('produtos/listar.html', produtos=produtos)

@bp.route('/produtos/novo/', methods=['GET', 'POST'])
def novo_produto():
    if request.method == 'POST':
        try:
            produto = Produto(
                nome=request.form['nome'],
                descricao=request.form['descricao'],
                price=request.form['price'],
                stock=request.form['stock'],
                id_market=request.form['id_market']
            )
            db.session.add(produto)
            db.session.commit()
            flash('Produto criado com sucesso!', 'success')
            return redirect(url_for('main.listar_produtos'))
        except IntegrityError:
            db.session.rollback()
            produto_existente = Produto.query.filter_by(id_market=request.form['id_market']).first()
            flash(f'O ID Market que você inseriu já existe. Deseja apenas aumentar o estoque? (Produto existente: {produto_existente.nome})', 'warning')
            return redirect(url_for('main.listar_produtos', id_market=request.form['id_market']))
    return render_template('produtos/novo.html')

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
        return redirect(url_for('main.listar_produtos'))
    return render_template('produtos/editar.html', produto=produto)

@bp.route('/produtos/excluir/<int:id>/')
def excluir_produto(id):
    produto = Produto.query.get_or_404(id)
    produto.stock = 0
    db.session.commit()
    flash('Estoque do produto foi zerado com sucesso!', 'success')
    return redirect(url_for('main.listar_produtos'))

# Rotas para Pedidos
@bp.route('/pedidos')
def listar_pedidos():
    # Obtém os parâmetros de filtro
    ordenacao = request.args.get('ordenacao', 'recente')  # 'recente' ou 'antigo'
    data_filtro = request.args.get('data', '')  # formato: YYYY-MM-DD
    nome_filtro = request.args.get('nome', '').strip()
    id_filtro = request.args.get('id', '').strip()
    
    # Query base
    query = Pedido.query
    
    # Aplica filtro de data se fornecido
    if data_filtro:
        try:
            data = datetime.strptime(data_filtro, '%Y-%m-%d')
            query = query.filter(db.func.date(Pedido.date) == data.date())
        except ValueError:
            pass
    
    # Aplica ordenação
    if ordenacao == 'recente':
        query = query.order_by(Pedido.date.desc())
    else:
        query = query.order_by(Pedido.date.asc())
    
    pedidos = query.all()
    pedidos_com_produtos = []
    
    # Define o timezone de Brasília
    tz = pytz.timezone('America/Sao_Paulo')
    
    for pedido in pedidos:
        produto = Produto.query.get(pedido.id_produto)
        
        # Aplica filtros de nome e ID
        if nome_filtro and nome_filtro.lower() not in produto.nome.lower():
            continue
        if id_filtro and str(pedido.id_pedido) != id_filtro:
            continue
            
        # Converte a data para o timezone de Brasília
        data_brasilia = pedido.date.astimezone(tz)
        pedido_info = {
            'id_pedido': pedido.id_pedido,
            'produto': produto,
            'quantidade': pedido.qnt_itens,
            'status': pedido.status,
            'data': data_brasilia
        }
        pedidos_com_produtos.append(pedido_info)
    
    return render_template('pedidos/listar.html', 
                         pedidos=pedidos_com_produtos,
                         ordenacao_atual=ordenacao,
                         data_filtro=data_filtro,
                         nome_filtro=nome_filtro,
                         id_filtro=id_filtro)

@bp.route('/pedidos/novo/', methods=['GET', 'POST'])
def novo_pedido():
    if request.method == 'POST':
        pedido = Pedido(
            id_produto=request.form['id_produto'],
            qnt_itens=request.form['qnt_itens'],
            status=request.form['status']
        )
        db.session.add(pedido)
        db.session.commit()
        flash('Pedido criado com sucesso!', 'success')
        return redirect(url_for('main.listar_pedidos'))
    produtos = Produto.query.all()
    return render_template('pedidos/novo.html', produtos=produtos)

@bp.route('/pedidos/editar/<int:id>/', methods=['GET', 'POST'])
def editar_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    if request.method == 'POST':
        produto_id = request.form['produto']
        qnt_itens = int(request.form['qnt_itens'])
        status = request.form['status']
        
        # Se o produto foi alterado ou a quantidade mudou
        if pedido.id_produto != int(produto_id) or pedido.qnt_itens != qnt_itens:
            produto_antigo = Produto.query.get(pedido.id_produto)
            produto_novo = Produto.query.get(produto_id)
            
            # Se o produto foi alterado, devolve os itens ao estoque antigo
            if pedido.id_produto != int(produto_id):
                produto_antigo.stock += pedido.qnt_itens
            
            # Verifica se há estoque suficiente no novo produto
            if produto_novo.stock < qnt_itens:
                flash('Quantidade indisponível em estoque!', 'error')
                return redirect(url_for('main.editar_pedido', id=id))
            
            # Atualiza o estoque do novo produto
            produto_novo.stock -= qnt_itens
            
            pedido.id_produto = int(produto_id)
            pedido.qnt_itens = qnt_itens
        
        pedido.status = status
        db.session.commit()
        flash('Pedido atualizado com sucesso!', 'success')
        return redirect(url_for('main.listar_pedidos'))
    
    produtos = Produto.query.all()
    return render_template('pedidos/editar.html', pedido=pedido, produtos=produtos)

@bp.route('/pedidos/excluir/<int:id>/')
def excluir_pedido(id):
    pedido = Pedido.query.get_or_404(id)
    db.session.delete(pedido)
    db.session.commit()
    flash('Pedido excluído com sucesso!', 'success')
    return redirect(url_for('main.listar_pedidos'))

# Rota para remover do carrinho
@bp.route('/remover_do_carrinho/<int:produto_id>', methods=['POST'])
def remover_do_carrinho(produto_id):
    if 'carrinho' in session:
        carrinho = session['carrinho']
        # Encontra o item antes de removê-lo
        item_removido = next((item for item in carrinho if item['id_produto'] == produto_id), None)
        if item_removido:
            # Devolve o estoque
            produto = Produto.query.get(produto_id)
            if produto:
                produto.stock += item_removido['qnt_itens']
                db.session.commit()
        
        carrinho = [item for item in carrinho if item['id_produto'] != produto_id]
        session['carrinho'] = carrinho
    return redirect(url_for('main.ver_carrinho'))

# Rota para atualizar quantidade no carrinho
@bp.route('/atualizar_quantidade/<int:produto_id>', methods=['POST'])
def atualizar_quantidade(produto_id):
    nova_quantidade = int(request.form.get('quantidade', 0))
    if nova_quantidade <= 0:
        flash('Quantidade inválida!', 'error')
        return redirect(url_for('main.ver_carrinho'))

    if 'carrinho' in session:
        carrinho = session['carrinho']
        item = next((item for item in carrinho if item['id_produto'] == produto_id), None)
        produto = Produto.query.get(produto_id)
        
        if item and produto:
            # Calcula a diferença de quantidade
            diferenca = nova_quantidade - item['qnt_itens']
            
            # Verifica se há estoque suficiente
            if produto.stock - diferenca < 0:
                flash('Quantidade indisponível em estoque!', 'error')
                return redirect(url_for('main.ver_carrinho'))
            
            # Atualiza o estoque
            produto.stock -= diferenca
            db.session.commit()
            
            # Atualiza a quantidade no carrinho
            item['qnt_itens'] = nova_quantidade
            session['carrinho'] = carrinho
            
    return redirect(url_for('main.ver_carrinho'))

# Rota para limpar o carrinho
@bp.route('/limpar-carrinho', methods=['POST'])
def limpar_carrinho():
    if 'carrinho' in session:
        carrinho = session['carrinho']
        # Devolve todos os itens ao estoque
        for item in carrinho:
            produto = Produto.query.get(item['id_produto'])
            if produto:
                produto.stock += item['qnt_itens']
        db.session.commit()
        # Limpa o carrinho
        session.pop('carrinho', None)
    flash('Carrinho limpo com sucesso!', 'success')
    return redirect(url_for('main.ver_carrinho')) 