import os
import pandas as pd
import numpy as np
import sqlite3
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

def get_energy_data(appliance,user_id,engine):

    query = f"""
        SELECT timestamp,{appliance}
        FROM powerconsumption 
        WHERE user_id = {user_id}
        """

    df = pd.read_sql_query(query, engine)

    if len(df) > 2:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        data = df[appliance]
        hourly_sum = data.resample('H').sum()
        hourly_sum.index = hourly_sum.index.strftime('%Y-%m-%d %H:%M')

        monthly_sum = data.resample('H').sum().resample('M').mean()  # Summieren auf Monatsbasis
        monthly_sum.index = monthly_sum.index.strftime('%Y-%m')

        yearly_sum = data.resample('H').sum().resample('Y').mean()
        yearly_sum.index = yearly_sum.index.strftime('%Y')

        labels = hourly_sum.index.to_list()
        values = hourly_sum.values.tolist()
        mean = round(monthly_sum.values.mean()/1000, 2)
        bills = round(yearly_sum.values.mean()*0.008, 2)

    else:
        labels=["no data"]
        values=[0]
        mean = 0
        bills = 0

    return labels, values, mean, bills

def get_dashboard_data(user_id,engine):

    query = f"""
        SELECT *
        FROM powerconsumption 
        WHERE user_id = {user_id}
        """

    df = pd.read_sql_query(query, engine)

    if len(df) > 2:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        data = df['aggregate']

        hourly_sum = data.resample('Y').sum()
        hourly_sum.index = hourly_sum.index.strftime('%b')

        monthly_sum = data.resample('H').sum().resample('M').mean()  # Summieren auf Monatsbasis
        monthly_sum.index = monthly_sum.index.strftime('%Y-%m')

        yearly_sum = data.resample('H').sum().resample('Y').mean()
        yearly_sum.index = yearly_sum.index.strftime('%Y')

        labels = hourly_sum.index.to_list()
        values = hourly_sum.values.tolist()
        mean = round(monthly_sum.values.mean()/1000, 2)
        bills = round(yearly_sum.values.mean()*0.008, 2)

        # df['other'] = df['aggregate'] - df[['washingmachine', 'fridge', 'microwave', 'kettle']].sum(axis=1) #.apply(lambda x:x[0]-(x[1]+x[2]+x[3]+x[4]))
        mean_values = df[['washingmachine', 'fridge', 'microwave', 'kettle']].mean()
        sum_mean = mean_values.sum()
        
        percentages = (mean_values / sum_mean) * 100
        pie_values = percentages.tolist()

        pie_labels = ['washingmachine', 'fridge', 'microwave', 'kettle']

    else:
        labels=["no data"]
        values=[0]
        mean = 0
        bills = 0

    return labels, values, mean, bills, pie_values, pie_labels



#---------------------------------------------------
def normalise(df):
    """
    Normalises the values in df
    """
    mean = df.fillna(method='ffill').values.mean()
    std = df.fillna(method = 'ffill').values.std()
    return mean, std, (df.fillna(method='ffill').values-mean)/std


def update_dataDB(df,engine,user_id):
    # vorhandene Daten auslesen
    df_existing = pd.read_sql_query('SELECT * from powerconsumption', con=engine)
    df_existing['timestamp'] = pd.to_datetime(df_existing['timestamp'])
    # angemeldeter Benutzer
    df_existing_update = df_existing[df_existing['user_id'] == user_id]
    # andere Benutzer
    df_existing_other = df_existing[df_existing['user_id'] != user_id]

    # Daten vom angemeldeten Benutzer zusammenführen -> neuen Daten haben Vorrang
    df_combined = pd.concat([df_existing_update, df]).drop_duplicates(subset='timestamp', keep='last')

    # andere Daten wieder hinzufügen
    df_combined = pd.concat([df_combined, df_existing_other])

    # Daten in der DB aktualisieren
    df_combined.to_sql('powerconsumption', con=engine, if_exists='replace', index=False)


def predict_seq2seq(read_csv, write_prediction,db_engine,user_id):

    data = pd.read_csv(read_csv,header=None).rename(columns={0:'timestamp',1:'aggregate'})
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data = data.set_index('timestamp')

    aggregate = data['aggregate']
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
        data[appliance]=data[appliance].apply(lambda x: 0 if x < 0 else x)
    
    data['user_id'] = user_id


    data.to_csv(write_prediction)
    update_dataDB(data.reset_index(),db_engine,user_id)

    return True