from flask import Blueprint, request, render_template, redirect, session, url_for

bp = Blueprint('user', __name__)

@bp.route('/', methods=['POST', 'GET'])
def index():
    return render_template('index.html')

@bp.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        session['username'] = username
        session['token'] = 'dummy_access_token'  # Replace with actual access token logic
        session["user"] = username  # Replace with actual user object
        return redirect(url_for('profile'))

@bp.route('/profile')
def profile():
    if "user" in session:
        user = session.get("user")
        access_token = session.get('token')
        role = session.get('role')
        username = session.get('username')
        return render_template('profile.html', user=user, token=access_token, role=role, username=username)
    else:
        return redirect(url_for("login"))

@bp.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("token", None)
    session.pop("role", None)
    session.pop("user", None)
    return redirect(url_for("login"))



