import paramiko
import mysql.connector
import os
from datetime import datetime, timedelta
from config import *

# Liste des serveurs a surveiller
serveurs = {
    "ftp": "172.16.78.161",
    "web": "172.16.78.160",
    "sql": "172.16.78.163"
}

cle = os.path.expanduser("~/.ssh/id_ed25519_monitor")

# Etape 1 : se connecter a la base de donnees
bdd = mysql.connector.connect(
    host=DB_HOTE,
    user=DB_UTILISATEUR,
    password=DB_MOT_DE_PASSE,
    database=DB_NOM
)
curseur = bdd.cursor()

# Etape 2 : verifier chaque serveur un par un
for nom_serveur in serveurs:
    ip = serveurs[nom_serveur]

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username="monitor", key_filename=cle)

    entree, sortie, erreur = ssh.exec_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'")
    cpu = float(sortie.read().decode().strip().replace(",", "."))

    entree, sortie, erreur = ssh.exec_command("free | grep Mem | awk '{print ($3/$2) * 100}'")
    ram = float(sortie.read().decode().strip().replace(",", "."))

    entree, sortie, erreur = ssh.exec_command("df / | tail -1 | awk '{print $5}' | tr -d '%'")
    disk = float(sortie.read().decode().strip().replace(",", "."))

    ssh.close()

    print(nom_serveur + " -> CPU: " + str(cpu) + "%  RAM: " + str(ram) + "%  DISK: " + str(disk) + "%")

    requete = "INSERT INTO system_status (serveur, date_heure, cpu_percent, ram_percent, disk_percent) VALUES (%s, %s, %s, %s, %s)"
    curseur.execute(requete, (nom_serveur, datetime.now(), cpu, ram, disk))
    bdd.commit()

# Etape 3 : supprimer les donnees de plus de 72h
limite = datetime.now() - timedelta(hours=72)
curseur.execute("DELETE FROM system_status WHERE date_heure < %s", (limite,))
bdd.commit()

bdd.close()
