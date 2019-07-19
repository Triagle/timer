from flask import Flask
from timer.main import main
from timer.model import db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/test.db"  # CHANGE ME!!!
db.init_app(app)

app.register_blueprint(main, url_prefix="/")
