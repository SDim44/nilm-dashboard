import os
from datetime import datetime
from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from app import app

basedir = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(basedir,"static\\uploads")

ALLOWED_EXTENSIONS = {'csv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/appliance/<appliance_name>', methods=['GET', 'POST'])
def upload_file(appliance_name):
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = secure_filename(timestamp + "_" + appliance_name + ".csv") # der Dateiname wird jetzt auf appliance_name gesetzt
            file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
            return redirect(url_for('upload_file', appliance_name=appliance_name, filename=filename))
        
    # return '''
    # <!doctype html>
    # <title>Upload new .csv file</title>
    # <h1>Upload new .csv file</h1>
    # <form method=post enctype=multipart/form-data>
    #   <input type=file name=file>
    #   <input type=submit value=Upload>
    # </form>
    # '''