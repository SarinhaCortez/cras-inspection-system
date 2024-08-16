import os
import requests
from flask import Blueprint, request, render_template, redirect, session, url_for
from werkzeug.utils import secure_filename
@bp.route('/predict', methods=['POST', 'GET'])
def predict():
    if request.method == 'POST':
        image = request.files["file"]
        if image.filename == '':
            print("Filename is invalid")
            return redirect(request.url)

        filename = secure_filename(image.filename)
        basedir = os.path.abspath(os.path.dirname(__file__))
        img_path = os.path.join(basedir, app.config['IMAGE_UPLOADS'], filename)
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


