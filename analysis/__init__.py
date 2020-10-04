from flask import Flask
from flask import render_template, flash, request, redirect, url_for, request
import os
from werkzeug.utils import secure_filename
import pandas as pd
import json

UPLOAD_FOLDER = 'analysis/static/uploads'
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/uploadfile', methods=['POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('display_data',
                                    filename=filename))


@app.route('/<filename>')
def display_data(filename):
    df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return render_template('index.html', url_data="/"+filename+"/getdata", columns=df.columns)

@app.route('/<filename>/getdata')
def get_data(filename):
    count = 100
    draw = request.args.get('draw')
    start = request.args.get('start')
    df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    
    
    
    print(f"----------------\n\n-------{start}-----\n\n-----------------\n")

    start = int(start)
    end = start + count
    result = df[start:end].to_json(orient="split")

    parsed = json.loads(result)
    parsed['draw'] = draw
    parsed['recordsTotal'] = len(df)
    parsed['recordsFiltered'] = len(df)
    return parsed

@app.route('/')
def index():
    return render_template('index.html')