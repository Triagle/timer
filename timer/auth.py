from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, UserMixin
import bcrypt

auth = Blueprint("auth", __name__)
login_manager = LoginManager()
login_manager.login_view = "auth.login"
password = b"$2b$12$Mo.uZKd10LTHuQef8XpxMe3S66.vRIt.KU5htTwIVhs53lutIxQZi"


class User(UserMixin):
    def __init__(self):
        self.name = "me"
        self.id = "all"
        self.active = False

    def is_active(self):
        return self.active


@login_manager.user_loader
def load_user(userid):
    return User()


@auth.route("/login")
def login():
    return render_template("login.html")


def verify_password(attempt):
    return bcrypt.checkpw(attempt, password)


@auth.route("/verify", methods=["POST"])
def verify():
    if verify_password(request.form["password"].encode()):
        login_user(User())
        return redirect(url_for("main.index"))
    else:
        return redirect(url_for("auth.login"))
