<a id="top"></a>

# Correction — projet 14 : GitHub Actions + GitHub Pages

> Ce document contient **les solutions complètes** des 4 missions, les explications ligne par ligne des workflows fournis, les réparations des 3 pannes, et les réponses aux questions de réflexion.
>
> **Ne l'ouvrez qu'après avoir vraiment essayé.** Lire la solution avant d'avoir tâtonné, c'est passer à côté de 80 % de l'apprentissage.

---

## Table des matières

- [Mission 1 — Personnaliser config.json](#mission-1--personnaliser-configjson)
- [Mission 2 — Comprendre les workflows fournis + prouver la boucle push → Pages](#mission-2--comprendre-les-workflows-fournis--prouver-la-boucle-push--pages)
- [Mission 3 — Réparation des 3 pannes](#mission-3--reparation-des-3-pannes)
- [Mission 4 — Bonus](#mission-4--bonus)
- [Réponses aux questions de réflexion](#reponses-aux-questions-de-reflexion)
- [Erreurs classiques à éviter](#erreurs-classiques-a-eviter)

---

## Mission 1 — Personnaliser `config.json`

**Exemple de fichier valide :**

```json
{
  "titre": "Portfolio de <votre nom>",
  "sous_titre": "Deploiement automatique via GitHub Actions",
  "couleur_fond": "#7c3aed",
  "couleur_texte": "#f8fafc",
  "couleur_accent": "#22d3ee",
  "auteur": "<Votre Nom>",
  "version": "1.0.0"
}
```

**Points à respecter :**

1. Les 7 clés (`titre`, `sous_titre`, `couleur_fond`, `couleur_texte`, `couleur_accent`, `auteur`, `version`) sont **obligatoires**.
2. Les 3 couleurs doivent respecter le format `#RRGGBB` (6 caractères hexadécimaux après le `#`).
3. Le fichier doit rester un JSON valide : virgule après chaque champ **sauf** le dernier, guillemets doubles partout.

**Validation locale :**

```powershell
python .\outils\build.py
```

Doit afficher `OK dist/index.html genere` et `OK dist/css/style.css genere`. Toute erreur `ERREUR :` arrête le script et bloquera ensuite le workflow GitHub.

**Palette suggérée pour tester la boucle en mission 2 :**

| Couleur | Fond | Texte | Accent |
|---|---|---|---|
| Nuit sombre | `#0f172a` | `#f1f5f9` | `#38bdf8` |
| Violet vibrant | `#7c3aed` | `#f8fafc` | `#22d3ee` |
| Rouge vif | `#dc2626` | `#fef2f2` | `#facc15` |
| Vert forêt | `#16a34a` | `#f0fdf4` | `#fbbf24` |
| Bleu océan | `#0891b2` | `#ecfeff` | `#f472b6` |

---

## Mission 2 — Comprendre les workflows fournis + prouver la boucle push → Pages

### Lecture ligne par ligne de `deployer-pages.yml`

```yaml
name: Deployer sur GitHub Pages          # nom qui apparait dans l'UI Actions
```

Ce nom est purement cosmétique — il aide à repérer le workflow dans l'onglet Actions du dépôt.

```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:
```

**Deux déclencheurs :**

- Automatique dès qu'on pousse sur `main` (le cas normal).
- Manuel via un bouton **Run workflow** dans l'onglet Actions (utile pour re-déployer sans nouveau commit).

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

**Le trio magique de Pages.** Sans ces trois lignes, on obtient `Resource not accessible by integration` au job `deployer` (c'est exactement la panne 1 de la mission 3) :

- `contents: read` — permet à `actions/checkout@v4` de lire le code.
- `pages: write` — autorise `actions/deploy-pages@v4` à publier.
- `id-token: write` — nécessaire pour l'authentification **OIDC** entre le runner et le service Pages.

```yaml
concurrency:
  group: pages
  cancel-in-progress: false
```

Si deux `git push` arrivent presque en même temps, GitHub Actions ne lance **pas** deux déploiements en parallèle sur le même groupe `pages` — les runs s'exécutent l'un après l'autre. `cancel-in-progress: false` = on laisse le run en cours se terminer avant de démarrer le suivant. C'est **crucial** pour Pages : deux publications simultanées produisent des états incohérents.

```yaml
jobs:
  construire:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4                   # 1. recuperer le code
      - uses: actions/setup-python@v5               # 2. installer Python
        with:
          python-version: "3.12"
      - run: python outils/build.py                  # 3. generer dist/
      - uses: actions/upload-pages-artifact@v3       # 4. preparer l'artefact
        with:
          path: dist                                 #    <-- IMPORTANT : dossier a publier
```

Quatre étapes séquentielles. Si l'une échoue, les suivantes ne s'exécutent pas.

```yaml
  deployer:
    needs: construire                                # attend que "construire" reussisse
    environment:
      name: github-pages                             # environnement officiel Pages
      url: ${{ steps.publication.outputs.page_url }} # affiche l'URL dans l'UI
    steps:
      - uses: actions/deploy-pages@v4
        id: publication
```

Le job `deployer` attend explicitement `construire` grâce à `needs:`. À la fin, l'UI GitHub affiche un lien cliquable vers `https://<vous>.github.io/<depot>/`.

### Lecture ligne par ligne de `verifier-config.yml`

```yaml
on:
  pull_request:
    branches: [main]
  push:
    branches-ignore: [main]
```

Se déclenche sur **PR vers `main`** et sur **push vers toute branche sauf `main`**. Le but : valider **avant** que le code ne soit fusionné. Notez qu'on **exclut** `main` du `push:` — sinon on doublerait le travail avec `deployer-pages.yml`.

Le reste des étapes est identique à `deployer-pages.yml` sauf qu'on **ne publie pas** : on se contente de vérifier que `dist/` se génère sans erreur.

### Preuve de la boucle push → Pages

Séquence à reproduire deux fois :

```powershell
# --- Iteration 1 : fond violet ---
# Edite site/config.json : "couleur_fond": "#7c3aed"
git add site/config.json
git commit -m "fond violet"
git push
# Attendre ~40 s -> ouvrir https://<vous>.github.io/<depot>/ -> fond violet

# --- Iteration 2 : fond rouge ---
# Edite site/config.json : "couleur_fond": "#dc2626"
git add site/config.json
git commit -m "fond rouge"
git push
# Attendre ~40 s -> ouvrir la meme URL -> fond rouge
```

**Vérifications à inclure dans le rapport :**

- `git log --oneline` : montre les 2 commits avec leurs SHAs courts.
- Onglet **Actions** : les 2 runs de `Deployer sur GitHub Pages` sont verts.
- Deux **captures d'écran** de la page publique avec les 2 couleurs différentes.
- Sur chaque capture, la **tuile « Commit SHA »** doit correspondre au commit qui a déclenché ce run.

---

## Mission 3 — Réparation des 3 pannes

### Panne 1 — Permissions manquantes

**Diff du correctif dans `.github/workflows/casse-1-permissions-manquantes.yml` :**

```diff
 name: Casse 1 - Permissions manquantes

 on:
   push:
     branches: [main]
   workflow_dispatch:

+permissions:
+  contents: read
+  pages: write
+  id-token: write
+
 concurrency:
   group: pages
   cancel-in-progress: false

 jobs:
   ...
```

**Diagnostic écrit à mettre dans le rapport :**

Sans le bloc `permissions:`, GitHub octroie au workflow uniquement `contents: read` (lecture du code) — pas la permission de **publier** sur Pages. L'action `actions/deploy-pages@v4` réclame explicitement `pages: write` et `id-token: write` (jeton OIDC). D'où l'erreur `Resource not accessible by integration` (`403 Forbidden`) au job `deployer`.

**Règle de sécurité :** on donne **le moins de permissions possible**, mais pas moins. Le principe du **moindre privilège** appliqué au CI/CD.

### Panne 2 — Déclencheur erroné

**Diff du correctif :**

```diff
 name: Casse 2 - Declencheur errone

 on:
-  pushh:
+  push:
     branches: [main]
```

**Diagnostic écrit à mettre dans le rapport :**

GitHub Actions **ne signale pas** les déclencheurs inconnus dans `on:` — il les ignore silencieusement. Un simple `pushh` (avec deux `h`) fait qu'**aucun run** ne se déclenche : on ne voit pas d'erreur, on ne voit **rien du tout** dans l'onglet Actions.

**Comment on découvre la panne ?** On pousse un commit, on va dans Actions, on constate qu'aucun run n'apparaît pour ce workflow. Le seul indice est **l'absence**.

**Astuce anti-piège :** un rapide `Run workflow` (bouton manuel, disponible si `workflow_dispatch:` est présent) vérifie que le workflow lui-même est syntaxiquement valide. Le `workflow_dispatch:` fonctionne indépendamment de `push:`.

### Panne 3 — Chemin d'artefact erroné

**Diff du correctif :**

```diff
       - name: Preparer le dossier a publier
         uses: actions/upload-pages-artifact@v3
         with:
-          path: public
+          path: dist
```

**Diagnostic écrit à mettre dans le rapport :**

`outils/build.py` écrit systématiquement dans `dist/` (constante `DIST = RACINE / "dist"` dans le code Python). Le workflow demandait `path: public` — un dossier qui n'existe pas. D'où :

```
Error: Path does not exist: ./public
```

`actions/upload-pages-artifact@v3` vérifie l'existence du dossier avant de créer l'artefact et échoue immédiatement si le chemin est faux. La bonne pratique : **toujours faire pointer le workflow vers le dossier exact que produit le script de build**.

---

## Mission 4 — Bonus

### 4.a — Badge d'état dans `README.md`

Dans le `README.md` de votre dépôt GitHub (à la racine, pas dans le dossier `projet14-github-actions-pages-tp/` du cours), ajoutez :

```markdown
# Mon site portfolio

![Deploy](https://github.com/<vous>/<depot>/actions/workflows/deployer-pages.yml/badge.svg)

Site publie : https://<vous>.github.io/<depot>/
```

Le badge devient **vert** si le dernier run est passé, **rouge** sinon. Il se met à jour tout seul.

### 4.b — PR de test avec `config.json` invalide

```powershell
git checkout -b test-config-cassee
# Editer site/config.json et remplacer "couleur_fond": "#0f172a" par "couleur_fond": "rouge"
git add site/config.json
git commit -m "test : couleur invalide"
git push -u origin test-config-cassee
# Puis sur GitHub : ouvrir une PR de test-config-cassee vers main
```

Le workflow `Verifier la configuration` va se déclencher, `build.py` va crier :

```
ERREUR : couleur_fond doit etre au format #RRGGBB (recu : 'rouge')
```

La PR affiche un carré rouge et le bouton **Merge pull request** est bloqué si vous avez configuré la protection de branche (**Settings → Branches → Add rule → Require status checks to pass**).

### 4.c — Workflow avec secret

`.github/workflows/notifier.yml` :

```yaml
name: Notifier une URL

on:
  workflow_dispatch:

jobs:
  notifier:
    runs-on: ubuntu-latest
    steps:
      - name: Ping du webhook
        env:
          URL: ${{ secrets.URL_WEBHOOK }}
        run: |
          curl -X POST "$URL" \
            -H "Content-Type: application/json" \
            -d '{"texte":"Un utilisateur a declenche notifier.yml"}'
```

Le secret `URL_WEBHOOK` est défini dans **Settings → Secrets and variables → Actions → New repository secret**. Il **n'apparaîtra jamais** dans les logs : GitHub masque automatiquement toute valeur qui correspond à un secret.

---

## Réponses aux questions de réflexion

**1. `on: push` sans `branches:` — quand se déclenche-t-il ?**

Il se déclenche à chaque push **sur toutes les branches**. C'est rarement souhaitable : un `git push` sur une branche de feature en cours de développement va lancer un déploiement Pages en production. Toujours limiter avec `branches: [main]` ou une liste explicite.

**2. Pourquoi `id-token: write` est-il nécessaire pour Pages ? À quoi sert le jeton OIDC ?**

`actions/deploy-pages@v4` utilise **OIDC (OpenID Connect)** pour prouver au service Pages que la requête vient bien d'un run GitHub Actions autorisé, sans utiliser de mot de passe ni de PAT (Personal Access Token). Le jeton OIDC est **éphémère** (durée de vie limitée au run) et signé par GitHub — plus sûr qu'un secret statique. `id-token: write` autorise le runner à **générer** ce jeton pour ce workflow.

**3. Deux pushes simultanés sur `main` — que fait `concurrency` ?**

Sans `concurrency`, GitHub lance **deux workflows en parallèle**. Le premier finit son upload d'artefact, le deuxième démarre son propre upload, et Pages peut recevoir **les deux publications dans le désordre** → l'ordre final n'est plus garanti. Avec `concurrency: { group: pages, cancel-in-progress: false }`, les deux runs sont **sérialisés** : le deuxième attend que le premier se termine. `cancel-in-progress: true` aurait un autre effet — annuler le run en cours dès qu'un nouveau démarre, utile pour un rebuild ultra-rapide mais dangereux pour Pages.

**4. Un secret peut-il apparaître dans les logs ?**

GitHub **masque automatiquement** toute valeur enregistrée comme secret : elle apparaît sous forme de `***` dans les logs. **Mais** si vous transformez le secret (par exemple `echo "$SECRET" | base64`), le masquage ne s'applique plus à la valeur transformée. Règle : ne **jamais** transformer un secret dans un `run:`, l'utiliser tel quel via `env:` et le passer directement à l'outil (ici `curl`).

**5. Pourquoi garder les deux workflows `deployer-pages.yml` et `verifier-config.yml` ?**

- `deployer-pages.yml` **publie** sur `main` : c'est le workflow de **livraison**. Il ne tourne **qu'après** un merge.
- `verifier-config.yml` **valide** sur les branches de feature et sur les PR : c'est le workflow de **prévention**. Il empêche un `config.json` cassé d'atteindre `main`.

Les deux forment un **filet à deux couches** : la vérification bloque en amont, le déploiement livre en aval. C'est le pattern **CI (Continuous Integration)** + **CD (Continuous Deployment)**.

**6. Que se passerait-il si `build.py` créait un fichier `historique.log` ?**

Rien de durable. Le runner est une **VM éphémère détruite à la fin du run**. Le fichier disparaîtrait avec la VM. Pour conserver un historique entre runs, il faudrait le **committer dans le dépôt** (bof, pollue le repo), le **stocker dans un artefact** avec `actions/upload-artifact` (durée de vie 90 jours max), ou l'**envoyer vers un service externe** (S3, Postgres, etc.).

---

## Erreurs classiques à éviter

| Symptôme | Cause probable | Solution |
|---|---|---|
| `Resource not accessible by integration` | Bloc `permissions:` absent ou incomplet | Ajouter `pages: write` + `id-token: write` |
| Aucun run ne se déclenche | Faute de frappe dans `on:` (`pushh:`, `pull_requests:`) | Vérifier l'orthographe des clés YAML |
| `Path does not exist: ./xxx` | Chemin dans `upload-pages-artifact.path:` ne correspond pas au dossier de sortie de `build.py` | Vérifier `path:` = `dist` |
| Page publiée montre l'ancien contenu | Cache navigateur | Ctrl+Shift+R pour un rechargement dur |
| Le premier déploiement met > 5 min | Propagation DNS de GitHub Pages | Normal la première fois, ~40 s ensuite |
| Workflow rouge à l'étape `python outils/build.py` | `config.json` invalide | Lancer `python .\outils\build.py` en local pour voir l'erreur exacte |
| Le workflow tourne mais l'URL renvoie 404 | Source Pages toujours en mode « Deploy from a branch » | Passer en **GitHub Actions** dans Settings → Pages |
| Deux runs Pages en même temps produisent un contenu incohérent | `concurrency:` absent | Ajouter le bloc `concurrency: { group: pages }` |

---

## Comment le prof évalue votre travail

Le prof ouvre trois onglets :

1. **Votre dépôt GitHub** : structure des fichiers, contenu de `config.json`, présence de `.github/workflows/` avec au moins les 3 workflows corrigés (les originaux `deployer-pages.yml` et `verifier-config.yml` + les 3 pannes réparées).
2. **Votre onglet Actions** : au moins 2 runs verts de `Deployer sur GitHub Pages` (mission 2), plus les runs de la mission 3 (avant/après réparation).
3. **Votre site publié** : `https://<vous>.github.io/<votre-depot>/` — doit s'afficher avec vos couleurs personnalisées et un SHA récent.

Puis il lit **votre `RAPPORT.md`** :

- Il compte les captures d'écran (2 pour la mission 2, 6 pour la mission 3 : avant/après × 3 pannes).
- Il vérifie que les diagnostics des pannes sont écrits **avec vos mots**, pas copiés depuis ce document.
- Il note la qualité des réponses aux 6 questions de réflexion.

Un rapport propre + un dépôt bien structuré = **plein pot facile**. La difficulté n'est pas technique, elle est dans **la rigueur de la démonstration**.

---

<p align="center">
  <strong>Cours créé par Dr. Haythem REHOUMA — Développement et déploiement de solutions de données</strong>
</p>
