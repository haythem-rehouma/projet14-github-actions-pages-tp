"""Constructeur du site statique.

Lit :
  - site/config.json
  - site/src/index.html.template
  - site/src/css/style.css.template

Ecrit :
  - dist/index.html
  - dist/css/style.css

Chaque marqueur {{CLE}} est remplace par la valeur correspondante :
  - Cles de config.json en majuscules       (ex: {{TITRE}}, {{COULEUR_FOND}})
  - Metadonnees GitHub Actions du run       (ex: {{COMMIT_SHA}}, {{NUMERO_RUN}}, {{BRANCHE}})
  - Date de build                            (ex: {{DATE_BUILD}})

Toutes les valeurs GitHub Actions sont lues depuis les variables
d'environnement GITHUB_SHA / GITHUB_RUN_NUMBER / GITHUB_REF_NAME
(automatiquement fournies par les runners GitHub). En execution locale,
si ces variables sont absentes, on utilise des valeurs "local-*".
"""

import datetime
import json
import os
import pathlib
import re
import shutil
import sys

RACINE = pathlib.Path(__file__).resolve().parents[1]
SITE = RACINE / "site"
DIST = RACINE / "dist"

CLES_ATTENDUES = {
    "titre", "sous_titre",
    "couleur_fond", "couleur_texte", "couleur_accent",
    "auteur", "version",
}

FORMAT_COULEUR = re.compile(r"^#[0-9a-fA-F]{6}$")


def charger_config():
    fichier = SITE / "config.json"
    if not fichier.exists():
        sys.exit("ERREUR : site/config.json est introuvable.")
    try:
        return json.loads(fichier.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        sys.exit("ERREUR : site/config.json est mal forme (%s)." % err)


def valider(config):
    manquantes = CLES_ATTENDUES - set(config.keys())
    if manquantes:
        sys.exit("ERREUR : cles manquantes dans config.json : %s"
                 % ", ".join(sorted(manquantes)))

    for cle in ("couleur_fond", "couleur_texte", "couleur_accent"):
        val = str(config[cle])
        if not FORMAT_COULEUR.match(val):
            sys.exit("ERREUR : %s doit etre au format #RRGGBB (recu : %r)"
                     % (cle, val))


def variables(config):
    """Compose le dictionnaire {marqueur: valeur} pour la substitution."""
    variables_run = {
        "COMMIT_SHA": (os.environ.get("GITHUB_SHA", "local-non-commit")[:7]),
        "NUMERO_RUN": os.environ.get("GITHUB_RUN_NUMBER", "local"),
        "BRANCHE": os.environ.get("GITHUB_REF_NAME", "local"),
        "DATE_BUILD": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }
    variables_config = {cle.upper(): str(val) for cle, val in config.items()}
    return {**variables_config, **variables_run}


def substituer(gabarit, variables):
    def remplace(match):
        cle = match.group(1)
        if cle not in variables:
            sys.exit("ERREUR : le gabarit reference {{%s}} mais aucune valeur "
                     "n'est fournie." % cle)
        return variables[cle]
    return re.sub(r"\{\{(\w+)\}\}", remplace, gabarit)


def construire():
    config = charger_config()
    valider(config)
    vars_ = variables(config)

    if DIST.exists():
        shutil.rmtree(DIST)
    (DIST / "css").mkdir(parents=True)

    html_gabarit = (SITE / "src" / "index.html.template").read_text(encoding="utf-8")
    css_gabarit = (SITE / "src" / "css" / "style.css.template").read_text(encoding="utf-8")

    (DIST / "index.html").write_text(substituer(html_gabarit, vars_), encoding="utf-8")
    (DIST / "css" / "style.css").write_text(substituer(css_gabarit, vars_), encoding="utf-8")

    print("OK  dist/index.html      genere")
    print("OK  dist/css/style.css   genere")
    print("--- Substitutions appliquees ---")
    for cle, val in vars_.items():
        if len(val) > 60:
            val = val[:57] + "..."
        print("  {{%s}} -> %s" % (cle, val))


if __name__ == "__main__":
    construire()
