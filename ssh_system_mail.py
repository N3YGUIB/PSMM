import paramiko
import mysql.connector
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

# --- Connexion SSH ---
CLE_PRIVEE = os.path.expanduser("~/.ssh/id_ed25519_monitor")
UTILISATEUR_SSH = "monitor"

SERVEURS = {
    "ftp": "172.16.78.161",
    "web": "172.16.78.160",
    "sql": "172.16.78.163"
}

# --- Connexion MySQL ---
HOTE_SQL = "172.16.78.163"
UTILISATEUR_DB = "monitor_app"
MOT_DE_PASSE_DB = "Debian13"
BASE_DB = "supervision"

# --- SMTP Gmail ---
SMTP_HOTE = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EXPEDITEUR = "najib.benkouider@laplateforme.io"
SMTP_MOT_DE_PASSE = "rocv dihv lwke vool"
DESTINATAIRE = "najib.benkouider@laplateforme.io"

# --- SEUILS D'ALERTE (facilement modifiables ici) ---
SEUIL_CPU = 70
SEUIL_DISK = 90
SEUIL_RAM = 80


def convertir_nombre(valeur_str):
    return float(valeur_str.strip().replace(",", "."))


def recuperer_etat_serveur(hote):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=hote, username=UTILISATEUR_SSH, key_filename=CLE_PRIVEE, timeout=10)

    _, stdout_cpu, _ = client.exec_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}'")
    cpu = convertir_nombre(stdout_cpu.read().decode())

    _, stdout_ram, _ = client.exec_command("free | grep Mem | awk '{print ($3/$2) * 100}'")
    ram = convertir_nombre(stdout_ram.read().decode())

    _, stdout_disk, _ = client.exec_command("df / | tail -1 | awk '{print $5}' | tr -d '%'")
    disk = convertir_nombre(stdout_disk.read().decode())

    client.close()
    return cpu, ram, disk


def enregistrer_en_base(nom_serveur, cpu, ram, disk):
    connexion = mysql.connector.connect(
        host=HOTE_SQL, user=UTILISATEUR_DB, password=MOT_DE_PASSE_DB, database=BASE_DB
    )
    curseur = connexion.cursor()
    curseur.execute(
        "INSERT INTO system_status (serveur, date_heure, cpu_percent, ram_percent, disk_percent) "
        "VALUES (%s, %s, %s, %s, %s)",
        (nom_serveur, datetime.now(), cpu, ram, disk)
    )
    connexion.commit()
    curseur.close()
    connexion.close()


def purger_anciennes_donnees():
    limite = datetime.now() - timedelta(hours=72)
    connexion = mysql.connector.connect(
        host=HOTE_SQL, user=UTILISATEUR_DB, password=MOT_DE_PASSE_DB, database=BASE_DB
    )
    curseur = connexion.cursor()
    curseur.execute("DELETE FROM system_status WHERE date_heure < %s", (limite,))
    connexion.commit()
    curseur.close()
    connexion.close()


def verifier_seuils(nom_serveur, cpu, ram, disk):
    """Retourne une liste d'alertes si un seuil est dépassé."""
    alertes = []

    if cpu > SEUIL_CPU:
        alertes.append(f"CPU à {cpu}% (seuil : {SEUIL_CPU}%)")
    if ram > SEUIL_RAM:
        alertes.append(f"RAM à {ram:.1f}% (seuil : {SEUIL_RAM}%)")
    if disk > SEUIL_DISK:
        alertes.append(f"DISQUE à {disk}% (seuil : {SEUIL_DISK}%)")

    return alertes


def envoyer_mail_alerte(nom_serveur, alertes):
    corps = f"Alerte sur le serveur {nom_serveur} :\n\n" + "\n".join(f"- {a}" for a in alertes)

    message = MIMEMultipart()
    message["From"] = SMTP_EXPEDITEUR
    message["To"] = DESTINATAIRE
    message["Subject"] = f"[ALERTE] Ressources critiques sur {nom_serveur}"
    message.attach(MIMEText(corps, "plain"))

    with smtplib.SMTP(SMTP_HOTE, SMTP_PORT) as serveur:
        serveur.starttls()
        serveur.login(SMTP_EXPEDITEUR, SMTP_MOT_DE_PASSE)
        serveur.send_message(message)

    print(f"[MAIL ENVOYÉ] Alerte pour {nom_serveur}.")


if __name__ == "__main__":
    for nom_serveur, ip in SERVEURS.items():
        try:
            cpu, ram, disk = recuperer_etat_serveur(ip)
            enregistrer_en_base(nom_serveur, cpu, ram, disk)
            print(f"[{nom_serveur}] CPU: {cpu}% | RAM: {ram:.1f}% | DISK: {disk}%")

            alertes = verifier_seuils(nom_serveur, cpu, ram, disk)
            if alertes:
                envoyer_mail_alerte(nom_serveur, alertes)

        except Exception as e:
            print(f"[ERREUR] {nom_serveur} ({ip}) : {e}")

    purger_anciennes_donnees()
