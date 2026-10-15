# Model card

> Model card historique v1. Les rapports v2 portent deux modèles et un schéma étendu ; voir `data-contract-v2.md` et `validation/evidence-v2/comparison.json`.

## Usage prévu

Démontrer les mécanismes d’une plateforme MLOps MedTech en entretien : contrôle de données, reproductibilité, évaluation, promotion, API, dérive et rollback. **Aucun usage clinique.** La cible synthétique ne représente pas une maladie validée, une mortalité ni une décision thérapeutique.

## Modèle et entraînement

StandardScaler et LogisticRegression, C=1, solver lbfgs, max_iter=1000. Toutes les variables sont numériques. La standardisation et les coefficients sont exportés au format JSON ; l’inférence réutilise directement les mêmes paramètres. Le seuil est choisi sur validation : seuil le plus élevé dans une grille de 0,05 à 0,80 atteignant 85 % de sensibilité. L’absence de seuil admissible entraîne l’usage de 0,05, avec obligation de satisfaire ensuite les critères test.

## Critères de promotion technique

| Critère sur le jeu de test | Seuil |
|---|---|
| AUC | ≥ 0,78 |
| Sensibilité | ≥ 0,75 |
| Spécificité | ≥ 0,40 |
| Brier | ≤ 0,20 |
| Effectif par tranche d’âge | ≥ 50 observations et ≥ 20 positifs |
| Sensibilité par tranche d’âge | ≥ 0,65 |

Deux tranches : moins de 65 ans et 65 ans ou plus. Ces seuils sont des critères d’exercice prédéfinis, sans justification clinique ou réglementaire. Un faux négatif dans la simulation est comptabilisé, mais aucun effet médical réel ne peut lui être attribué.

## Résultats vérifiés

Cohorte seed 42, 4 000 mesures, test 800 mesures dont 232 positives :

| Mesure | Résultat |
|---|---|
| AUC | 0,88565 |
| IC bootstrap 95 % de l’AUC (200 tirages) | [0,86264 ; 0,90694] |
| Sensibilité | 0,90517 |
| Spécificité | 0,66197 |
| Brier | 0,11814 |
| TP / FN / TN / FP | 210 / 22 / 376 / 192 |
| Sensibilité moins de 65 ans | 0,89262 |
| Sensibilité 65 ans et plus | 0,92771 |
| Seuil choisi | 0,19 |

Le rapport machine inclut une baseline à probabilité constante, les bins de calibration et les effectifs de chaque tranche. Le Brier mesure conjointement calibration et discrimination ; il ne prouve pas une calibration clinique. Les sous-groupes d’âge seuls ne suffisent pas à une analyse d’équité.

## Limites et surveillance

Le générateur et le modèle partagent une structure logistique : les performances ne mesurent pas la difficulté d’un vrai problème médical. Les variables corrélées, données manquantes, artefacts de dispositifs et trajectoires temporelles ne sont pas simulés. Aucun test externe ou prospectif.

Le PSI compare les distributions à celles de train, par dix bins quantiles avec lissage 0,5. Alerte à PSI ≥ 0,2. Le seuil est heuristique et dépend de la taille des lots. Une dérive ne prouve pas une perte de performance ; l’absence de dérive ne prouve pas la sécurité. Les métriques de performance en production nécessiteraient des labels fiables et des analyses de couverture et de délai.

Avant toute application réelle : préciser population et événement, obtenir les autorisations de données, réaliser une validation indépendante et prospective, étudier les sous-groupes pertinents, établir un processus de supervision humaine et consulter les responsables cliniques, qualité et réglementaires. Le projet ne revendique aucune conformité.
