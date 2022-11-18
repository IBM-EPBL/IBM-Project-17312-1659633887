from flask import Flask, render_template, url_for, redirect, flash, request
from flask_login import login_user, LoginManager, login_required, logout_user
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from wtforms import StringField, PasswordField, SubmitField
from flask_wtf import FlaskForm
from flask_cors import CORS
import joblib
import ibm_db
import requests
# NOTE: you must manually set API_KEY below using information retrieved from your IBM Cloud account.
API_KEY = "05v3AdW4glComLU-hp_MrtEo9fn3RLu27kzVIttUAQ6l"
token_response = requests.post('https://iam.cloud.ibm.com/identity/token', data={"apikey": API_KEY, "grant_type": 'urn:ibm:params:oauth:grant-type:apikey'})
mltoken = token_response.json()["access_token"]

header = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + mltoken}
app = Flask(__name__)
CORS(app)

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'B7-1A3E'

conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=1bbf73c5-d84a-4bb0-85b9-ab1a4348f4a4.c3n41cmd0nqnrk39u98g.databases.appdomain.cloud;PORT=32286;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=jqx32302;PWD=xB6z3lioK6cEBx7c", '', '')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    stmt = ibm_db.prepare(conn, 'SELECT * FROM user WHERE id=?')
    ibm_db.bind_param(stmt, 1, user_id)
    ibm_db.execute(stmt)
    user = ibm_db.fetch_tuple(stmt)
    usr_obj = User(user[0], user[1], user[2])
    return usr_obj

class User:
    def __init__(self, id, email, username):
        self.id = id
        self.username = username
        self.email = email

    def to_json(self):
        return {"username": self.username, "email": self.email}
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)
    

class RegisterForm(FlaskForm):
    email = StringField(validators=[InputRequired(), Length(min=4, max=50)], render_kw={"placeholder":"Email"})
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    rollnumber = StringField(validators=[InputRequired(), Length(min=5, max=10)], render_kw={"placeholder":"RollNumber"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)],render_kw={"placeholder": "Password"})
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        stmt = ibm_db.prepare(conn, 'SELECT * FROM user WHERE username=?')
        ibm_db.bind_param(stmt, 1, username.data)
        ibm_db.execute(stmt)
        existing_user_username = ibm_db.fetch_tuple(stmt)
        if existing_user_username:
            raise ValidationError('That username already exists. Try another one.')

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

class UpdateForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    oldpassword = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder":"Previous Password"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Update')

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        stmt = ibm_db.prepare(conn, 'SELECT * FROM user WHERE username=?')
        ibm_db.bind_param(stmt, 1, form.username.data)
        ibm_db.execute(stmt)
        user = ibm_db.fetch_tuple(stmt)
        if user:
            if bcrypt.check_password_hash(user[4], form.password.data):
                usr_obj = User(user[0], user[1], user[2])
                login_user(usr_obj)
                return redirect(url_for('welcome'))
            else:
                print('Hi')
                flash(f'Invalid credentials, check and try logging in again.', 'danger')
                return redirect(url_for('login'))
    return render_template('login.html', form=form)

@app.route('/welcome', methods=['GET', 'POST'])
@login_required
def welcome():
    return render_template('welcome.html')
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')
    
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        stmt = ibm_db.prepare(conn, 'INSERT INTO user (email, username, roll_number, pass_word) VALUES (?, ?, ?, ?)')
        ibm_db.bind_param(stmt, 1, form.email.data)
        ibm_db.bind_param(stmt, 2, form.username.data)
        ibm_db.bind_param(stmt, 3, form.rollnumber.data)
        ibm_db.bind_param(stmt, 4, hashed_password)
        #hash causes size to exceed VARCHAR size in DB2, hence made VARCHAR(8000)
        ibm_db.execute(stmt)
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@ app.route('/update', methods=['GET', 'POST'])
def update():
    form = UpdateForm()
    if form.validate_on_submit():
        stmt = ibm_db.prepare(conn, 'SELECT * FROM user WHERE username=?')
        ibm_db.bind_param(stmt, 1, form.username.data)
        ibm_db.execute(stmt)
        user = ibm_db.fetch_tuple(stmt)
        if user:
            if bcrypt.check_password_hash(user[4], form.oldpassword.data):
                print(user)
                hashed_password1 = bcrypt.generate_password_hash(form.password.data)
                stmt = ibm_db.prepare(conn, 'UPDATE user SET pass_word=? WHERE username=?')
                ibm_db.bind_param(stmt, 1, hashed_password1)
                ibm_db.bind_param(stmt, 2, form.username.data)
                user = ibm_db.execute(stmt)
                flash(f'Password changed successfully.', 'success')
                return redirect(url_for('home'))
            else:
                flash(f'Invalid password, Enter valid password.', 'danger')
                return redirect(url_for('update'))
        else:
            flash(f'Invalid user, Enter valid User.', 'danger')
            return redirect(url_for('update'))
    return render_template('update.html', form=form)


@app.route('/predict', methods=['POST'])
def predictSpecies():
    wdir = float(request.form['wdir'])
    mnt = float(request.form['mnt'])
    dy = float(request.form['dy'])
    hr = float(request.form['hr'])
    mspd = float(request.form['mspd'])
    X = [[wdir, mnt, dy, hr, mspd]]

    ## NOTE: manually define and pass the array(s) of values to be scored in the next line
    payload_scoring = {"input_data": [{"field": [[wdir, mnt, dy, hr, mspd]], "values": X}]}

    response_scoring = requests.post('https://us-south.ml.cloud.ibm.com/ml/v4/deployments/cf951dc0-191b-4301-b69c-34efcb1adf59/predictions?version=2022-11-12', json=payload_scoring,headers={'Authorization': 'Bearer ' + mltoken})
    print(response_scoring)
    predictions = response_scoring.json()
    predict = predictions['predictions'][0]['values'][0][0]
    print("Final prediction : ",predict)

    return render_template('predict.html',predict=predict)

if __name__ == "__main__":
    app.run(debug=True)

