from flask import Flask, render_template, url_for, redirect, flash
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
from wtforms import StringField, PasswordField, SubmitField, IntegerField
from flask_wtf import FlaskForm
import sqlite3

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'B7-1A3E'


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    conn = connect_db()
    user = conn.execute('SELECT * FROM user WHERE id = ?',
                        (user_id,)).fetchone()
    usr_obj = User(user[0], user[1], user[2])
    return usr_obj


def connect_db():
    conn = sqlite3.connect('database.db')
    return conn

class User:   

    def __init__(self, id, email, username):
        self.id = id
        self.username = username
        self.email = email

    def to_json(self):        
        return {"username": self.username,
                "email": self.email}

    def is_authenticated(self):
        return True

    def is_active(self):   
        return True           

    def is_anonymous(self):
        return False          

    def get_id(self):         
        return str(self.id)

class RegisterForm(FlaskForm):
    email = StringField(validators=[
        InputRequired(), Length(min=4, max=50)], render_kw={"placeholder": "Email"})
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    rollnumber = StringField(validators=[
        InputRequired(), Length(min=5, max=10)], render_kw={"placeholder": "RollNumber"})
    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Register')

    def validate_username(self, username):
        conn = connect_db()
        existing_user_username = conn.execute('SELECT * FROM user WHERE username = ?',
                                              (username.data,)).fetchone()
        conn.commit()
        conn.close()
        if existing_user_username:
            raise ValidationError(
                'That username already exists. Try another one.')


class LoginForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Login')


class UpdateForm(FlaskForm):
    username = StringField(validators=[
                           InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})

    oldpassword = PasswordField(validators=[
        InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Previous Password"})

    password = PasswordField(validators=[
                             InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField('Update')


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        conn = connect_db()
        user = conn.execute('SELECT * FROM user WHERE username = ?',
                            (form.username.data,)).fetchone()
        conn.commit()
        conn.close()
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
    conn = connect_db()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        conn.execute('INSERT INTO user (email, username, roll_number, pass_word) VALUES (?, ?, ?, ?)',
                     (form.email.data, form.username.data, form.rollnumber.data, hashed_password))
        conn.commit()
        conn.close()
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@ app.route('/update', methods=['GET', 'POST'])
def update():
    form = UpdateForm()
    conn = connect_db()
    if form.validate_on_submit():
        conn = connect_db()
        user = conn.execute('SELECT * FROM user WHERE username = ?',
                            (form.username.data,)).fetchone()
        if user:
            if bcrypt.check_password_hash(user[4], form.oldpassword.data):
                print(user)
                hashed_password1 = bcrypt.generate_password_hash(
                    form.password.data)
                conn.execute('UPDATE user set pass_word = ? where username = ?',
                             (hashed_password1, form.username.data))
                conn.commit()
                conn.close()
                flash(f'Password changed successfully.', 'success')
                return redirect(url_for('home'))
            else:
                flash(f'Invalid password, Enter valid password.', 'danger')
                return redirect(url_for('update'))
        else:
            flash(f'Invalid user, Enter valid User.', 'danger')
            return redirect(url_for('update'))
    return render_template('update.html', form=form)


if __name__ == "__main__":
    app.run(debug=True)
