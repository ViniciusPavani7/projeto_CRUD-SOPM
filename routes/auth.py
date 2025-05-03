from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_user, current_user, login_required, logout_user
from models import Usuario
from extensions import db, bcrypt
from flask_jwt_extended import unset_jwt_cookies, create_access_token, set_access_cookies

bp = Blueprint('auth', __name__)


@bp.route('/auth', methods=['GET', 'POST'])
def auth_unified():
    # Redireciona se já estiver logado
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    # Valores padrão
    active_tab = 'login'
    form_data = {}
    login_error = None
    register_error = None
    register_success = False

    if request.method == 'POST':
        # Processa LOGIN
        if 'login_submit' in request.form:
            nome = request.form.get('login_nome')
            senha = request.form.get('login_senha')
            usuario = Usuario.query.filter_by(nome=nome).first()

            if usuario and bcrypt.check_password_hash(usuario.senha_hash, senha):
                login_user(usuario)
                access_token = create_access_token(identity=str(usuario.id))
                response = redirect(url_for('main.home'))
                set_access_cookies(response, access_token)
                return response
            else:
                login_error = 'Credenciais inválidas'
                active_tab = 'login'
                form_data = {'login_nome': nome}

        # Processa REGISTRO
        elif 'register_submit' in request.form:
            nome = request.form.get('register_nome')
            senha = request.form.get('register_senha')
            confirmar_senha = request.form.get('register_confirmar_senha')

            if senha != confirmar_senha:
                register_error = 'As senhas não coincidem'
                active_tab = 'register'
            elif Usuario.query.filter_by(nome=nome).first():
                register_error = 'Nome já está em uso'
                active_tab = 'register'
            else:
                novo_usuario = Usuario(nome=nome, role='user')
                novo_usuario.set_senha(senha)
                db.session.add(novo_usuario)
                db.session.commit()
                register_success = True
                active_tab = 'login'

            form_data = {'register_nome': nome}

    # Renderiza o template com os estados controlados pelo Flask
    return render_template('userAuth.html',
                           login_active=active_tab == 'login',
                           register_active=active_tab == 'register',
                           form_data=form_data,
                           login_error=login_error,
                           register_error=register_error,
                           register_success=register_success)


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    response = redirect(url_for('auth.auth_unified'))
    unset_jwt_cookies(response)
    return response
