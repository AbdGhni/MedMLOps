# État de validation — 14 octobre 2026

> Historique du prototype v1. L’état actuel de la spécification étendue est dans `Progress.md` et `validation/evidence-v2`. Les résultats Flask/SQLite ne valident pas FastAPI/MLflow/PostgreSQL.

Les preuves brutes sont dans [evidence/](evidence/). Les affirmations ci-dessous concernent des exécutions réelles dans cette session.

| Parcours | État | Preuve ou limite |
|---|---|---|
| Entraînement et évaluation | PASS | `evidence/demo.json`, partitions 2400/800/800 |
| Reproductibilité seed et parité | PASS | Test de même version et parité ≤ 1e-12 |
| Critères de rejet | PASS | Test métrique dégradée, promotion refusée |
| Promotion et rollback | PASS | Deux seeds, changement de version puis retour |
| Contrat, NaN, booléens, bornes | PASS | Tests de validation adversariale |
| Authentification et erreurs sans valeurs | PASS | 401, 422 et sentinelle confidentielle absente |
| Intégrité d’artefact | PASS | JSON modifié → readiness et inférence 503 |
| Audit concurrent | PASS | 20 écritures sur quatre threads |
| Monitoring | PASS | Lot stable sans alerte ; lot décalé avec alerte |
| Batch et protection d’écrasement | PASS | Commande exécutée, refus d’un fichier existant |
| API HTTP réelle | PASS | Readiness et inférence via urllib, serveur loopback |
| Latence locale | MESURÉE | `evidence/http-benchmark.json` ; aucun SLA revendiqué |
| Page HTML | PASS HTTP | Route et contenu testés ; interactions navigateur non vérifiées |
| Installation depuis zéro | BLOQUÉE | PyPI inaccessible, dépendances système utilisées |
| Compose | CONFIG VALIDE | `docker compose config --quiet` réussit avec jeton défini |
| Image et conteneurs | BLOQUÉS | Moteur Docker absent ; verrou `.docker/buildx/.lock` refusé |
| Publication et CI GitHub | BLOQUÉES | `gh auth status` indique un jeton invalide |
| Placement durable | BLOQUÉ | Écriture refusée dans home/Projects ; dossier temporaire utilisé |

## Tests

12 tests `unittest` passent. Ils vérifient les critères ci-dessus ainsi que la gestion des corps trop grands, du JSON invalide, du registre vide et des jetons trop courts. Le script de validation retourne 0 uniquement si tests, démonstration et batch réussissent. Le fichier `validation.json` donne plateforme, date UTC et codes de sortie.

Les tests sont exécutables hors ligne lorsque les dépendances sont installées. Une première relance dans le sandbox a rencontré un refus d’accès lié aux permissions restrictives des répertoires `tempfile`. Les tests utilisent désormais des dossiers dédiés avec permissions héritées dans `runtime/tests` et vérifient le chemin avant nettoyage. La dernière exécution complète passe.

## Ce qui manque pour déclarer la livraison complète

1. Copier l’archive dans un emplacement durable et installer les dépendances dans un environnement vierge.
2. Exécuter le build et le parcours Compose sur un moteur Docker fonctionnel.
3. Vérifier les interactions et le rendu dans un navigateur desktop et mobile.
4. Rétablir GitHub, publier le dépôt et obtenir une exécution CI réussie.

Ces points restent ouverts. La création des Dockerfiles et du workflow ne vaut pas validation de leur exécution.
