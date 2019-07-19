from flask import Flask
from timer.main import main
from timer.model import db
from timer.auth import auth, login_manager

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/test.db"  # CHANGE ME!!!
app.secret_key = "super secret string"
db.init_app(app)
login_manager.init_app(app)

app.register_blueprint(main, url_prefix="/")
app.register_blueprint(auth, url_prefix="/")
