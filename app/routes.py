from flask import Flask, request, render_template, redirect, session, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests

def init_routes(app):
    
    users = {}  
    
    @app.route('/', methods=['POST', 'GET'])
    def home():
        if "user" not in session:
            return redirect(url_for('login'))
        return render_template('index.html')

    @app.route('/login', methods=['POST', 'GET'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            user = users.get(username)
            if user and check_password_hash(user['password'], password):
                session['username'] = username
                session['token'] = 'dummy_access_token'  # Replace with actual access token logic
                session["user"] = username  # Replace with actual user object
                return redirect(url_for('home'))
            else:
                return "Invalid credentials", 401
        return render_template('login.html')

    @app.route('/signup', methods=['POST', 'GET'])
    def signup():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            if username in users:
                return "User already exists", 400
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
            users[username] = {'password': hashed_password}
            session['username'] = username
            session['token'] = 'dummy_access_token'  # Replace with actual access token logic
            session["user"] = username  # Replace with actual user object
            return redirect(url_for('home'))
        return render_template('signup.html')

    @app.route('/profile')
    def profile():
        if "user" in session:
            user = session.get("user")
            access_token = session.get('token')
            role = session.get('role')
            username = session.get('username')
            return render_template('profile.html', user=user, token=access_token, role=role, username=username)
        else:
            return redirect(url_for("login"))

    @app.route("/logout")
    def logout():
        session.pop("username", None)
        session.pop("token", None)
        session.pop("role", None)
        session.pop("user", None)
        return redirect(url_for("login"))

    @app.route('/predict', methods=['POST', 'GET'])
    def predict():
        if "user" not in session:
            return redirect(url_for('login'))

        if request.method == 'POST':
            image = request.files["file"]
            if image.filename == '':
                return redirect(request.url)

            filename = secure_filename(image.filename)
            img_path = os.path.join(app.config['IMAGE_UPLOADS'], filename)
            image.save(img_path)

            res = requests.post("http://localhost:8083/predictions/detr", files={'data': open(img_path, 'rb')})
            prediction = res.json()

            if "error" in prediction:
                prediction_text = f"Error in prediction: {prediction['error']}"
            else:
                prediction_text = process_detr_prediction(prediction)

            return render_template('index.html', prediction_text=prediction_text)

    def process_detr_prediction(prediction):
        results = []
        boxes = prediction.get('boxes', [])
        labels = prediction.get('labels', [])
        scores = prediction.get('scores', [])

        for i in range(len(boxes)):
            for j in range(len(boxes[i])):
                bbox = boxes[i][j]
                label = labels[i][j]
                score = scores[i][j]
                results.append(f"Label: {label}, Score: {score}, BBox: {bbox}")

        return " | ".join(results)


