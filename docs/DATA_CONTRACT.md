# Contrat de données

> Contrat historique v1. Le contrat cible étendu est décrit dans `data-contract-v2.md`.

Schéma : `synthetic-risk-v1`. Une ligne représente un sujet synthétique indépendant, une seule observation avant un événement artificiel. Les colonnes restent dans cet ordre dans tous les pipelines.

| Champ | Unité | Intervalle accepté |
|---|---|---|
| age | années | 18–100 |
| heart_rate | battements/minute | 40–180 |
| systolic_bp | mmHg | 70–220 |
| oxygen_saturation | pourcentage | 80–100 |
| temperature | °C | 35–42 |

Ces intervalles sont des bornes techniques de simulation, pas des références médicales. Hors intervalle, l’API refuse la mesure ; elle ne procède ni à une imputation ni à une extrapolation silencieuse. Les valeurs manquantes, chaînes, booléens, NaN, infinis, champs inconnus et identifiants sont refusés.

API : enveloppe `{"records": [<mesure>, ...]}`. Batch CLI : fichier JSON contenant directement la liste. Au moins une mesure et au plus 1 000. Monitoring : au moins 100 mesures.

## Génération

NumPy `default_rng(seed)` produit les mesures ; chaque variable est tronquée aux bornes. Un tirage Bernoulli dépend d’une fonction logistique explicitement codée. La cible décrit un événement abstrait de risque, sans diagnostic ni horizon clinique revendiqué. La seed, les sources et les hashes permettent de recréer la cohorte à l’identique dans l’environnement vérifié.

Une cohorte standard contient 4 000 lignes ; au moins 500 sont requises pour lancer l’entraînement. Cela ne garantit pas que les sous-groupes auront un effectif suffisant : les critères de qualité peuvent rejeter un petit jeu.

## Partitions et fuite

Partitions stratifiées 60 % train, 20 % validation, 20 % test. Elles sont disjointes, avec tests automatisés d’absence d’intersection et de couverture de la cohorte. Aucun sujet répété dans cette simulation. Un jeu réel longitudinal exigerait des partitions par patient, éventuellement temporelles et par établissement : un simple split de lignes serait insuffisant.

La cible n’entre jamais dans le vecteur de variables. Il n’existe ni jointure ni mesure postérieure à la cible dans ce générateur. Les empreintes de partitions et leurs effectifs sont enregistrés dans le rapport d’expérience.

## Persistance et confidentialité

La cohorte est régénérée en mémoire ; aucun fichier patient n’est distribué. Les modèles, rapports et journaux sont des artefacts synthétiques. Le schéma empêche les identifiants explicites, mais cela ne rendrait pas un ensemble de vraies mesures anonyme : il ne faut pas utiliser de données patients dans ce démonstrateur.
