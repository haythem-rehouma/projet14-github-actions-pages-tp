# Projet 14 — GitHub Actions & GitHub Pages : publier un site en un push


---

## En une phrase

Un **mini-site statique** dont les couleurs sont pilotées par `site/config.json` et **deux workflows GitHub Actions déjà écrits**. Vous clonez, vous poussez, votre site est en ligne. Vous changez une couleur dans `config.json`, vous re-poussez, la page publique se met à jour toute seule en 40 secondes.

Aucun serveur à administrer, aucun budget cloud, **zéro configuration manuelle** sur Pages : le workflow s'occupe de tout.

---

## Ce que vous allez apprendre

- Lire et comprendre un **workflow GitHub Actions** réel (`on:`, `jobs:`, `runs-on:`, `steps:`, `uses:`, `run:`).
- Comprendre le rôle des **permissions** (`pages: write`, `id-token: write`) et de la **concurrence**.
- Publier un site sur **GitHub Pages** gratuitement, avec l'URL `https://<vous>.github.io/<depot>/`.
- Observer un cycle **CI/CD** de bout en bout : commit → push → build → deploy → page publique mise à jour.
- Diagnostiquer et corriger 3 pannes classiques dans un workflow (permissions oubliées, déclencheur mal orthographié, chemin d'artefact erroné).

---

## Démarrage rapide (5 étapes, 10 minutes)

```powershell
# 1) Tester le build en local (facultatif mais rassurant)
python .\outils\build.py
start .\dist\index.html                                  # ouvre la page dans le navigateur

# 2) Creer un depot GitHub PUBLIC (obligatoire pour Pages gratuit)
#    Sur github.com : New repository -> Public -> Sans README ni .gitignore

# 3) Initialiser le depot local et pousser
git init
git branch -M main
git add .
git commit -m "point de depart projet14"
git remote add origin https://github.com/<vous>/projet14-actions-pages.git
git push -u origin main

# 4) Activer Pages en mode Actions
#    Settings -> Pages -> Source = "GitHub Actions"

# 5) Observer le premier deploiement
#    Onglet Actions -> le run "Deployer sur GitHub Pages" doit passer au vert (~40 s)
#    Une fois vert, ouvrir https://<vous>.github.io/projet14-actions-pages/
```

À partir de la, chaque modification de `site/config.json` suivie d'un `git push` **redeploie automatiquement** la page.

---

## Cartographie des documents et dossiers

| Fichier / dossier | À qui | Rôle |
|---|---|---|
| **`00-ENONCE.md`** | **Étudiant** | Sujet complet, concepts, 4 missions, annexes. **À lire en premier.** |
| **[`02-CORRECTION.md`](02-CORRECTION.md)** | **Étudiant** | Solutions détaillées + réponses aux questions de réflexion. À ouvrir après avoir essayé. |
| `site/config.json` | Étudiant (à modifier) | Les couleurs, le titre, l'auteur — la **seule source de vérité** du site |
| `site/src/` | Étudiant (à lire) | Gabarits HTML et CSS avec marqueurs `{{...}}` remplacés par `build.py` |
| `.github/workflows/deployer-pages.yml` | Étudiant (à lire) | Workflow **déjà fonctionnel** qui construit + publie sur Pages |
| `.github/workflows/verifier-config.yml` | Étudiant (à lire) | Workflow **déjà fonctionnel** qui valide `config.json` sur chaque PR |
| `outils/build.py` | Étudiant (à ne pas modifier) | Script Python qui lit `config.json` et produit `dist/` |
| `casses/` | Étudiant (à lire, copier, réparer) | 3 workflows **défectueux** à diagnostiquer et réparer (Mission 3) |
| `.gitignore` | Fourni | Ignore `dist/` (généré à chaque run) |

---

## Prérequis d'environnement

- **Git** installé (`git --version` — n'importe quelle version récente)
- **Python 3.10+** installé (`python --version` — pour tester `build.py` en local)
- **Un compte GitHub** avec un dépôt **public**
- **Un navigateur** pour voir la page publiée

---

## Rappel important

- **GitHub Pages exige un dépôt public** sur un compte gratuit.
- **Le premier déploiement** après activation de Pages peut prendre 2 à 3 minutes (propagation DNS). Les suivants tournent en 40 à 60 secondes.
- **Le dossier `dist/`** n'est jamais commité : il est reconstruit à chaque run par `build.py`.
- **Les modifications** de `outils/build.py`, `site/src/*.template`, ou des workflows dans `.github/workflows/` sont autorisées mais changent le comportement — restez sur `site/config.json` sauf pour la mission 3.

---

## Nettoyage

Ce projet ne consomme rien localement. Pour tout nettoyer :

```powershell
Remove-Item -Recurse -Force .\dist -ErrorAction SilentlyContinue
```

Sur GitHub, pour retirer la publication : **Settings → Pages → Source → None**. Pour supprimer le dépôt : **Settings → General → Danger Zone → Delete this repository**.

---

<p align="center">
  <strong>Cours créé par Dr. Haythem REHOUMA — Développement et déploiement de solutions de données</strong>
</p>
