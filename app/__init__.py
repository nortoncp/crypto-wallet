from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from datetime import datetime
from app.services.scheduler_sinais import iniciar_agendador


db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    from app.auth.routes import auth_bp
    from app.portfolio.routes import portfolio_bp
    from app.dashboard.routes import dashboard_bp
    from app.estatisticas.routes import estatisticas_bp
    from app.mercado_futuro.routes import mercado_futuro_bp
    from app.mercado_spot.routes import mercado_spot_bp
    from app.calendario_economico.routes import calendario_economico_bp
    from app.grafico.routes import grafico_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(portfolio_bp, url_prefix='/portfolio')
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(estatisticas_bp)
    app.register_blueprint(mercado_futuro_bp)
    app.register_blueprint(mercado_spot_bp)
    app.register_blueprint(calendario_economico_bp)
    app.register_blueprint(grafico_bp)

    def timestamp_to_date(value):
        return datetime.fromtimestamp(value / 1000).strftime('%d/%m/%Y %H:%M')

    app.jinja_env.filters['timestamp_to_date'] = timestamp_to_date

    @app.template_filter('datetimeformat')
    def datetimeformat(value):
        try:
            return datetime.fromtimestamp(value / 1000).strftime('%d/%m/%Y %H:%M')
        except:
            return value

    iniciar_agendador()

    return app
