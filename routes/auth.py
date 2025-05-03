from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, current_user, login_required, logout_user
from models import Usuario
from extensions import db, bcrypt
from flask_jwt_extended import unset_jwt_cookies, create_access_token, set_access_cookies

bp = Blueprint('auth', __name__)


@bp.route('/auth', methods=['GET', 'POST'])
def auth_unified():
    # Redireciona se já estiver autenticado
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    active_tab = 'login'
    form_data = {}

    if request.method == 'POST':
        is_login = 'login_submit' in request.form
        is_register = 'register_submit' in request.form

        # Processa LOGIN
        if is_login:
            nome = request.form.get('login_nome')
            senha = request.form.get('login_senha')
            usuario = Usuario.query.filter_by(nome=nome).first()

            if usuario and bcrypt.check_password_hash(usuario.senha_hash, senha):
                login_user(usuario)

                # Gera token JWT
                access_token = create_access_token(
                    identity=str(usuario.id),
                    additional_claims={'role': usuario.role.value}
                )

                # Configura resposta com cookies
                response = redirect(url_for('main.home'))
                set_access_cookies(response, access_token)

                return response

            else:
                flash('Credenciais inválidas', 'danger')
                active_tab = 'login'
                form_data = {'login_nome': nome}

        # Processa REGISTRO
        elif is_register:
            nome = request.form.get('register_nome')
            senha = request.form.get('register_senha')

            if Usuario.query.filter_by(nome=nome).first():
                flash('Nome já está em uso', 'danger')
                active_tab = 'register'
                form_data = {'register_nome': nome}
            else:
                novo_usuario = Usuario(nome=nome, role='user')
                novo_usuario.set_senha(senha)
                db.session.add(novo_usuario)
                db.session.commit()
                flash('Conta criada! Faça login', 'success')
                active_tab = 'login'

    return render_template('userAuth.html',
                           active_tab=active_tab,
                           form_data=form_data)


@bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    response = redirect(url_for('auth.auth_unified'))
    unset_jwt_cookies(response)
    return response
