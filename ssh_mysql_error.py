import paramiko
import mysql.connector
import os
from config import *

# Etape 1 : se connecter en SSH au serveur SQL
cle = os.path.expanduser("~/.ssh/id_ed25519_monitor")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("172.16.78.163", username="monitor", key_filename=cle)

# Etape 2 : lire le fichier de log
commande = "sudo cat /var/log/mysql/error.log"
entree, sortie, erreur = ssh.exec_command(commande, get_pty=True)
lignes = sortie.readlines()
ssh.close()

# Etape 3 : parcourir chaque ligne pour trouver les echecs de connexion
liste_erreurs = []
# Split les données
for ligne in lignes:

    if "Access denied for user" in ligne:
        date_complete = ligne.split(" ")[0] + " " + ligne.split(" ")[1]
        utilisateur = ligne.split("'")[1]
        adresse_ip = ligne.split("'")[3]

        liste_erreurs.append((utilisateur, date_complete, adresse_ip))

# Etape 4 : se connecter a la base de données
bdd = mysql.connector.connect(
    host=DB_HOTE,
    user=DB_UTILISATEUR,
    password=DB_MOT_DE_PASSE,
    database=DB_NOM
)
curseur = bdd.cursor()

# Etape 5 : enregistrer chaque erreur trouvée
for erreur in liste_erreurs:
    utilisateur = erreur[0]
    date_complete = erreur[1]
    adresse_ip = erreur[2]

    requete = "INSERT INTO sql_errors (username, date_heure, ip_source) VALUES (%s, %s, %s)"
    curseur.execute(requete, (utilisateur, date_complete, adresse_ip))

bdd.commit()
bdd.close()

# Etape 6 : afficher un resume
print(str(len(liste_erreurs)) + " tentative(s) SQL echouee(s) enregistree(s).")
