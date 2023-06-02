import os
import pandas as pd
from datetime import datetime
from werkzeug.utils import secure_filename
# from .deepmodels import *

BASEDIR = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = {'csv'}
SUPPORTED_APPLIANCES = {
    "washingmachine":{
        "name":"Washing Machine",
        "seq2seq_weights":"seq2seq-temp-weights-washing_machine-epoch0.h5"},
    "fridge":{
        "name":"Fridge",
        "seq2seq_weights":"seq2seq-temp-weights-fridge-epoch0.h5"},
    "microwave":{
        "name":"Microwave",
        "seq2seq_weights":"seq2seq-temp-weights-microwave-epoch0.h5"},
    "kettle":{
        "name":"Kettle",
        "seq2seq_weights":"seq2seq-temp-weights-kettle-epoch0.h5"}
        }

def get_appliance_name(appliance):
    return SUPPORTED_APPLIANCES[appliance]['name']

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def get_energy_data(appliance):
    df = pd.read_csv(os.path.join(BASEDIR,"static","uploads","20230602-183306_washingmachine.csv"),sep=';')
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date')
    monthly_sum = df['Wh'].resample('M').sum()
    monthly_sum.index = monthly_sum.index.strftime('%b')

    labels = monthly_sum.index.to_list()
    values = monthly_sum.values.tolist()
    mean = round(monthly_sum.values.mean()/1000,2)
    bills = round(monthly_sum.values.sum()*0.008/12,2)

    return labels, values, mean, bills

    

# def predict_seq2seq(appliance):
#     model = load_seq2seq_model(appliance)
#     data = pd.read_csv(os.path.join(BASEDIR,"static","uploads","20230602-183306_washingmachine.csv"))
#     prediction_raw = model.predict(data)
#     prediction = aggregate_seq(prediction_raw)


        
# def load_seq2seq_model(appliance):
#     model = return_seq2seq()
#     w_path = os.path.join(BASEDIR,"weights",SUPPORTED_APPLIANCES[appliance]['seq2seq_weights'])
#     model.load_weights(w_path)
#     return model
