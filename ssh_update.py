import subprocess
import paramiko
import smtplib
import os
from email.mime.text import MIMEText
from config import *

cle = os.path.expanduser("~/.ssh/id_ed25519_monitor")

serveurs = {
    "ftp": "172.16.78.161",
    "web": "172.16.78.160",
    "sql": "172.16.78.163"
}

# Etape 1 : lire les identifiants Alcasar dans le fichier .alcapass
fichier = open(os.path.expanduser("/home/debian-monitor/alcapass"), "r")
contenu = fichier.read()
fichier.close()

email_alcasar = contenu.split(" ")[0]
password_alcasar = contenu.split(" ")[1].strip()

# Etape 2 : se connecter a Alcasar (recuperation du token puis authentification)
commande_challenge = "curl -k -L --request GET https://alcasar.laplateforme.io/intercept.php 2>&1 | grep -oP 'name=\"challenge\" value=\"\\K(?:(?!\").)*'"
resultat_challenge = subprocess.run(commande_challenge, shell=True, capture_output=True, text=True)
challenge = resultat_challenge.stdout.strip()

commande_login = [
    "curl", "--request", "POST",
    "--url", "https://alcasar.laplateforme.io/intercept.php",
    "--header", "Content-Type: multipart/form-data",
    "--form", "username=" + email_alcasar,
    "--form", "password=" + password_alcasar,
    "--form", "challenge=" + challenge,
    "--form", "button=Authentication",
    "--location", "https://alcasar.laplateforme.io/intercept.php"
]
subprocess.run(commande_login, capture_output=True)

print("Connexion a Alcasar réussi.")

# Etape 3 : aller sur chaque serveur pour verifier et installer les mises a jour
liste_serveurs_a_redemarrer = []

for nom_serveur in serveurs:
    ip = serveurs[nom_serveur]

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username="monitor", key_filename=cle)

    # on met a jour la liste des paquets disponibles
    ssh.exec_command("sudo apt update", get_pty=True)

    # on installe les mises a jour disponibles
    entree, sortie, erreur = ssh.exec_command("sudo apt upgrade -y", get_pty=True)
    resultat_upgrade = sortie.read().decode()

    print(nom_serveur + " : mise a jour effectuee.")

    # on verifie si un redemarrage est necessaire
    entree, sortie, erreur = ssh.exec_command("test -f /var/run/reboot-required && echo OUI || echo NON")
    besoin_redemarrage = sortie.read().decode().strip()

    if besoin_redemarrage == "OUI":
        liste_serveurs_a_redemarrer.append(nom_serveur)
        print(nom_serveur + " : redemarrage necessaire.")

    ssh.close()

# Etape 4 : envoyer un mail si au moins un serveur a besoin d'etre redemarre
if len(liste_serveurs_a_redemarrer) > 0:
    corps = "Les serveurs suivants ont besoin d'etre redemarres apres mise a jour :\n\n"
    for nom_serveur in liste_serveurs_a_redemarrer:
        corps = corps + "- " + nom_serveur + "\n"

    message = MIMEText(corps)
    message["From"] = SMTP_EXPEDITEUR
    message["To"] = SMTP_DESTINATAIRE
    message["Subject"] = "[Supervision] Redemarrage necessaire apres mise a jour"

    serveur_smtp = smtplib.SMTP("smtp.gmail.com", 587)
    serveur_smtp.starttls()
    serveur_smtp.login(SMTP_EXPEDITEUR, SMTP_MOT_DE_PASSE)
    serveur_smtp.send_message(message)
