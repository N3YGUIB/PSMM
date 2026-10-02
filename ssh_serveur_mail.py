import mysql.connector
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from config import *

# Etape 1 : calculer les dates de debut et fin de la journee d'hier
hier = (datetime.now() - timedelta(days=1)).date()
debut = datetime.combine(hier, datetime.min.time())
fin = datetime.combine(hier, datetime.max.time())

# Etape 2 : se connecter a la base de donnees
bdd = mysql.connector.connect(
    host=DB_HOTE,
    user=DB_UTILISATEUR,
    password=DB_MOT_DE_PASSE,
    database=DB_NOM
)
curseur = bdd.cursor()

# Etape 3 : recuperer les tentatives echouees d'hier dans les 3 tables
corps = "Rapport de securite du " + hier.strftime("%d/%m/%Y") + "\n"

tables = ["sql_errors", "ftp_errors", "web_errors"]
noms = ["Serveur MariaDB", "Serveur FTP", "Serveur Web"]

total = 0

for i in range(len(tables)):
    table = tables[i]
    nom = noms[i]

    curseur.execute("SELECT * FROM " + table + " WHERE date_heure BETWEEN %s AND %s", (debut, fin))
    lignes = curseur.fetchall()

    corps = corps + "\n=== " + nom + " (" + str(len(lignes)) + " tentative(s)) ===\n"
    total = total + len(lignes)

    for ligne in lignes:
        corps = corps + "- " + str(ligne) + "\n"

bdd.close()

corps = corps + "\nTotal : " + str(total) + " tentative(s) echouee(s).\n"

# Etape 4 : envoyer le mail
message = MIMEText(corps)
message["From"] = SMTP_EXPEDITEUR
message["To"] = SMTP_DESTINATAIRE
message["Subject"] = "[Supervision] Rapport du " + hier.strftime("%d/%m/%Y")

serveur_smtp = smtplib.SMTP("smtp.gmail.com", 587)
serveur_smtp.starttls()
serveur_smtp.login(SMTP_EXPEDITEUR, SMTP_MOT_DE_PASSE)
serveur_smtp.send_message(message)
serveur_smtp.quit()

print("Mail envoye.")
