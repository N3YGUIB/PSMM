import paramiko
import os
import requests
from config import *

cle = os.path.expanduser("~/.ssh/id_ed25519_monitor")

serveurs = {
    "ftp": "172.16.78.161",
    "web": "172.16.78.160",
    "sql": "172.16.78.163"
}

url_webhook = WEBHOOK_CHAT

# Etape 1 : recuperer l'etat de chaque serveur
message = "Etat des serveurs :\n\n"

for nom_serveur in serveurs:
    ip = serveurs[nom_serveur]

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username="monitor", key_filename=cle)

    entree, sortie, erreur = ssh.exec_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'")
    cpu = sortie.read().decode().strip().replace(",", ".")

    entree, sortie, erreur = ssh.exec_command("free | grep Mem | awk '{print ($3/$2) * 100}'")
    ram = sortie.read().decode().strip().replace(",", ".")

    entree, sortie, erreur = ssh.exec_command("df / | tail -1 | awk '{print $5}' | tr -d '%'")
    disk = sortie.read().decode().strip()

    ssh.close()

    message = message + nom_serveur + " -> CPU: " + cpu + "%  RAM: " + ram + "%  DISK: " + disk + "%\n"

# Etape 2 : envoyer le message dans le Space Google Chat
donnees = {"text": message}
reponse = requests.post(url_webhook, json=donnees)

print("Message envoye, code de reponse : " + str(reponse.status_code))
