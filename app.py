from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required, login_user, logout_user, UserMixin
from secret_key import SECRET_KEY


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost/flaskdb'
app.config['SECRET_KEY'] = SECRET_KEY
app.config['STATIC_FOLDER'] = 'static'

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager()
login_manager.init_app(app)

with app.app_context():
    db.create_all()


class Utilisateur(db.Model, UserMixin):
    __tablename__= 'utilisateur'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False,)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    clients = db.relationship('Client', backref='utilisateur')

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password


class Client(db.Model):
    __tablename__ = 'client'
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50))
    telephone = db.Column(db.String(15))
    adresse = db.relationship('Adresse', backref='client', uselist=False)

    def __init__(self, name, email, telephone, adresse):
        self.name = name
        self.email = email
        self.telephone = telephone
        self.adresse = adresse


class Adresse(db.Model):
    __tablename__ = 'adresse'
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    street_number = db.Column(db.Integer, nullable=False)
    street_name = db.Column(db.String(100), nullable=False)
    zipcode = db.Column(db.String(20), nullable=False)
    city_name = db.Column(db.String(20), nullable=False)
    
    def __init__(self, street_number, street_name, zipcode, city_name):
        self.street_number = street_number
        self.street_name = street_name
        self.zipcode = zipcode
        self.city_name = city_name
    
    def __str__(self):
        return f'{self.street_number}, {self.street_name} {self.zipcode} {self.city_name}'


@login_manager.user_loader
def loader_user(user_id):
    return db.session.get(Utilisateur, int(user_id))


@app.route("/", methods=['GET', 'POST'])
def index():
    return render_template('index.html')


@app.route("/register/", methods=['GET', 'POST'])
def register():
    # register the user with form informations
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password') 
        confirm_password = request.form.get('confirm_password')

        # Ajoutez des vérifications pour vous assurer que les valeurs ne sont pas None
        if not username or not email or not password or not confirm_password:
            flash("Veuillez remplir tous les champs du formulaire.", 'error')
            return render_template('register.html')

        if password != confirm_password:
            # display error message 
            flash('Les mots de passe ne correspondent pas.', 'error')
            return render_template('register.html')

        # Ajoutez une vérification pour vous assurer que password n'est pas None
        if password is None:
            flash("Le mot de passe ne peut pas être vide.", 'error')
            return render_template('register.html')

        hashed_password = generate_password_hash(password, method='pbkdf2:sha1', salt_length=15)
        new_user = Utilisateur(username=username, email=email, password=hashed_password)

        try:
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login'))
        
        except Exception as e:
            flash("Il y a eu un problème avec les données. Veuillez réessayer.", 'error')
            print(str(e))
            return render_template('register.html')

    return render_template('register.html')


@app.route("/login/", methods=['GET', 'POST'])
def login():
    # check if informations are correct and connect the user
    if request.method == 'POST':
        user = Utilisateur.query.filter_by(username=request.form.get('username')).first()
        try:
            if check_password_hash(user.password, request.form.get('password')) and user.username == request.form.get('username'):
                login_user(user,remember=True)
                flash('Connexion réussie.', 'success')
                return redirect(url_for('index'))
        except Exception as e:
            flash("Votre nom ou mot de passe n'est pas correct.", 'error')
            print(str(e))
            return render_template('login.html')
        
    return render_template('login.html')



@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route("/add_a_client", methods=['GET', 'POST'])
@login_required
def add_a_client():
    # recover client informations and save them in db
    if request.method == 'POST':
        client_name =  request.form.get('name')
        client_email = request.form.get('email')
        client_telephone = request.form.get('telephone')
        street_number = request.form.get('street_number')
        street_name = request.form.get('street_name')
        zipcode = request.form.get('zipcode')
        city_name = request.form.get('city_name')

        # verifier que les valeurs ne sont pas None
        if not client_name or not client_email or not client_telephone or not street_number or not street_name or not zipcode or not city_name:
            flash("Veuillez remplir tous les champs du formulaire.", 'error')
            return render_template('add_client.html')

        adresse = Adresse(street_number, street_name, zipcode, city_name)
        new_client = Client(current_user.id, client_name, client_email, client_telephone, adresse)
  
        # verifier que les objets ne sont pas None
        if adresse and new_client:
            try:
                db.session.add(new_client)
                db.session.commit()

                flash("L'enregistrement de votre nouveau client est un succès", 'success')
                return redirect(url_for('index'))
            except Exception as e:
                flash(f"Problème avec l'enregistrement du client : {str(e)}", 'error')
                print(str(e))
                return render_template('add_client.html')
        else:
            flash("Problème avec la création de l'adresse ou du client.", 'error')
            return render_template('add_client.html')

    return render_template('add_a_client.html')


if __name__ == '__main__':
    app.run(debug=True)
