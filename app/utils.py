import os
import pandas as pd
import numpy as np
from datetime import datetime
from werkzeug.utils import secure_filename
from .deepmodels import return_seq2point, aggregate_seq

BASEDIR = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = {'csv'}
SAMPLE_PERIOD = 10
WINDOW_SIZE = 99
SUPPORTED_APPLIANCES = {
    "washingmachine":{
        "name":"Washing Machine",
        "seq2point_weights":"seq2point-temp-weights-washing_machine-epoch0.h5"},
    "fridge":{
        "name":"Fridge",
        "seq2point_weights":"seq2point-temp-weights-fridge-epoch0.h5"},
    "microwave":{
        "name":"Microwave",
        "seq2point_weights":"seq2point-temp-weights-microwave-epoch0.h5"},
    "kettle":{
        "name":"Kettle",
        "seq2point_weights":"seq2point-temp-weights-kettle-epoch0.h5"}
        }

def get_appliance_name(appliance):
    return SUPPORTED_APPLIANCES[appliance]['name']

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def get_energy_data(appliance):
    df = pd.read_csv(os.path.join(BASEDIR,"static","uploads","20230605-212139_prediction.csv"))
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.set_index('Date')
    hourly_sum = df[appliance].resample('H').sum()
    hourly_sum.index = hourly_sum.index.strftime('%Y-%m-%d %H:%M')

    labels = hourly_sum.index.to_list()
    values = hourly_sum.values.tolist()
    mean = round(hourly_sum.values.mean()/1000,2)
    bills = round(hourly_sum.values.sum()*0.008/12,2)

    return labels, values, mean, bills



#---------------------------------------------------
def normalise(df):
    """
    Normalises the values in df
    """
    mean = df.fillna(method='ffill').values.mean()
    std = df.fillna(method = 'ffill').values.std()
    return mean, std, (df.fillna(method='ffill').values-mean)/std

def predict_seq2seq(file_name):
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = secure_filename(timestamp + "_prediction" + ".csv")
    file_path = os.path.join(BASEDIR,"static","uploads",filename)

    data = pd.read_csv(file_name,header=None).rename(columns={0:'Date',1:'Aggregate'})
    data['Date'] = pd.to_datetime(data['Date'])
    data = data.set_index('Date')

    aggregate = data['Aggregate']
    mean_agg, std_agg, aggregate = normalise(aggregate)

    aggregate = np.pad(aggregate, (WINDOW_SIZE//2, WINDOW_SIZE//2 +1))
    aggregate = np.array([aggregate[i:i+WINDOW_SIZE] for i in range(len(aggregate)-WINDOW_SIZE)])
    aggregate = np.expand_dims(aggregate, axis=-1)


    model = return_seq2point()
    for appliance in SUPPORTED_APPLIANCES.keys():
        WEIGHTS_PATH = os.path.join(BASEDIR,"weights",SUPPORTED_APPLIANCES[appliance]['seq2point_weights'])
        model.load_weights(WEIGHTS_PATH)
        predict = model.predict(aggregate)

        data[appliance] = np.squeeze(predict)


    data.to_csv(file_path)

    return data


        
# def load_seq2seq_model(appliance):
#     model = return_seq2seq()
#     w_path = os.path.join(BASEDIR,"weights",SUPPORTED_APPLIANCES[appliance]['seq2seq_weights'])
#     model.load_weights(w_path)
#     return model
