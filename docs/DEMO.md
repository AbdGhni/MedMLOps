# Démonstration en entretien — 7 minutes

> Scénario historique v1. Il ne démontre pas encore les intégrations de la stack cible ; leur acceptation figure dans `validation/acceptance.md`.

## 0:00 — Problème

« Un modèle performant dans un notebook ne garantit ni reproductibilité ni exploitabilité. MedMLOps montre un parcours vérifiable, de la donnée à la surveillance, avec un modèle synthétique partageable. »

## 0:45 — Pipeline

Exécuter `python -m medmlops.cli demo`. Montrer la seed, les empreintes, les trois partitions et le seuil de validation. Expliquer que le jeu test n’est pas utilisé pour ajuster le scaler ou sélectionner le seuil.

## 2:00 — Qualité

Montrer AUC, sensibilité, spécificité, faux négatifs, Brier et résultats par âge. Expliquer le compromis : le seuil 0,19 conserve une forte sensibilité, avec davantage de faux positifs. Le modèle et le générateur sont logistiques ; ces résultats ne prouvent aucun bénéfice clinique.

## 3:00 — Inférence

Lancer le serveur, connecter l’interface avec le jeton, exécuter une simulation. Montrer le hash de version dans la réponse et le journal agrégé. Une valeur hors bornes est refusée ; aucun nom de patient n’est accepté dans le contrat.

## 4:00 — Surveillance

Exécuter `python -m medmlops.cli monitor` puis `python -m medmlops.cli monitor --shifted`. Montrer les alertes pour fréquence cardiaque et saturation. Dire explicitement qu’une dérive de distribution ne mesure pas la dégradation de précision.

## 5:00 — Rollback

Noter la version active. Entraîner seed 43, promouvoir si accepté, puis revenir à la version précédente avec `rollback`. Exécuter le smoke HTTP et montrer le journal des promotions. Aucun redémarrage du serveur requis.

## 6:00 — Preuves et limites

Exécuter `python scripts/validate.py` : tests, pipeline et batch. Montrer `docs/evidence/validation.json`. Expliquer les limites actuelles : environnement vierge, build conteneur, CI GitHub et parcours navigateur restent à vérifier sur une machine avec ces accès disponibles. Le démonstrateur n’est pas une infrastructure clinique certifiée.
