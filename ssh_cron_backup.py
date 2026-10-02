import paramiko
import os
from datetime import datetime

# Etape 1 : se connecter en SSH au serveur SQL
cle = os.path.expanduser("~/.ssh/id_ed25519_monitor")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("172.16.78.163", username="monitor", key_filename=cle)

# Etape 2 : lancer la sauvegarde de la base sur le serveur distant
fichier_distant = "/tmp/supervision_dump.sql"
ssh.exec_command("sudo mysqldump supervision > " + fichier_distant, get_pty=True)
ssh.exec_command("sudo chmod 644 " + fichier_distant)

# on attend un peu que la commande se termine avant de recuperer le fichier
import time
time.sleep(2)

# Etape 3 : telecharger le fichier de sauvegarde sur la VM monitor
horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
dossier_backup = os.path.expanduser("~/backups")
os.makedirs(dossier_backup, exist_ok=True)
fichier_local = dossier_backup + "/supervision_" + horodatage + ".sql"

sftp = ssh.open_sftp()
sftp.get(fichier_distant, fichier_local)
sftp.close()

# Etape 4 : supprimer le fichier temporaire sur le serveur distant
ssh.exec_command("rm -f " + fichier_distant)
ssh.close()

print("Sauvegarde enregistree : " + fichier_local)

# Etape 5 : ne garder que les 7 dernieres sauvegardes
liste_fichiers = []
for nom_fichier in os.listdir(dossier_backup):
    if nom_fichier.startswith("supervision_"):
        liste_fichiers.append(dossier_backup + "/" + nom_fichier)

liste_fichiers.sort(key=os.path.getmtime, reverse=True)

fichiers_a_supprimer = liste_fichiers[7:]
for fichier in fichiers_a_supprimer:
    os.remove(fichier)
    print("Ancienne sauvegarde supprimee : " + fichier)
