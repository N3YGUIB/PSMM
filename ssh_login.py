import paramiko
import os
import sys

# Etape 1 : recuperer les parametres tapes dans le terminal
adresse_serveur = sys.argv[1]
commande_a_lancer = sys.argv[2]

# Etape 2 : se connecter en SSH
cle = os.path.expanduser("~/.ssh/id_ed25519_monitor")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(adresse_serveur, username="monitor", key_filename=cle)

# Etape 3 : executer la commande et afficher le resultat
entree, sortie, erreur = ssh.exec_command(commande_a_lancer)
resultat = sortie.read().decode()
ssh.close()

print(resultat)
