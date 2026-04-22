from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flasgger import Swagger
import os
import random
from datetime import datetime
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv() # Charge les variables du fichier .env en local

# Utilise la variable d'environnement de Render, ou localhost par défaut
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "postgresql://alex:Bf1im16y@localhost/banque")
#DB
#app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://alex:Bf1im16y@localhost/banque"


db = SQLAlchemy(app)
swagger = Swagger(app)


#  MODÈLES BD~
class Utilisateur(db.Model):
    __tablename__ = 'utilisateurs'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    comptes = db.relationship('Compte', backref='titulaire', lazy=True, cascade="all, delete-orphan")

    def convertir_json(self):
        return {"id": self.id, "nom": self.nom, "email": self.email}

class Compte(db.Model):
    __tablename__ = 'comptes'
    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    type_compte = db.Column(db.String(20), default='courant')
    solde = db.Column(db.Float, default=0.0)
    transactions = db.relationship('Transaction', backref='compte_associe', lazy=True)

    def convertir_json(self):
        return {
            "id": self.id, "utilisateur_id": self.utilisateur_id,
            "numero": self.numero, "type_compte": self.type_compte, "solde": self.solde
        }

class Transaction(db.Model):
    __tablename__ = 'transactions'
    id = db.Column(db.Integer, primary_key=True)
    compte_id = db.Column(db.Integer, db.ForeignKey('comptes.id'), nullable=False)
    type_op = db.Column(db.String(20), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    solde_apres = db.Column(db.Float, nullable=False)
    date_op = db.Column(db.DateTime, default=datetime.utcnow)

    def convertir_json(self):
        return {
            "id": self.id, "type_op": self.type_op, 
            "montant": self.montant, "solde_apres": self.solde_apres, "date": self.date_op.isoformat()
        }

# Initialisation des tables
with app.app_context():
    db.create_all()
# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES UTILISATEURS (CRUD)
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/utilisateurs", methods=["POST"])
def creer_utilisateur():
    """
    Créer un utilisateur
    ---
    tags: [Utilisateurs]
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nom: {type: string, example: "Alex Georgy"}
            email: {type: string, example: "alex@banque.cm"}
    responses:
      201: {description: "Utilisateur créé"}
      400: {description: "Erreur de validation ou email déjà utilisé"}
    """
    data = request.get_json()
    if not data or not data.get("nom") or not data.get("email"):
        return jsonify({"erreur": "nom et email requis"}), 400
    try:
        user = Utilisateur(nom=data["nom"].strip(), email=data["email"].strip().lower())
        db.session.add(user)
        db.session.commit()
        return jsonify(user.convertir_json()), 201
    except:
        db.session.rollback()
        return jsonify({"erreur": "email déjà utilisé"}), 400

@app.route("/utilisateurs", methods=["GET"])
def lister_utilisateurs():
    """
    Lister tous les utilisateurs
    ---
    tags: [Utilisateurs]
    responses:
      200: {description: "Liste des utilisateurs"}
    """
    users = Utilisateur.query.all()
    return jsonify([u.convertir_json() for u in users])

@app.route("/utilisateurs/<int:user_id>", methods=["GET"])
def obtenir_utilisateur(user_id):
    """
    Obtenir un utilisateur par ID
    ---
    tags: [Utilisateurs]
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200: {description: "Utilisateur trouvé"}
    """
    user = Utilisateur.query.get_or_404(user_id)
    return jsonify(user.convertir_json())

@app.route("/utilisateurs/<int:user_id>", methods=["PUT"])
def modifier_utilisateur(user_id):
    """
    Modifier un utilisateur
    ---
    tags: [Utilisateurs]
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            nom: {type: string, example: "Nouveau Nom"}
            email: {type: string, example: "nouveau@email.com"}
    responses:
      200: {description: "Utilisateur modifié"}
    """
    user = Utilisateur.query.get_or_404(user_id)
    data = request.get_json()
    user.nom = data.get("nom", user.nom)
    user.email = data.get("email", user.email)
    db.session.commit()
    return jsonify(user.convertir_json())

@app.route("/utilisateurs/<int:user_id>", methods=["DELETE"])
def supprimer_utilisateur(user_id):
    """
    Supprimer un utilisateur
    ---
    tags: [Utilisateurs]
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
    responses:
      200: {description: "Utilisateur supprimé"}
    """
    user = Utilisateur.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"Utilisateur {user_id} supprimé avec succès"})

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES COMPTES
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/utilisateurs/<int:user_id>/comptes", methods=["POST"])
def creer_compte(user_id):
    """
    Créer un compte bancaire
    ---
    tags: [Comptes]
    parameters:
      - in: path
        name: user_id
        type: integer
        required: true
      - in: body
        name: body
        schema:
          type: object
          properties:
            type_compte: {type: string, example: "courant"}
            solde_initial: {type: number, example: 5000}
    responses:
      201: {description: "Compte créé"}
    """
    user = Utilisateur.query.get_or_404(user_id)
    data = request.get_json() or {}
    
    numero = f"BK{user.id:04d}{random.randint(100000, 999999)}"
    nouveau_compte = Compte(
        utilisateur_id=user.id,
        numero=numero,
        type_compte=data.get("type_compte", "courant"),
        solde=float(data.get("solde_initial", 0.0))
    )
    db.session.add(nouveau_compte)
    db.session.commit()
    return jsonify(nouveau_compte.convertir_json()), 201

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTES TRANSACTIONS
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/comptes/<int:compte_id>/depot", methods=["POST"])
def effectuer_depot(compte_id):
    """
    Effectuer un dépôt
    ---
    tags: [Transactions]
    parameters:
      - in: path
        name: compte_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            montant: {type: number, example: 1000}
    responses:
      200: {description: "Dépôt réussi"}
    """
    compte = Compte.query.get_or_404(compte_id)
    data = request.get_json()
    montant = float(data.get("montant", 0))

    if montant <= 0: return jsonify({"erreur": "montant invalide"}), 400

    compte.solde += montant
    txn = Transaction(compte_id=compte.id, type_op="depot", montant=montant, solde_apres=compte.solde)
    db.session.add(txn)
    db.session.commit()
    
    return jsonify({"message": "Dépôt réussi", "nouveau_solde": compte.solde})

@app.route("/comptes/<int:compte_id>/retrait", methods=["POST"])
def effectuer_retrait(compte_id):
    """
    Effectuer un retrait
    ---
    tags: [Transactions]
    parameters:
      - in: path
        name: compte_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            montant: {type: number, example: 500}
    responses:
      200: {description: "Retrait réussi"}
      400: {description: "Solde insuffisant"}
    """
    compte = Compte.query.get_or_404(compte_id)
    data = request.get_json()
    montant = float(data.get("montant", 0))

    if montant <= 0 or compte.solde < montant:
        return jsonify({"erreur": "montant invalide ou solde insuffisant"}), 400

    compte.solde -= montant
    txn = Transaction(compte_id=compte.id, type_op="retrait", montant=montant, solde_apres=compte.solde)
    db.session.add(txn)
    db.session.commit()

    return jsonify({"message": "Retrait réussi", "nouveau_solde": compte.solde})

@app.route("/comptes/<int:compte_id>/transactions", methods=["GET"])
def historique_transactions(compte_id):
    """
    Historique des transactions
    ---
    tags: [Transactions]
    parameters:
      - in: path
        name: compte_id
        type: integer
        required: true
    responses:
      200: {description: "Liste des transactions"}
    """
    compte = Compte.query.get_or_404(compte_id)
    return jsonify([t.convertir_json() for t in compte.transactions])

if __name__ == "__main__":
    app.run(debug=True)