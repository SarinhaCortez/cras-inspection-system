from flask import Flask, request, render_template, redirect, session, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime as dt
from app.models import db, User, Report

def init_routes(app):

    #browsing
    
    @app.route('/', methods=['POST', 'GET'])
    def home():
        if "user" not in session:
            return redirect(url_for('login'))
        return render_template('index.html', footer=render_footer())

    @app.route('/login', methods=['POST', 'GET'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            # Query the User model to find the user by username
            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password, password):
                # Set session variables
                session['token'] = 'dummy_access_token'  # Replace with actual access token logic
                session["user"] = username  # Replace with actual user object
                session["username"] = username
                return redirect(url_for('home'))
            else:
                # Handle invalid credentials
                error = "Invalid credentials"
                return render_template('login.html', error=error, footer=render_footer())

        return render_template('login.html', footer=render_footer())

    @app.route('/signup', methods=['POST', 'GET'])
    def signup():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            conf_pw = request.form.get('conf-pw')

            if not username or not password or not conf_pw:
                return "All fields are required", 400

            if password != conf_pw:
                return "Passwords do not match", 400

            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            # Check if the username already exists in the database
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                return "User already exists", 400

            # Create a new user and add to the database
            new_user = User(username=username, name=username, pic=None, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            # Set session variables
            session['username'] = username
            session['token'] = 'dummy_access_token'  # Replace with actual access token logic
            session["user"] = username  # Replace with actual user object

            return redirect(url_for('home'))

        return render_template('signup.html', footer=render_footer())
    
    
    @app.route('/profile')
    def profile():
        if "user" in session:
            user = session.get("user")
            access_token = session.get('token')
            role = session.get('role')
            username = session.get('username')
            reports = Report.query.filter_by(username=username).order_by(Report.name.desc()).all()
            return render_template('profile.html', user=user, token=access_token, role=role, username=username, reports=reports, footer=render_footer())
        else:
            return redirect(url_for("login"))

    @app.route("/logout")
    def logout():
        session.pop("username", None)
        session.pop("token", None)
        session.pop("role", None)
        session.pop("user", None)
        return redirect(url_for("login"))
    
    
    #template rendering
    
    
    def render_footer():
        return render_template('_footer.html')
    
    
    #model interaction
    
    @app.route('/predict', methods=['POST', 'GET'])
    def predict():
        try:
            if "user" not in session:
                return redirect(url_for('login'))

            if request.method == 'POST':
                image_files = request.files.getlist("file")
                #if image_files == []:
                    #return render_template('index.html', footer=render_footer())
                all_predictions = []

                for image in image_files:
                    if image.filename == '':
                        continue

                    filename = secure_filename(image.filename)
                    img_path = os.path.join(app.config['IMAGE_UPLOADS'], filename)
                    if not os.path.exists(app.config['IMAGE_UPLOADS']):
                        os.makedirs(app.config['IMAGE_UPLOADS'])
                    # Save the file
                    image.save(img_path)

                    # Read and send the image
                    with open(img_path, 'rb') as file_data:
                        res = requests.post("http://localhost:8083/predictions/detr", files={'data': file_data})
                        predictions = res.json()

                    if "error" in predictions:
                        prediction_text = f"Error in prediction: {predictions['error']}"
                    else:
                        #prediction_text = process_detr_prediction(predictions)

                        all_predictions.append({
                            'filename': filename,
                            'predictions': predictions
                        })

                    # Delete the image after processing
                    if os.path.exists(img_path):
                        os.remove(img_path)

                # Create a single XML file with sections for each image
                xml_filename = dt.now().strftime('%Y-%m-%d %H-%M-%S') + '.xml'
                xml_path = os.path.join(app.config['XML_OUTPUTS'], xml_filename)
                if not os.path.exists(app.config['XML_OUTPUTS']):
                    os.makedirs(app.config['XML_OUTPUTS'])
                create_xml_file(all_predictions, xml_path)

                if "user" in session:
                    username = session.get('user')
                    save_report_to_db(xml_filename, xml_path, username)
                else:
                    return redirect(url_for("login"))
                
                if os.path.exists(xml_path):
                    os.remove(xml_path)

                return profile()
            
        except FileNotFoundError as e:
            return 'An error occurred while processing the file', 500
        except Exception as e:
            return 'An unexpected error occurred', 500
        
    #report management

    @app.route('/report/<int:report_id>', methods=['GET'])
    def view_report(report_id):
        report = Report.query.get(report_id)
        
        if report is None:
            abort(404)  # Return a 404 error if the report is not found
        
        return render_template('report_detail.html', report=report)
    
    @app.route('/delete-reports', methods=['POST'])
    def delete_reports():
        report_ids = request.form.getlist('report_ids')  # Get list of report IDs from the form
        for report_id in report_ids:
            report = Report.query.get(report_id)
            if report:
                db.session.delete(report)
        db.session.commit()
        return redirect(url_for('profile'))

    

""" 
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
"""
#report creation

def create_xml_file(all_predictions, output_path):
    """
    Function to create a single XML file from a list of predictions for multiple images.
    """
    # Create the root element
    root = ET.Element("YourData")

    # Process each image's predictions
    for image_data in all_predictions:
        image_section = ET.SubElement(root, "Image")
        image_filename = ET.SubElement(image_section, "Filename")
        image_filename.text = image_data['filename']

        predictions = image_data['predictions']

        # Extract boxes, labels, and scores from prediction data
        boxes = predictions.get('boxes', [])
        labels = predictions.get('labels', [])
        scores = predictions.get('scores', [])

        # Collect predictions into a list of dictionaries
        sorted_predictions = []
        for i in range(len(boxes)):
            for j in range(len(boxes[i])):
                sorted_predictions.append({
                    'label': labels[i][j],
                    'score': scores[i][j],
                    'box': boxes[i][j]
                })

        # Sort the list by label
        sorted_predictions = sorted(sorted_predictions, key=lambda x: x['label'])

        # Create XML elements for each sorted prediction
        for pred in sorted_predictions:
            prediction_element = ET.SubElement(image_section, "Prediction")

            # Create elements for label, score, and box
            label_element = ET.SubElement(prediction_element, "Label")
            label_element.text = str(pred['label'])

            score_element = ET.SubElement(prediction_element, "Score")
            score_element.text = str(pred['score'])

            box_element = ET.SubElement(prediction_element, "Box")
            box_element.text = ",".join(map(str, pred['box']))  # Join list items as comma-separated string

    # Write the XML to a file
    tree = ET.ElementTree(root)
    tree.write(output_path, encoding='utf-8', xml_declaration=True)

    

def save_report_to_db(name, output_path, username):
    """
    Save the report entry to the database.
    """
    try:
        new_report = Report(
            name=name,
            content=output_path,
            username=username
        )
        db.session.add(new_report)
        db.session.commit()
        print("Report saved successfully.")
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred while saving the report: {e}")
