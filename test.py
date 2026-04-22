"""
tests.py – Suite de Tests Automatisés (Version SQLAlchemy/Postgres)
INF3521 : Introduction to Software Testing
KWEKEM FANKAM ALEX GEORGY – 23U2469

Teste :
  - CRUD Utilisateurs (SQLAlchemy)
  - Création de comptes
  - Dépôts et Retraits
  - Cas limites et erreurs
"""

import unittest
import json
import os
import sys
import HtmlTestRunner

# Importer l'app Flask et l'objet db
sys.path.insert(0, os.path.dirname(__file__))
from api_transaction import app, db, Utilisateur, Compte, Transaction

class TestResultat:
    """Stocke les résultats pour le rapport de test."""
    resultats = []

    @classmethod
    def ajouter(cls, categorie, nom, statut, detail=""):
        cls.resultats.append({
            "categorie": categorie,
            "nom": nom,
            "statut": statut,   # "PASS" ou "FAIL"
            "detail": detail
        })


class BaseTest(unittest.TestCase):
    """Classe de base : configure Flask en mode test avec une base de données propre."""

    def setUp(self):
        # Configuration de l'application pour le test
        app.config["TESTING"] = True
        # On utilise la même DB mais SQLAlchemy gérera l'isolation
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()

        # Recréer les tables à chaque test pour l'isolation
        db.drop_all()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def post_json(self, url, data):
        return self.client.post(url, data=json.dumps(data),
                                content_type="application/json")

    def put_json(self, url, data):
        return self.client.put(url, data=json.dumps(data),
                               content_type="application/json")

    def creer_user(self, nom="Alex", email="alex@test.cm"):
        r = self.post_json("/utilisateurs", {"nom": nom, "email": email})
        return r, json.loads(r.data)

    def creer_compte_pour_user(self, user_id, type_c="courant", solde=0):
        r = self.post_json(f"/utilisateurs/{user_id}/comptes",
                           {"type_compte": type_c, "solde_initial": solde})
        return r, json.loads(r.data)


# ══════════════════════════════════════════════════════════════════════════════
# 1. TESTS UTILISATEURS – CRUD
# ══════════════════════════════════════════════════════════════════════════════

class TestUtilisateurs(BaseTest):
    CAT = "Utilisateurs – CRUD"

    def test_01_creer_utilisateur_valide(self):
        r, data = self.creer_user("Alex Georgy", "alex@banque.cm")
        ok = r.status_code == 201 and data.get("nom") == "Alex Georgy"
        TestResultat.ajouter(self.CAT, "Créer un utilisateur valide",
                             "PASS" if ok else "FAIL", f"id={data.get('id')}")
        self.assertEqual(r.status_code, 201)

    def test_04_creer_email_duplique(self):
        self.creer_user("Alex", "doublon@banque.cm")
        r, _ = self.creer_user("Bob", "doublon@banque.cm")
        ok = r.status_code == 400
        TestResultat.ajouter(self.CAT, "Email dupliqué → erreur 400",
                             "PASS" if ok else "FAIL")
        self.assertEqual(r.status_code, 400)

    def test_05_lister_utilisateurs(self):
        self.creer_user("Alice", "alice@cm.cm")
        self.creer_user("Bob", "bob@cm.cm")
        r = self.client.get("/utilisateurs")
        data = json.loads(r.data)
        self.assertEqual(len(data), 2)
        TestResultat.ajouter(self.CAT, "Lister tous les utilisateurs", "PASS")

    def test_10_supprimer_utilisateur(self):
        _, u = self.creer_user("Temp", "temp@cm.cm")
        r = self.client.delete(f"/utilisateurs/{u['id']}")
        self.assertEqual(r.status_code, 200)
        # Vérification 404
        r2 = self.client.get(f"/utilisateurs/{u['id']}")
        self.assertEqual(r2.status_code, 404)
        TestResultat.ajouter(self.CAT, "Supprimer un utilisateur", "PASS")


# ══════════════════════════════════════════════════════════════════════════════
# 2. TESTS COMPTES BANCAIRES
# ══════════════════════════════════════════════════════════════════════════════

class TestComptes(BaseTest):
    CAT = "Comptes Bancaires"

    def test_12_creer_compte_courant(self):
        _, u = self.creer_user("Denis", "denis@cm.cm")
        r, data = self.creer_compte_pour_user(u["id"], "courant", 10000)
        self.assertEqual(r.status_code, 201)
        self.assertEqual(data["solde"], 10000)
        TestResultat.ajouter(self.CAT, "Créer un compte courant", "PASS")


# ══════════════════════════════════════════════════════════════════════════════
# 3. TESTS TRANSACTIONS
# ══════════════════════════════════════════════════════════════════════════════

class TestTransactions(BaseTest):
    CAT = "Transactions"

    def _setup_compte(self, solde=10000):
        _, u = self.creer_user("Investor", "inv@cm.cm")
        _, c = self.creer_compte_pour_user(u["id"], "courant", solde)
        return c["id"]

    def test_18_depot_valide(self):
        cid = self._setup_compte(1000)
        r = self.post_json(f"/comptes/{cid}/depot", {"montant": 500})
        data = json.loads(r.data)
        self.assertEqual(data.get("nouveau_solde"), 1500)
        TestResultat.ajouter(self.CAT, "Dépôt valide", "PASS")

    def test_23_retrait_valide(self):
        cid = self._setup_compte(5000)
        r = self.post_json(f"/comptes/{cid}/retrait", {"montant": 2000})
        data = json.loads(r.data)
        self.assertEqual(data.get("nouveau_solde"), 3000)
        TestResultat.ajouter(self.CAT, "Retrait valide", "PASS")

    def test_24_retrait_solde_insuffisant(self):
        cid = self._setup_compte(100)
        r = self.post_json(f"/comptes/{cid}/retrait", {"montant": 999})
        self.assertEqual(r.status_code, 400)
        TestResultat.ajouter(self.CAT, "Retrait solde insuffisant → 400", "PASS")




def run_tests():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # On ajoute toutes tes classes de tests
    classes_de_test = [TestUtilisateurs, TestComptes, TestTransactions]
    for cls in classes_de_test:
        suite.addTests(loader.loadTestsFromTestCase(cls))

    # Configuration du générateur de rapport HTML
    # Il va créer un dossier "reports" et un fichier à l'intérieur
    runner = HtmlTestRunner.HTMLTestRunner(
        output='reports',
        report_title='Rapport de Tests - API Transaction Bancaire',
        report_name='Rapport_INF3521_Alex_Georgy',
        combine_reports=True,
        add_timestamp=True
    )
    
    return runner.run(suite)

if __name__ == "__main__":
    print("Début de la suite de tests...")
    result = run_tests()
    
    # On garde ton résumé console pour le fun
    print(f"\n--- RÉSUMÉ RAPIDE ---")
    for r in TestResultat.resultats:
        print(f"[{r['statut']}] {r['categorie']} : {r['nom']}")
    
    print(f"\nRapport détaillé généré dans le dossier : {os.path.abspath('reports')}")
    
    sys.exit(0 if result.wasSuccessful() else 1)