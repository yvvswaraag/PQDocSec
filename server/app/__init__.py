from flask import Flask
from flask_cors import CORS
from .config import Config

def create_app():
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB
    app.config.from_object(Config)

    CORS(app)

    CORS(app, origins=["http://localhost:5173"])
    from .routes.file_routes import file_bp
    from .routes.health_routes import health_bp
    from app.routes.handshake_routes import handshake_bp
    from app.routes.control_routes import control_bp
    from app.routes.pqc_file_routes import file_pqc_bp
    from app.routes.pqc_handshake_routes import pqc_handshake_bp
    from app.routes.pqc_control_routes import pqc_control_bp
    
    app.register_blueprint(file_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(handshake_bp)
    app.register_blueprint(control_bp)
    app.register_blueprint(file_pqc_bp)
    app.register_blueprint(pqc_handshake_bp)
    app.register_blueprint(pqc_control_bp)

    return app
