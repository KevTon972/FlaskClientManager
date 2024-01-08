from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user
from secret_key import SECRET_KEY


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost/flaskdb'
app.config['SECRET_KEY'] = SECRET_KEY

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)

with app.app_context():
    db.create_all()


class Utilisateur(db.Model):
    __tablename__= 'utilisateur'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False,)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password
    
    def is_active(self):
        return True

    def get_id(self):
        return self.id


@login_manager.user_loader
def loader_user(user_id):
    return Utilisateur.query.get(user_id)


@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('base.html')


@app.route("/register/", methods=['GET', 'POST'])
def register():
    # register the user with form informations
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password') 
        confirm_password = request.form.get('confirm_password')

        if password == confirm_password:
            new_user = Utilisateur(username=username,
                                   email=email,
                                   password=generate_password_hash(password, method='pbkdf2:sha1', salt_length=15))

            try:
                db.session.add(new_user)
                db.session.commit()

                return redirect(url_for('login'))
        
            except:
                flash("Error with datas", 'error')
                return render_template('register.html')
        else:
            # display error message 
            flash('Problem with the Password')
            return render_template('register.html')

    return render_template('register.html')


@app.route("/login/", methods=['GET', 'POST'])
def login():
    # check if informations are correct and connect the user
    if request.method == 'POST':
        user = Utilisateur.query.filter_by(username=request.form.get('username')).first()
        
        if check_password_hash(user.password, request.form.get('password')) and user.username == request.form.get('username'):
            login_user(user,remember=True)
            flash('Successful Login', 'success')
            return redirect(url_for('index'))
        else:
            flash("Your username or your password aren't correct", 'error')
            return render_template('login.html')
        
    return render_template('login.html')


if __name__ == '__main__':
    app.run(debug=True)