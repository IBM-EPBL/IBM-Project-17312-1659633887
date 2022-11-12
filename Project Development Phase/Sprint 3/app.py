import flask
from flask import request, render_template
from flask_cors import CORS
import joblib

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
    model = joblib.load('power.pkl')
    power = model.predict(X)[0]
    return render_template('predict.html',predict=power)

if __name__ == '__main__':
    app.run()