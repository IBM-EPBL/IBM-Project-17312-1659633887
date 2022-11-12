import flask
from flask import request, render_template
from flask_cors import CORS
import joblib

import requests

# NOTE: you must manually set API_KEY below using information retrieved from your IBM Cloud account.
API_KEY = "k78MvTjP7helaz_76UwZfVrwsHqvZl4c6ZDnfyA3tBFC"
token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey":API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
mltoken = token_response.json()["access_token"]

header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mltoken}




app = flask.Flask(__name__, static_url_path='')
CORS(app)

@app.route('/', methods=['GET'])
def sendHomePage():
    return render_template('dashboard.html')

@app.route('/predict', methods=['POST'])
def predictSpecies():
    wdir = float(request.form['wdir'])
    mnt = float(request.form['mnt'])
    dy = float(request.form['dy'])
    hr = float(request.form['hr'])
    mspd = float(request.form['mspd'])
    X = [[wdir,mnt,dy,hr,mspd]]

    ## NOTE: manually define and pass the array(s) of values to be scored in the next line
    payload_scoring = {"input_data": [{"field": [[wdir,mnt,dy,hr,mspd]], "values": X}]}

    response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/ml/v4/deployments/9246a076-dada-401e-bf10-b4b59fcc9cf2/predictions?version=2022-11-12', json=payload_scoring,headers={'Authorization': 'Bearer ' + mltoken})
    print(response_scoring)
    predictions = response_scoring.json()
    predict = predictions['predictions'][0]['values'][0][0]
    print("Final prediction : ",predict)

    return render_template('predict.html',predict=predict)

if __name__ == '__main__':
    app.run()