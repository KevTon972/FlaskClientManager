from flask import Flask, render_template, render_template_string, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required, login_user, logout_user, UserMixin

import requests
import folium

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


class Utilisateur(db.Model, UserMixin):
    __tablename__= 'utilisateur'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    clients = db.relationship('Client', backref='utilisateur')
    adresse = db.relationship('Adresse', backref='utilisateur', uselist=False, cascade='save-update, merge, delete')

    def __init__(self, username, email, password, adresse):
        self.username = username
        self.email = email
        self.password = password
        self.adresse = adresse


class Client(db.Model):
    __tablename__ = 'client'
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50))
    telephone = db.Column(db.String(15))
    adresse = db.relationship('Adresse', backref='client', uselist=False, cascade='save-update, merge, delete')

    def __init__(self, utilisateur_id, name, email, telephone, adresse):
        self.utilisateur_id = utilisateur_id
        self.name = name
        self.email = email
        self.telephone = telephone
        self.adresse = adresse


class Adresse(db.Model):
    __tablename__ = 'adresse'
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateur.id'))
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    street_number = db.Column(db.String, nullable=True)
    street_name = db.Column(db.String(100), nullable=False)
    zipcode = db.Column(db.String(50), nullable=False)
    city_name = db.Column(db.String(50), nullable=False)
    
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


@app.route("/index/", methods=['GET', 'POST'])
def index():
    try:
        # check if user is authenticated and recover his clients
        if current_user.is_authenticated:
            user = current_user
            clients = Client.query.filter_by(utilisateur_id=user.id).all()

            return render_template('index.html', clients=clients)
        
    except Exception as e:
        print('Error: ', str(e))
        return render_template('index.html')


@app.route("/register/", methods=['GET', 'POST'])
def register():
    # register the user with form informations
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password') 
        confirm_password = request.form.get('confirm_password')
        street_number = request.form.get('street_number')
        street_name = request.form.get('street_name')
        zipcode = request.form.get('zipcode')
        city_name = request.form.get('city_name')

        # Chek if values aren't none
        if not username or not email or not password or not confirm_password:
            flash("Veuillez remplir tous les champs du formulaire.", 'error')
            return render_template('register.html')

        if password != confirm_password:
            # display error message 
            flash('Les mots de passe ne correspondent pas.', 'error')
            return render_template('register.html')

        # Check if password aren't none
        if password is None:
            flash("Le mot de passe ne peut pas être vide.", 'error')
            return render_template('register.html')

        adresse = Adresse(street_number, street_name, zipcode, city_name)
        hashed_password = generate_password_hash(password, method='pbkdf2:sha1', salt_length=15)
        new_user = Utilisateur(username, email, hashed_password, adresse)

        try:
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('login'))
        
        except Exception as e:
            flash("Il y a eu un problème avec les données. Veuillez réessayer.", 'error')
            print(str(e))
            return render_template('register.html')

    return render_template('register.html')


@app.route("/", methods=['GET', 'POST'])
def login():
    # check if informations are correct and connect the user
    if request.method == 'POST':
        user = Utilisateur.query.filter_by(username=request.form.get('username')).first()

        if user:
            try:
                if check_password_hash(user.password, request.form.get('password')) and user.username == request.form.get('username') or user.email == request.form.get('username'):
                    login_user(user,remember=True)
                    flash('Connexion réussie.', 'success')

                    return redirect(url_for('index'))    
                
            except Exception as e:
                flash("Votre nom ou mot de passe n'est pas correct.", 'error')
                print(str(e))

                return render_template('login.html')
        else:
            flash("L'utilisateur n'est pas enregistré dans la base de données.", 'error')
            return render_template('login.html')
    try:
        user = current_user
        clients = Client.query.filter_by(utilisateur_id=user.id).all()

        return render_template('index.html', clients=clients)
        
    except Exception as e:
        print("Error login:", e)
        return render_template('login.html')


@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


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
                flash(f"Problème avec l'enregistrement du client", 'error')
                print(str(e))
                return render_template('add_a_client.html')
        else:
            flash("Problème avec la création de l'adresse ou du client.", 'error')
            return render_template('add_a_client.html')

    return render_template('add_a_client.html')

@app.route("/client_profil/<int:client_id>", methods=['GET', 'POST'])
def client_profil(client_id):
    client = Client.query.filter_by(id=client_id).first()
    adresse = Adresse.query.filter_by(client_id=client_id).first()
    return render_template('client_profil.html', client=client, adresse=adresse)

@app.route("/update/<int:client_id>", methods=['GET', 'POST'])
@login_required
def update(client_id):
    try:
        client = Client.query.filter_by(id=client_id).first()
        adresse = Adresse.query.filter_by(client_id=client_id).first()

        if request.method == "POST":
            if client and adresse:
                client.name = request.form.get('name')
                client.email = request.form.get('email')
                client.telephone = request.form.get('telephone')
                adresse.street_number = request.form.get('street_number')
                adresse.street_name = request.form.get('street_name')
                adresse.zipcode = request.form.get('zipcode')
                adresse.city_name = request.form.get('city_name')

                db.session.commit()
                flash("Les informations du client ont été mises à jour avec succès.", 'success')
                return redirect(url_for('index'))
            else:
                flash("Impossible de trouver le client ou l'adresse associée.", 'error')
    except Exception as e:
        print(e)
        flash("Aucun résultat trouvé pour le client ou l'adresse associée.", 'error')

    return render_template('client_profil.html', client=client, adresse=adresse)


@app.route("/delete_client/<int:client_id>", methods=['GET', 'POST'])
@login_required
def delete_client(client_id):
    user = current_user
    clients = Client.query.filter_by(utilisateur_id=user.id).all()    
    client = Client.query.filter_by(id=client_id).first()
    adresse = Adresse.query.filter_by(client_id=client_id).first()

    if request.method == 'GET':
        try:
            db.session.delete(client)
            db.session.commit()

            return redirect(url_for('index', clients=clients))

        except Exception as e:
            print(e)
            return render_template('client_profil.html', client=client, adresse=adresse)
    
    return render_template('client_profil.html', client=client, adresse=adresse)


@app.route("/map_street/<int:client_id>")
def map_street(client_id):
    adresse = Adresse.query.filter_by(client_id=client_id).first()
    URL_BASE ='https://nominatim.openstreetmap.org/search?'
    numero_de_rue = adresse.street_number
    street = adresse.street_name
    city = adresse.city_name

    response = requests.get(f'{URL_BASE}q={numero_de_rue}+{street}+{city}&format=json')

    data = response.json()
    longitude = data[0].get('lon')
    latitude = data[0].get('lat')
    location = float(latitude), float(longitude)

    m = folium.Map(location=location,control_scale=True, zoom_start=13, height=400)
    folium.Marker([latitude, longitude], popup='Client Location').add_to(m)
    m.get_root().render()
    header = m.get_root().header.render()
    body_html = m.get_root().html.render()
    script = m.get_root().script.render()

    return render_template_string(
        """
            {% extends 'base.html' %}
                {% block head %}
                    {{ header|safe }}
                {%endblock %}
                {% block body%}
                <div class="flex flex-col justify-center items-center px-6 py-12 lg:px-8">
                    <div class="flex flex-col justify-center items-center w-2/4 px-6 py-12 lg:px-8">
                        <h1 class="">Street Map</h1>
                        {{ body_html|safe }}
                    </div>
                </div>
                    <script>
                        {{ script|safe }}
                    </script>
                {% endblock %}
            
        """,
        header=header,
        body_html=body_html,
        script=script,
    )



if __name__ == '__main__':
    app.run(debug=True)
