from flask import Response, make_response, jsonify, request, render_template, redirect, session, url_for
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime as dt
from app.models import db, User, Report
import pdfkit

from lxml import etree


def init_routes(app):

    #browsing
    
    @app.route('/', methods=['POST', 'GET'])
    def home():
        if "user" not in session:
            return redirect(url_for('login'))
        user = User.query.filter_by(username=session["user"]).first()
        return render_template('index.html', user=user, footer=render_footer())

    @app.route('/login', methods=['POST', 'GET'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            user = User.query.filter_by(username=username).first()

            if user and check_password_hash(user.password, password):
                session['user'] = username  
                session['token'] = 'dummy_access_token'  
                return redirect(url_for('home'))
            else:
                error = "Invalid credentials"
                return render_template('login.html', error=error, footer=render_footer())

        return render_template('login.html', footer=render_footer())

    @app.route('/signup', methods=['POST', 'GET'])
    def signup():
        if request.method == 'POST':
            username = request.form.get('username')
            full_name = request.form.get('full-name')
            password = request.form.get('password')
            conf_pw = request.form.get('conf-pw')

            if not username or not password or not conf_pw:
                return "All fields are required", 400

            if password != conf_pw:
                return "Passwords do not match", 400

            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                return "User already exists", 400

            new_user = User(username=username, name=full_name, pic=None, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            session['user'] = username  
            session['token'] = 'dummy_access_token' 
            return redirect(url_for('home'))

        return render_template('signup.html', footer=render_footer())

    
    @app.route('/profile')
    def profile():
        if "user" in session:
            user = User.query.filter_by(username=session["user"]).first()
            access_token = session.get('token')
            reports = Report.query.filter_by(username=session["user"]).order_by(Report.name.desc()).all()
            return render_template('profile.html', user=user, token=access_token, reports=reports, footer=render_footer())
        else:
            return redirect(url_for("login"))
        
    @app.route('/change_profile_pic', methods=['POST'])
    def change_profile_pic():
        
        if 'user' not in session:
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=session["user"]).first()

        if 'profile_pic' not in request.files:
            return profile()
        

        file = request.files['profile_pic']
        if file.filename == '':
            return  profile()

        if file:
            
            filename = secure_filename(file.filename)
    
            rel_path = os.path.join('uploads', filename)
            
            abs_path = os.path.join(app.config['UPLOAD_PICS'], filename)
            if not os.path.exists(app.config['UPLOAD_PICS']):
                os.makedirs(app.config['UPLOAD_PICS'])
            file.save(abs_path)

            user.pic = rel_path
            db.session.commit()

            user.pic = f'static/uploads/profile_pics/{filename}'
            db.session.commit()

            return redirect(url_for('profile'))

        return "File upload failed", 400


    @app.route('/delete_profile_pic', methods=['POST'])
    def delete_profile_pic():
        username = session["user"]
        if not username:
            return login()

        user = User.query.filter_by(username=username).first()
        if user and user.pic:
            pic_path = os.path.join(os.getcwd(),'app', user.pic)
            if os.path.exists(pic_path):
                os.remove(pic_path)

            user.pic = None
            db.session.commit()

        elif not user:
            return login()
        

        return profile()
    
    @app.route('/delete_account', methods=['POST'])
    def delete_account():
        if 'user' not in session:
            return redirect(url_for('login'))

        username = session.get('user')
        user = User.query.get(username)
        if not user:
            return logout()

        try:
            db.session.delete(user)
            db.session.commit()
            session.clear()
            return logout()
        except Exception as e:
            return f"An error occurred: {e}", 500

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
                
                all_predictions = []

                multifile = request.files.getlist("multifile")
                folder = request.files.getlist("folder")
                
                file_input = multifile + folder

                #filter_duplicates = []
                
                for image in file_input:
                    
                    if image.filename == '':
                        continue
                    
                    filename = secure_filename(image.filename)
                    img_path = os.path.join(app.config['SAMPLE_UPLOADS'], filename)
                    if not os.path.exists(app.config['SAMPLE_UPLOADS']):
                        os.makedirs(app.config['SAMPLE_UPLOADS'])

                    image.save(img_path)

                    with open(img_path, 'rb') as file_data:
                        res = requests.post("http://localhost:8083/predictions/detr", files={'data': file_data})
                        predictions = res.json()
                        
                    if os.path.exists(img_path):
                        os.remove(img_path)

                    if "error" in predictions:
                        return f"Error in prediction: {predictions['error']}"
                    else:
                        all_predictions.append({
                            'filename': filename,
                            'predictions': predictions
                        })
                        
                    

                filename = dt.now().strftime('%Y-%m-%d %H:%M:%S')
                xml_path = os.path.join(app.config['XML_OUTPUTS'], filename + '.xml')

                
                if not os.path.exists(app.config['XML_OUTPUTS']):
                    os.makedirs(app.config['XML_OUTPUTS'])
                app.logger.info(f"Output directory: {app.config['XML_OUTPUTS']}")
              
                try:
                    create_xml_file(all_predictions, xml_path, filename)
                except Exception as e:
                    print(f"Error creating XML file: {e}")

                if "user" in session:
                    username = session.get('user')
                    save_report_to_db(filename, xml_path, username)
                else:
                    return redirect(url_for("login"))
                
                return jsonify({'redirect': url_for('profile')}), 200
            
        except FileNotFoundError as e:
            return 'An error occurred while processing the file', 500
        except Exception as e:
            return 'An unexpected error occurred', 500
        
    #report management

    @app.route('/report_detail/<int:report_id>', methods=['GET'])
    def report_detail(report_id):
        html_str = transform_xml_to_html(report_id)
        return Response(html_str, content_type='text/html')
    
    @app.route('/generate_pdf/<int:report_id>', methods=['GET'])
    def generate_pdf(report_id):
        
        report = Report.query.get(report_id)

        html_str = transform_xml_to_html(report_id)

        pdf = pdfkit.from_string(html_str, False)

        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={report.name}.pdf'

        return response
    
        
    @app.route('/delete-reports', methods=['POST'])
    def delete_reports():
        report_ids = request.form.getlist('report_ids')   
        for report_id in report_ids:
            report = Report.query.get(report_id)
            if report:
                db.session.delete(report)
                abs_path = os.path.join(app.config['XML_OUTPUTS'], report.name)
                if os.path.exists(abs_path):
                    os.remove(abs_path)
        db.session.commit()
        return redirect(url_for('profile'))
    
    import xml.etree.ElementTree as ET

def create_xml_file(all_predictions, output_path, filename):
    """
    Function to create a single XML file from a list of predictions for multiple images.
    """
    root = ET.Element("YourReport")
    date = ET.SubElement(root, "Date") 
    date.text = filename[:10]
    time = ET.SubElement(root, "Time")
    time.text = filename[11:]

    label_desc = {0:"Vertex Generator; Missing Teeth",1:"Leading Edge; Erosion",  2:"Lightning Receptor; Damage", 3:"Leading Edge;Crack",4:"Surface; Paint-Off"}

    for image_data in all_predictions:
        image_section = ET.SubElement(root, "Image")
        image_filename = ET.SubElement(image_section, "Filename")

        image_filename.text = image_data.get('filename', '')
        predictions = image_data.get('predictions', {})

        boxes = predictions.get('boxes', [])
        labels = predictions.get('labels', [])
        scores = predictions.get('scores', [])

        predictions = []
        for i in range(len(boxes)):
            if i < len(labels) and i < len(scores):  
                for j in range(len(boxes[i])):
                    if j < len(labels[i]) and j < len(scores[i]):
                       if(filter(scores[i][j], boxes[i][j][2], boxes[i][j][3])):
                        predictions.append({
                            'label': label_desc[labels[i][j]],
                            'score': round(scores[i][j],3),
                            'box': [round(i, 2) for i in boxes[i][j]]
                        })
                       

        for pred in predictions:
            prediction_element = ET.SubElement(image_section, "Prediction")

            label_element = ET.SubElement(prediction_element, "Label")
            label_element.text = str(pred['label'])

            score_element = ET.SubElement(prediction_element, "Score")
            score_element.text = str(pred['score'])

            box_element = ET.SubElement(prediction_element, "Box")
            box_element.text = ",".join(map(str, pred['box']))  
            
            
 
    try:

        xml_str = ET.tostring(root, encoding='unicode')

        xml_declaration = '<?xml version="1.0" encoding="utf-8"?>\n'
        xsl_link =  '<?xml-stylesheet type="text/xsl" href="../transform.xsl"?>\n'
        full_xml_str = xml_declaration + xsl_link + xml_str

        with open(output_path, 'w', encoding='utf-8-sig') as f:
            f.write(full_xml_str)

        print(f"XML file successfully created at {output_path}")

    except Exception as e:
        print(f"Failed to write XML file: {e}")

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


def save_report_to_db(name, output_path, username):
    """
    Save the report entry to the database.
    """
    rel_path = "app/static/xmls/" + name + '.xml'
    try:
        new_report = Report(
            name=name,
            content=rel_path,
            username=username
        )
        db.session.add(new_report)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred while saving the report: {e}")

def filter(score, bbox_width, bbox_height):
    return ((bbox_width < 0.50) and (bbox_height < 0.5) and (score >= 0.25))

def transform_xml_to_html(report_id):
    report = Report.query.get(report_id)

    xml_file = report.content
    xslt_file = 'app/static/transform.xsl'

    xml_tree = etree.parse(xml_file)
    xslt_tree = etree.parse(xslt_file)

    transform = etree.XSLT(xslt_tree)
    result_html = transform(xml_tree)

    return str(result_html)