# Runbook

> Guide du prototype v1. Pour le noyau v2, consulter `runbooks/windows-core.md`. Toute action de push par l’agent nécessite une autorisation explicite de l’utilisateur.

## Démarrer le laboratoire

Installer les dépendances et lancer `python -m medmlops.cli demo`. Le pipeline entraîne, évalue et promeut si les critères passent. Définir `MEDMLOPS_API_TOKEN` à une valeur aléatoire d’au moins 16 caractères, puis lancer `python -m medmlops.cli serve`. Valeurs par défaut : loopback, port 8000 et dossier `runtime`.

Éviter `--host 0.0.0.0` hors d’un réseau de conteneur maîtrisé. Le serveur fourni ne convient pas à une exploitation clinique ou publique.

Dans la session de construction, le serveur déjà démarré utilise le jeton de démonstration **`local-synthetic-demo-token-2026`**. Ce jeton public de laboratoire ne doit jamais être réutilisé en production ; il n’est pas une valeur par défaut du code.

## API

| Méthode et route | Protection | Réponse |
|---|---|---|
| GET / | publique | Interface locale |
| GET /health/live | publique | 200 si processus répond |
| GET /health/ready | publique | 200 si modèle actif vérifié, sinon 503 |
| GET /api/status | Bearer | Registre, rapports et derniers 100 événements |
| POST /api/predict | Bearer | Version, probabilités, flags, seuil, latence |
| POST /api/monitor | Bearer | Version, PSI, alerte par variable et globale |

Codes : 401 jeton absent ou incorrect ; 422 contrat de données invalide ; 400 JSON invalide ; 413 corps supérieur à 1 Mio ; 503 modèle absent ou corrompu ; 500 erreur interne générique. L’API ne renvoie pas les détails d’exception ni les valeurs fautives.

Exemple PowerShell :

```powershell
$body = @{records=@(@{age=68;heart_rate=105;systolic_bp=110;oxygen_saturation=94;temperature=38})} | ConvertTo-Json -Depth 5
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/predict -ContentType application/json -Headers @{Authorization="Bearer $env:MEDMLOPS_API_TOKEN"} -Body $body
```

## Promouvoir et revenir en arrière

1. Enregistrer la version active avec `python -m medmlops.cli status`.
2. Exécuter `python -m medmlops.cli train --seed 43` et consulter le rapport.
3. Promouvoir avec `python -m medmlops.cli promote <nouvelle-version>`.
4. Vérifier `/health/ready`, exécuter `scripts/http_smoke.py` et contrôler la version renvoyée.
5. Revenir à l’ancienne version acceptée avec `python -m medmlops.cli rollback <ancienne-version>`.

L’API charge le pointeur actif à chaque requête : aucune interruption n’est nécessaire. Une requête déjà commencée peut terminer avec la version précédente ; chaque réponse nomme la version réellement utilisée. Les promotions sont transactionnelles avec leur événement d’audit. Les fichiers anciens restent disponibles.

## Réagir à une alerte de dérive

Exécuter `python -m medmlops.cli monitor --shifted` pour un incident simulé. En cas d’alerte réelle dans une future adaptation, vérifier d’abord les unités, le contrat, les dispositifs et la population ; demander une évaluation avec des labels fiables. Une dérive seule ne justifie ni réentraînement automatique ni décision clinique. Le projet ne réentraîne pas automatiquement sur des entrées API.

## Sauvegarde et incidents

Arrêter les écritures et sauvegarder l’ensemble du dossier `runtime`, y compris `platform.sqlite` et `models`. Restaurer les deux ensemble, vérifier readiness et exécuter un smoke test. Cette procédure de sauvegarde est documentée mais n’a pas fait l’objet d’un exercice automatisé de restauration.

Si readiness renvoie 503, ne pas modifier le JSON actif : choisir un ancien modèle vérifié et le promouvoir. Si le disque est plein ou non accessible, l’API échoue explicitement au lieu de confirmer une prédiction sans audit. Le journal local n’est pas un mécanisme de non-répudiation.

## Publier sur GitHub

Le dépôt local est préparé. Après restauration de l’accès GitHub, depuis une copie située dans un emplacement durable :

```powershell
gh auth login --hostname github.com
gh repo create MedMLOps --private --source . --remote origin --push
gh run list
```

Ne publier que les sources et preuves synthétiques. `.gitignore` exclut `.env`, les environnements et `runtime`. Le workflow effectue les tests, le pipeline, le build Docker, Compose et le smoke HTTP. Une CI non exécutée n’est pas une CI verte. En cas d’échec, consulter les logs et corriger avant de présenter la livraison comme validée.
