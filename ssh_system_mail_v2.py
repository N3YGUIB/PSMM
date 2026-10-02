import paramiko
import mysql.connector
import smtplib
import os
import json
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from config import *

# Seuils d'alerte (modifiables ici facilement)
SEUIL_CPU = 70
SEUIL_RAM = 80
SEUIL_DISK = 90

# Liste des serveurs a surveiller
serveurs = {
    "ftp": "172.16.78.161",
    "web": "172.16.78.160",
    "sql": "172.16.78.163"
}

cle = os.path.expanduser("~/.ssh/id_ed25519_monitor")
fichier_suivi = os.path.expanduser("~/dernier_mail_envoye.json")

# Etape 1 : charger la date du dernier mail envoye pour chaque serveur
if os.path.exists(fichier_suivi):
    fichier = open(fichier_suivi, "r")
    derniers_envois = json.load(fichier)
    fichier.close()
else:
    derniers_envois = {}

# Etape 2 : se connecter a la base de donnees
bdd = mysql.connector.connect(
    host=DB_HOTE,
    user=DB_UTILISATEUR,
    password=DB_MOT_DE_PASSE,
    database=DB_NOM
)
curseur = bdd.cursor()

# Etape 3 : verifier chaque serveur un par un
for nom_serveur in serveurs:
    ip = serveurs[nom_serveur]

    # connexion SSH au serveur
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username="monitor", key_filename=cle)

    # recuperer le CPU
    entree, sortie, erreur = ssh.exec_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'")
    texte_cpu = sortie.read().decode()
    cpu = float(texte_cpu.strip().replace(",", "."))

    # recuperer la RAM
    entree, sortie, erreur = ssh.exec_command("free | grep Mem | awk '{print ($3/$2) * 100}'")
    texte_ram = sortie.read().decode()
    ram = float(texte_ram.strip().replace(",", "."))

    # recuperer le DISQUE
    entree, sortie, erreur = ssh.exec_command("df / | tail -1 | awk '{print $5}' | tr -d '%'")
    texte_disk = sortie.read().decode()
    disk = float(texte_disk.strip().replace(",", "."))

    ssh.close()

    print(nom_serveur + " -> CPU: " + str(cpu) + "%  RAM: " + str(ram) + "%  DISK: " + str(disk) + "%")

    # Etape 4 : enregistrer les valeurs dans la base
    requete = "INSERT INTO system_status (serveur, date_heure, cpu_percent, ram_percent, disk_percent) VALUES (%s, %s, %s, %s, %s)"
    curseur.execute(requete, (nom_serveur, datetime.now(), cpu, ram, disk))
    bdd.commit()

    # Etape 5 : construire la liste des alertes si un seuil est depasse
    alertes = []
    if cpu > SEUIL_CPU:
        alertes.append("CPU trop eleve : " + str(cpu) + "%")
    if ram > SEUIL_RAM:
        alertes.append("RAM trop elevee : " + str(ram) + "%")
    if disk > SEUIL_DISK:
        alertes.append("DISQUE trop plein : " + str(disk) + "%")

    # Etape 6 : envoyer un mail seulement s'il y a une alerte ET que le dernier mail date de plus d'1h
    if len(alertes) > 0:

        peut_envoyer = True
        if nom_serveur in derniers_envois:
            dernier_envoi = datetime.fromisoformat(derniers_envois[nom_serveur])
            if datetime.now() - dernier_envoi < timedelta(hours=1):
                peut_envoyer = False

        if peut_envoyer:
            corps = "Alerte sur le serveur " + nom_serveur + " :\n\n"
            for alerte in alertes:
                corps = corps + "- " + alerte + "\n"

            message = MIMEText(corps)
            message["From"] = SMTP_EXPEDITEUR
            message["To"] = SMTP_DESTINATAIRE
            message["Subject"] = "[ALERTE] Ressources critiques sur " + nom_serveur

            serveur_smtp = smtplib.SMTP("smtp.gmail.com", 587)
            serveur_smtp.starttls()
            serveur_smtp.login(SMTP_EXPEDITEUR, SMTP_MOT_DE_PASSE)
            serveur_smtp.send_message(message)
            serveur_smtp.quit()

            print("Mail envoye pour " + nom_serveur)

            derniers_envois[nom_serveur] = datetime.now().isoformat()
        else:
            print("Mail ignore pour " + nom_serveur + " (deja envoye il y a moins d'1h)")

bdd.close()

# Etape 7 : sauvegarder la date des mails envoyes
fichier = open(fichier_suivi, "w")
json.dump(derniers_envois, fichier)
fichier.close()

# Etape 8 : supprimer les donnees de plus de 72h
bdd = mysql.connector.connect(
    host=DB_HOTE,
    user=DB_UTILISATEUR,
    password=DB_MOT_DE_PASSE,
    database=DB_NOM
)
curseur = bdd.cursor()
limite = datetime.now() - timedelta(hours=72)
curseur.execute("DELETE FROM system_status WHERE date_heure < %s", (limite,))
bdd.commit()
bdd.close()
