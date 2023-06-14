import os
import pandas as pd
import numpy as np
import sqlite3
from sqlalchemy import create_engine
from datetime import datetime,timedelta
from werkzeug.utils import secure_filename
from .deepmodels import return_seq2point, aggregate_seq, return_seq2seq, return_dae

BASEDIR = os.path.abspath(os.path.dirname(__file__))
ALLOWED_EXTENSIONS = {'csv'}
SAMPLE_PERIOD = 10
WINDOW_SIZE = 99
SUPPORTED_APPLIANCES = {
    "washingmachine":{
        "name":"Washing Machine",
        "seq2point_weights":"seq2point-temp-weights-washing_machine-epoch0.h5",
        "seq2seq_weights":"seq2seq-temp-weights-washing_machine-epoch0.h5",
        "dae_weights":"dae-temp-weights-washing_machine-epoch0.h5"},
    "fridge":{
        "name":"Fridge",
        "seq2point_weights":"seq2point-temp-weights-fridge-epoch0.h5",
        "seq2seq_weights":"seq2seq-temp-weights-fridge-epoch0.h5",
        "dae_weights":"dae-temp-weights-fridge-epoch0.h5"},
    "microwave":{
        "name":"Microwave",
        "seq2point_weights":"seq2point-temp-weights-microwave-epoch0.h5",
        "seq2seq_weights":"seq2seq-temp-weights-microwave-epoch0.h5",
        "dae_weights":"dae-temp-weights-microwave-epoch0.h5"},
    "kettle":{
        "name":"Kettle",
        "seq2point_weights":"seq2point-temp-weights-kettle-epoch0.h5",
        "seq2seq_weights":"seq2seq-temp-weights-kettle-epoch0.h5",
        "dae_weights":"dae-temp-weights-kettle-epoch0.h5"}
        }

engine = create_engine('sqlite:///data.db')

