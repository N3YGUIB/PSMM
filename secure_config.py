import os

# fichiers a ne surtout pas modifier
exclure = ["config.py", "config_exemple.py", "secure_config.py", "update_ip.py"]

# liste des remplacements : (texte a chercher, texte de remplacement)
remplacements = [
    ('host="172.16.78.163"', 'host=DB_HOTE'),
    ('user="monitor_app"', 'user=DB_UTILISATEUR'),
    ('password="Debian13"', 'password=DB_MOT_DE_PASSE'),
    ('database="supervision"', 'database=DB_NOM'),
    ('message["From"] = "[ADRESSE@MAIL.COM]"', 'message["From"] = SMTP_EXPEDITEUR'),
    ('message["To"] = "[ADRESSE@MAIL.COM]"', 'message["To"] = SMTP_DESTINATAIRE'),
    ('serveur_smtp.login("[ADRESSE@MAIL.COM]", "[key_api_mail]")', 'serveur_smtp.login(SMTP_EXPEDITEUR, SMTP_MOT_DE_PASSE)'),
    ('url_webhook = "[URL_WEBHOOK]"', 'url_webhook = WEBHOOK_CHAT'),
]

dossier = os.path.expanduser("~")

for nom_fichier in os.listdir(dossier):

    if not nom_fichier.endswith(".py"):
        continue
    if nom_fichier in exclure:
        continue

    chemin = os.path.join(dossier, nom_fichier)

    fichier = open(chemin, "r", encoding="utf-8")
    contenu = fichier.read()
    fichier.close()

    contenu_original = contenu

    for ancien, nouveau in remplacements:
        contenu = contenu.replace(ancien, nouveau)

    if contenu != contenu_original:

        # ajouter l'import de config juste apres les autres imports, si pas deja fait
        if "from config import" not in contenu:
            lignes = contenu.split("\n")
            index_insertion = 0
            for i in range(len(lignes)):
                if lignes[i].startswith("import ") or lignes[i].startswith("from "):
                    index_insertion = i + 1
            lignes.insert(index_insertion, "from config import *")
            contenu = "\n".join(lignes)

        fichier = open(chemin, "w", encoding="utf-8")
        fichier.write(contenu)
        fichier.close()

        print(nom_fichier + " : modifie.")
    else:
        print(nom_fichier + " : rien a changer.")

