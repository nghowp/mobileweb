import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app():
    # Lấy đường dẫn tuyệt đối của thư mục hiện tại
    base_dir = os.path.abspath(os.path.dirname(__file__))

    app = Flask(
        __name__,
        static_folder=os.path.join(base_dir, "static"),
        template_folder=os.path.join(base_dir, "templates"),
    )
    app.secret_key = "KSDHFKS^*^%^#$^%$kjhjkh"
    app.config.from_mapping(
        SECRET_KEY="nguyenhop1026",
        SQLALCHEMY_DATABASE_URI="mysql+pymysql://root:Nguyenhop12345%40@localhost/mobilesale?charset=utf8mb4",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        PAGE_SIZE=8,
    )
    db.init_app(app)
    # Import routes và đăng ký Blueprint
    from .routes import bp

    app.register_blueprint(bp)

    return app