def get_appliance_name(appliance):
    return SUPPORTED_APPLIANCES[appliance]['name']

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def get_energy_data(appliance,user_id,model_name):

    # predict(model_name,user_id)

    query = f"""
        SELECT timestamp,{appliance}
        FROM {model_name} 
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

def get_history_data(user_id,period):
    query = f"""
        SELECT *
        FROM aggregate
        WHERE user_id = {user_id}
        """

    df = pd.read_sql_query(query, engine)

    if len(df) > 2:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')

        if period == 'last3months':
            three_months_ago = datetime.now() - timedelta(days=90)
            df = df[df.index >= three_months_ago]
            df = df.resample('H').mean()
            labels = df.index.strftime('%Y-%m-%d %H').to_list()
        elif period == 'lastyear':
            last_year = datetime.now() - timedelta(days=365)
            df = df[df.index >= last_year]
            df = df.resample('D').mean()
            labels = df.index.strftime('%d %b. %Y').to_list()
        else:
            df = df.resample('D').mean()
            labels = df.index.strftime('%d %b. %Y').to_list()


        
        values = df['aggregate'].tolist()

    else:
        labels=["no data"]
        values=[0]

    return labels, values

def get_dashboard_data(user_id):

    query = f"""
        SELECT *
        FROM aggregate
        WHERE user_id = {user_id}
        """
    df = pd.read_sql_query(query, engine)

    query2 = f"""
        SELECT *
        FROM dae
        WHERE user_id = {user_id}
        """
    df_p = pd.read_sql_query(query2, engine)

    if len(df) > 1:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.set_index('timestamp')
        data = df['aggregate']

        six_months_ago = datetime.now() - timedelta(days=180)
        day_sum = data[data.index >= six_months_ago]
        day_sum = day_sum.resample('D').mean()
        day_sum.index = day_sum.index.strftime('%b')
        labels = day_sum.index.to_list()
        values = day_sum.values.tolist()


        monthly_sum = data.resample('H').sum().resample('M').mean()  # Summieren auf Monatsbasis
        monthly_sum.index = monthly_sum.index.strftime('%Y-%m')
        mean = round(monthly_sum.values.mean()/1000, 2)

        yearly_sum = data.resample('H').sum().resample('Y').mean()
        yearly_sum.index = yearly_sum.index.strftime('%Y')
        bills = round(yearly_sum.values.mean()*0.008, 2)
        
    else:
        labels=["no data"]
        values=[0]
        mean = 0
        bills = 0

    if len(df_p) > 1:
        # df['other'] = df['aggregate'] - df[['washingmachine', 'fridge', 'microwave', 'kettle']].sum(axis=1) #.apply(lambda x:x[0]-(x[1]+x[2]+x[3]+x[4]))
        mean_values = df_p[['washingmachine', 'fridge', 'microwave', 'kettle']].mean()
        sum_mean = mean_values.sum()
        
        percentages = (mean_values / sum_mean) * 100
        pie_values = percentages.tolist()

        pie_labels = ['washingmachine', 'fridge', 'microwave', 'kettle']

    else:
        pie_values = [0]
        pie_labels = ["no data"]

    return labels, values, mean, bills, pie_values, pie_labels


def get_leaderboard_data():
    # query to get all user ids
    query_users = "SELECT DISTINCT user_id FROM aggregate"
    users_df = pd.read_sql_query(query_users, engine)

    engine_user = create_engine('sqlite:///app.db')

    leaderboard_data = []
    for user_id in users_df['user_id'].values:
        query = f"""
            SELECT *
            FROM aggregate 
            WHERE user_id = {user_id}
            """
        df = pd.read_sql_query(query, engine)
        
        query_user = f'''select first_name, last_name from ab_user where id = {user_id}'''
        name = engine_user.execute(query_user).fetchall()[0]

        if len(df) > 2:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            data = df['aggregate']

            yearly_sum = data.resample('H').sum().resample('Y').mean()
            bills = round(yearly_sum.values.mean() * 0.008, 2)
            avg_consumption = round(data.mean() / 1000, 2)

            leaderboard_data.append({
                'user_id': f'{name[0]} {name[1]}', 
                'avg_consumption': avg_consumption, 
                'bills': bills
            })

    leaderboard_data.sort(key=lambda x: x['bills'], reverse=False)

    return leaderboard_data




#---------------------------------------------------
def normalise(df):
    """
    Normalises the values in df
    """
    mean = df.fillna(method='ffill').values.mean()
    std = df.fillna(method = 'ffill').values.std()
    return (df.fillna(method='ffill').values-mean)/std


def update_dataDB(df,user_id):
    # vorhandene Daten auslesen
    df_existing = pd.read_sql_query(f'SELECT * from aggregate', con=engine)
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
    df_combined.to_sql('aggregate', con=engine, if_exists='replace', index=False)
    


def save_agg(read_csv, user_id):

    data = pd.read_csv(read_csv,header=None).rename(columns={0:'timestamp',1:'aggregate'})
    data['timestamp'] = pd.to_datetime(data['timestamp'])
    data = data.set_index('timestamp')
    data['user_id'] = user_id

    update_dataDB(data.reset_index(),user_id)

def trim_array(arr, target_size):
    remove_count = len(arr) - target_size
    remove_front = remove_count // 2
    remove_back = remove_count // 2
    if remove_count % 2 != 0:
        remove_front += 1
    trimmed_arr = arr[remove_front:(len(arr) - remove_back)]
    return trimmed_arr

def prep_data_for_prediction(aggregate):
    aggregate = normalise(aggregate)
    aggregate = np.pad(aggregate, (WINDOW_SIZE//2, WINDOW_SIZE//2 +1))
    aggregate = np.array([aggregate[i:i+WINDOW_SIZE] for i in range(len(aggregate)-WINDOW_SIZE)])
    aggregate = np.expand_dims(aggregate, axis=-1)
    return aggregate


def predict(model_name,user_id):    
    query = f"""
            SELECT *
            FROM aggregate 
            WHERE user_id = {user_id}
            """
    data = pd.read_sql_query(query, engine).reset_index()
    query = f"""
            SELECT *
            FROM {model_name} 
            WHERE user_id = {user_id}
            """
    current = pd.read_sql_query(query, engine).reset_index()
    to_predict = data[~data['timestamp'].isin(current['timestamp'])]
    aggregate = prep_data_for_prediction(to_predict['aggregate'])
    columns=['timestamp']

    for appliance in SUPPORTED_APPLIANCES.keys():
        WEIGHTS_PATH = os.path.join(BASEDIR,"weights",SUPPORTED_APPLIANCES[appliance][f'{model_name}_weights'])

        if model_name == 'seq2seq':
            predict = predict_seq2seq(WEIGHTS_PATH,aggregate)
        elif model_name == 'seq2point':
            predict = predict_seq2point(WEIGHTS_PATH,aggregate)
        elif model_name == 'dae':
            predict = predict_dae(WEIGHTS_PATH,aggregate)
        else:
            break

        if not len(to_predict['timestamp']) == len(predict):
            predict = trim_array(predict, len(to_predict['timestamp']))

        to_predict[appliance] = predict
        to_predict[appliance] = to_predict[appliance].apply(lambda x: 0 if x < 0 else x)
        columns.append(appliance)
    
    df_p = to_predict[columns].copy()
    df_p['user_id'] = user_id
    df_p.to_sql(model_name, con=engine, if_exists='append', index=False)

    return True



def predict_seq2point(WEIGHTS_PATH,aggregate):
    model = return_seq2point()
    model.load_weights(WEIGHTS_PATH)    
    return model.predict(aggregate)


def predict_seq2seq(WEIGHTS_PATH,aggregate):
    model = return_seq2seq()
    model.load_weights(WEIGHTS_PATH)
    predict = model(aggregate,training = False)
    return aggregate_seq(predict.numpy())

def predict_dae(WEIGHTS_PATH,aggregate):
    model = return_dae()
    model.load_weights(WEIGHTS_PATH)
    predict = model.predict(aggregate)
    return predict.flatten()