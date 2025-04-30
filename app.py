from flask import Flask, redirect, url_for
from dotenv import load_dotenv
import os
from extensions import db
from urllib.parse import quote_plus
from flask_wtf.csrf import CSRFProtect

# Carrega as variáveis de ambiente
load_dotenv()

def create_app():
    app = Flask(__name__)

    # Configuração do banco de dados
    password = quote_plus(os.getenv('DB_PASSWORD', ''))
    app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USER')}:{password}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'chave-secreta-padrao')

    # Inicializa as extensões
    db.init_app(app)
    csrf = CSRFProtect(app)

    # Registra o Blueprint
    from routes import bp
    app.register_blueprint(bp)

    # Rota raiz
    @app.route('/')
    def index():
        return redirect(url_for('main.listar_produtos'))

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True) 