from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
import os
from dotenv import load_dotenv

app = Flask(__name__)


load_dotenv() # Charge les variables du fichier .env en local

# Utilise la variable d'environnement de Render, ou localhost par défaut
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "postgresql://alex:Bf1im16y@localhost/banque")
#DB
#app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://alex:Bf1im16y@localhost/banque"


db = SQLAlchemy(app)
swagger = Swagger(app)


class Utilisateur(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    solde = db.Column(db.Float, default=0.0)

    def convertir_json(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "solde": self.solde
        }
    
#creation des tables
with app.app_context():
    db.create_all()
    print("Toutes les tables ont ete creer")

#routes pour ajouter les utilisateurs
@app.route("/utilisateurs", methods=["POST"])
def ajouter_utilisateur():
    """
    Ajouter un utilisateur
    ---
    tags:
      - Utilisateurs
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nom:
              type: string
              example: "Alex"
            solde:
              type: number
              example: 1000
    responses:
      201:
        description: utilisateur créé
      400:
        description: erreur de validation (probleme dans  la requete)
    """
    data = request.get_json()
    if not data or "nom" not in data:
        return jsonify({"erreur": "nom requis"}), 400
   

    user = Utilisateur(
        nom=data["nom"],
        solde=data.get("solde", 0)
    )

    db.session.add(user)
    db.session.commit()

    return jsonify(user.convertir_json()), 201


#Route pour lister les utilisateurs
@app.route("/utilisateurs", methods=["GET"])
def lister_utilisateurs():
    """
    Lister les utilisateurs
    ---
    tags:
      - Utilisateurs
    responses:
      200:
        description: liste des utilisateurs
        schema:
          type: array
          items:
            type: object
    """

    users = Utilisateur.query.all()
    return jsonify([u.convertir_json() for u in users])


if __name__ == "__main__":
    app.run(debug=True)