import mysql.connector
from config import *

# Etape 1 : se connecter a la base de donnees
bdd = mysql.connector.connect(
    host=DB_HOTE,
    user=DB_UTILISATEUR,
    password=DB_MOT_DE_PASSE,
    database=DB_NOM
)

print("Connexion reussie a la base supervision.")

# Etape 2 : afficher la liste des tables presentes
curseur = bdd.cursor()
curseur.execute("SHOW TABLES;")
tables = curseur.fetchall()

print("Tables presentes :")
for table in tables:
    print("-", table[0])

bdd.close()
