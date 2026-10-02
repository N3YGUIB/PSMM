import paramiko
import mysql.connector
import os
from config import *

# Etape 1 : se connecter en SSH au serveur FTP
cle = os.path.expanduser("~/.ssh/id_ed25519_monitor")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("172.16.78.161", username="monitor", key_filename=cle)

# Etape 2 : lire le fichier de log
commande = "sudo cat /var/log/proftpd/auth.log"
entree, sortie, erreur = ssh.exec_command(commande, get_pty=True)
lignes = sortie.readlines()
ssh.close()

# Etape 3 : convertir les noms de mois francais en chiffres
mois = {
    "janv.": "01", "fevr.": "02", "mars": "03", "avr.": "04",
    "mai": "05", "juin": "06", "juil.": "07", "aout": "08",
    "sept.": "09", "oct.": "10", "nov.": "11", "dec.": "12"
}

# Etape 4 : parcourir chaque ligne du log pour trouver les echecs
liste_erreurs = []
utilisateur = ""
adresse_ip = ""
date_complete = ""

for ligne in lignes:

    if '"USER ' in ligne:
        morceau = ligne.split('"USER ')[1]
        utilisateur = morceau.split('"')[0]

        adresse_ip = ligne.split(" ")[0]

        morceau_date = ligne.split("[")[1]
        morceau_date = morceau_date.split("]")[0]
        jour = morceau_date.split("/")[0]
        nom_mois = morceau_date.split("/")[1]
        reste = morceau_date.split("/")[2]
        annee = reste[0:4]
        heure = reste[5:13]

        numero_mois = mois[nom_mois]
        date_complete = annee + "-" + numero_mois + "-" + jour + " " + heure

    if '"PASS' in ligne and " 530" in ligne:
        liste_erreurs.append((utilisateur, date_complete, adresse_ip))

# Etape 5 : se connecter a la base de donnees
bdd = mysql.connector.connect(
    host=DB_HOTE,
    user=DB_UTILISATEUR,
    password=DB_MOT_DE_PASSE,
    database=DB_NOM
)
curseur = bdd.cursor()

# Etape 6 : enregistrer chaque erreur trouvee
for erreur in liste_erreurs:
    utilisateur = erreur[0]
    date_complete = erreur[1]
    adresse_ip = erreur[2]

    requete = "INSERT INTO ftp_errors (username, date_heure, ip_source) VALUES (%s, %s, %s)"
    curseur.execute(requete, (utilisateur, date_complete, adresse_ip))

bdd.commit()
bdd.close()

# Etape 7 : afficher un resume
print(str(len(liste_erreurs)) + " tentative(s) FTP echouee(s) enregistree(s).")
