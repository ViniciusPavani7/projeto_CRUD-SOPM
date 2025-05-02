from flask import Flask, redirect, url_for
from dotenv import load_dotenv
import os
from urllib.parse import quote_plus
from extensions import db, migrate, bcrypt
from flask_jwt_extended import JWTManager
from flask_login import LoginManager

load_dotenv()


def create_app():
    app = Flask(__name__)

    # Configuração do banco de dados
    password = quote_plus(os.getenv('DB_PASSWORD', ''))
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{password}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # Configurações do Flask-JWT-Extended
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
    app.config['JWT_COOKIE_SECURE'] = False
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    jwt = JWTManager(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Registrar blueprints (área modificada)
    from routes.auth import bp as auth_bp
    from routes.main import bp as main_bp
    from routes.produtos import bp as products_bp
    from routes.carrinho import bp as cart_bp
    from routes.pedidos import bp as orders_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(products_bp, url_prefix='/produtos')
    app.register_blueprint(cart_bp, url_prefix='/carrinho')
    app.register_blueprint(orders_bp, url_prefix='/pedidos')

    @login_manager.user_loader
    def load_user(id_user):
        from models import Usuario
        return Usuario.query.get(int(id_user))

    @app.context_processor
    def inject_user():
        from flask_login import current_user
        return dict(current_user=current_user)

    @app.route('/')
    def index():
        return redirect(url_for('products.listar_produtos'))

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
