from flask import Flask
from flask import render_template, flash, request, redirect, url_for, request
import os
from werkzeug.utils import secure_filename
import pandas as pd
import json
import re

UPLOAD_FOLDER = 'analysis/static/uploads'
ALLOWED_EXTENSIONS = {'csv'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = b'_5#y2L"F4Q8z\n\xec]]/'

# function used for restirct the upload file types.
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# this route is used to upload file to the server.
@app.route('/uploadfile', methods=['POST'])
def upload():
    error = u'Invalid file format'
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            x = re.findall("^[a-zA-Z]", filename)
            if x:
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                try:
                    df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    if len(df) > 0:
                        return redirect(url_for('display_data',
                                        filename=filename))
                    else:
                        error = 'File must containe some records'
                except Exception as e:
                    error = 'Unable to read file.'
            else:
                error = 'Filename dont start with alphabet.' 
    flash(error, 'error')
    return redirect(url_for('index'))

# this route is used to disply graph between two dates
@app.route('/<filename>/displaygraph')
def display_graph(filename):
    df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    start_date = request.args.get('startdate')
    end_date = request.args.get('enddate')
    newdf = get_date_between(df, start_date, end_date)
    uni = newdf['ACCIDENT_DATE'].value_counts().rename_axis('days').reset_index(name='counts')
    uni = uni.sort_values(by='days')
    dates = uni['days']
    dates = dates.apply(lambda x: x.strftime('%Y-%m-%d'))
    dates = dates.tolist()
    counts = (uni['counts']/24).tolist()
    
    return render_template('dategraph.html', dates=dates, counts=counts, startdate=start_date, enddate=end_date)


@app.route('/<filename>')
def display_data(filename):
    df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return render_template('index.html', url_data="/"+filename+"/getdata",
        graph=f"/{filename}/displaygraph", columns=df.columns,
        alcohol_impact=url_for('alcohol_impact',filename=filename),
        speed_zone=url_for('speezone', filename=filename),
        )

@app.route('/<filename>/alcoholimpact')
def alcohol_impact(filename):
    alc_time = request.args.get('alcoholtime')
    selectedcolumn = request.args.get('selectedcolumn')
    selectedcolumn = 'LIGHT_CONDITION'
    if alc_time == None:
        alc_time = 'no'
        selectedcolumn = 'LIGHT_CONDITION'

    df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    df['ALCOHOLTIME'] = df['ALCOHOLTIME'].str.lower()
    df = df[df['ALCOHOLTIME'] == alc_time]
    no_alc = df[selectedcolumn].value_counts().rename_axis('trends').reset_index(name='counts')
    counts = no_alc['counts'].tolist()
    trends = no_alc['trends'].tolist()
    columns = df.columns
    return render_template('alcohol.html', trends=trends, counts=counts,
     columns=columns, filename=filename, alc_time=alc_time, selectedcolumn=selectedcolumn)

@app.route('/<filename>/speezone')
def speezone(filename):
    speedzone = 'SPEED_ZONE'
    year = 2015
    try:
        year = int(request.args.get('year'))
    except:
        pass
    selectedcolumn = 'ACCIDENT_DATE'

    df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    df['YEAR'] = pd.DatetimeIndex(df[selectedcolumn]).year
    
    years = df['YEAR'].unique()
    df = df[df['YEAR'] == year]

    no_alc = df[speedzone].value_counts().rename_axis('trends').reset_index(name='counts')
    counts = no_alc['counts'].tolist()
    trends = no_alc['trends'].tolist()
    
    return render_template('speedzone.html', trends=trends, counts=counts,
     years=years, filename=filename, year = year)

def get_date_between(df, start, end):
    df['ACCIDENT_DATE'] = pd.to_datetime(df['ACCIDENT_DATE'])
    mask = (df['ACCIDENT_DATE'] > start) & (df['ACCIDENT_DATE'] <= end)
    return df.loc[mask]

# This route will be used by the ajax to get data from csv file
@app.route('/<filename>/getdata')
def get_data(filename):
    count = 100
    start_date = request.args.get('startdate')
    end_date = request.args.get('enddate')

    draw = request.args.get('draw')
    start = request.args.get('start')
    search = request.args.get('search[value]')

    df = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    df = get_date_between(df, start_date, end_date)    

    if len(search) != 0:
        df = df[df['DCA_CODE'].str.contains(search, case=False)]

    start = int(start)
    end = start + count
    df['ACCIDENT_DATE'] = df['ACCIDENT_DATE'].apply(lambda x: x.strftime('%Y-%m-%d'))
    result = df[start:end].to_json(orient="split")

    parsed = json.loads(result)
    parsed['draw'] = draw
    parsed['recordsTotal'] = len(df)
    parsed['recordsFiltered'] = len(df)
    return parsed

@app.route('/')
def index():
    return render_template('upload.html')