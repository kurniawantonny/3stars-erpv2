"""
ERP System - Flask Backend Application
Modular architecture inspired by Odoo
"""

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_mail import Mail

from config.settings import config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()
mail = Mail()


def create_app(config_name=None):
    """Application factory pattern"""
    
    if config_name is None:
        config_name = 'default'
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app


def register_blueprints(app):
    """Register all module blueprints"""
    
    from app.routes.auth import auth_bp
    from app.modules.admin.routes import admin_bp
    from app.modules.inventory.routes import inventory_bp
    from app.modules.purchase.routes import purchase_bp
    from app.modules.cash.routes import cash_bp
    from app.modules.ap.routes import ap_bp
    from app.modules.ar.routes import ar_bp
    from app.modules.production.routes import production_bp
    from app.modules.costing.routes import costing_bp
    from app.modules.accounting.routes import accounting_bp
    from app.modules.fixed_asset.routes import fixed_asset_bp
    
    # API version prefix
    api_prefix = '/api/v1'
    
    app.register_blueprint(auth_bp, url_prefix=f'{api_prefix}/auth')
    app.register_blueprint(admin_bp, url_prefix=f'{api_prefix}/admin')
    app.register_blueprint(inventory_bp, url_prefix=f'{api_prefix}/inventory')
    app.register_blueprint(purchase_bp, url_prefix=f'{api_prefix}/purchase')
    app.register_blueprint(cash_bp, url_prefix=f'{api_prefix}/cash')
    app.register_blueprint(ap_bp, url_prefix=f'{api_prefix}/ap')
    app.register_blueprint(ar_bp, url_prefix=f'{api_prefix}/ar')
    app.register_blueprint(production_bp, url_prefix=f'{api_prefix}/production')
    app.register_blueprint(costing_bp, url_prefix=f'{api_prefix}/costing')
    app.register_blueprint(accounting_bp, url_prefix=f'{api_prefix}/accounting')
    app.register_blueprint(fixed_asset_bp, url_prefix=f'{api_prefix}/fixed-assets')


def register_error_handlers(app):
    """Register global error handlers"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad Request', 'message': str(error)}), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized', 'message': 'Authentication required'}), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden', 'message': 'Access denied'}), 403
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not Found', 'message': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({'error': 'Internal Server Error', 'message': 'Something went wrong'}), 500
