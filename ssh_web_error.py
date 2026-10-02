import paramiko
import mysql.connector
import os
from datetime import datetime
from config import *

# Etape 1 : se connecter en SSH au serveur Web
cle = os.path.expanduser("~/.ssh/id_ed25519_monitor")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("172.16.78.160", username="monitor", key_filename=cle)

# Etape 2 : lire le fichier de log
commande = "sudo cat /var/log/nginx/access.log"
entree, sortie, erreur = ssh.exec_command(commande, get_pty=True)
lignes = sortie.readlines()
ssh.close()

# Etape 3 : parcourir chaque ligne pour trouver les echecs (code 401)
liste_erreurs = []

for ligne in lignes:

    if " 401 " in ligne:
        adresse_ip = ligne.split(" ")[0]

        utilisateur = ligne.split(" - ")[1]
        utilisateur = utilisateur.split(" ")[0]

        morceau_date = ligne.split("[")[1]
        morceau_date = morceau_date.split("]")[0]
        morceau_date = morceau_date.split(" ")[0]  # on enleve le fuseau horaire

        date_objet = datetime.strptime(morceau_date, "%d/%b/%Y:%H:%M:%S")

        liste_erreurs.append((utilisateur, date_objet, adresse_ip))

# Etape 4 : se connecter a la base de donnees
bdd = mysql.connector.connect(
    host=DB_HOTE,
    user=DB_UTILISATEUR,
    password=DB_MOT_DE_PASSE,
    database=DB_NOM
)
curseur = bdd.cursor()

# Etape 5 : enregistrer chaque erreur trouvee
for erreur in liste_erreurs:
    utilisateur = erreur[0]
    date_objet = erreur[1]
    adresse_ip = erreur[2]

    requete = "INSERT INTO web_errors (username, date_heure, ip_source, code_http) VALUES (%s, %s, %s, %s)"
    curseur.execute(requete, (utilisateur, date_objet, adresse_ip, 401))

bdd.commit()
bdd.close()

# Etape 6 : afficher un resume
print(str(len(liste_erreurs)) + " tentative(s) web echouee(s) enregistree(s).")
