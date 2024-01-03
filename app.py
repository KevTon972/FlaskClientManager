from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost/flaskdb'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

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


@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('base.html')


@app.route("/register/", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password') 
        confirm_password = request.form.get('confirm_password')

        if password == confirm_password:
            new_user = Utilisateur(username=username, email=email, password=generate_password_hash(password, method='pbkdf2:sha1', salt_length=15))
            print(new_user.password)

            try:

                db.session.add(new_user)
                db.session.commit()

                return redirect(url_for('login'))
        
            except:
                print("Erreur dans l'enregistrement des données")

                return render_template('register.html')
        else:
            # ajouter affichage message d'erreur avec flash
            print('too bad')
            return render_template('register.html')

        

    return render_template('register.html')


@app.route("/login/", methods=['GET', 'POST'])
def login():
    # ajouter logique pour connecter l'utilisateur
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)