from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:admin@localhost/flaskdb'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Utilisateur(db.Model):
    __tablename__= 'Utilisateur'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    email = db.Column(db.String(50))
    password = db.Column(db.String(50))

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password


@app.route("/")
def index():
    return 'hello world'


if __name__ == '__main__':
    app.run(debug=True)