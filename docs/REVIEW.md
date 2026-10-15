# Revue de livraison

> Revue historique v1. La revue de la spécification étendue est ci-dessous ; elle remplace toute interprétation de complétude de la première livraison.

## Revue v2

Exactitude 4/5 : 19 tests et pipeline réel, limites explicites ; intégrations cible non exécutées. Complétude 2/5 : cœur data/ML/monitoring validé, stack de services exigée absente. Clarté 4/5 : README anglais et backlog avec frontière historique ; aucune capture de dashboard cible. Utilisabilité 3/5 : commandes locales exécutées, installation vierge et Docker bloqués. Concision 4/5 : détail placé dans les guides et résumés courts. Moyenne : 3,4/5.

Priorité : restaurer PyPI/Docker, résoudre et auditer les dépendances, puis exécuter les intégrations et le scénario complet. L’écart de complétude nécessite les accès demandés ; il ne peut pas être corrigé par des mocks. L’utilisateur peut contrôler les sorties réelles dans `validation/evidence-v2`.

## Historique v1

Livraison locale fonctionnelle vérifiée ; livraison intégrale encore incomplète en raison des accès environnementaux.

| Axe | Note / 5 | Preuve et amélioration |
|---|---|---|
| Exactitude | 4 | Preuves exécutées, métriques synthétiques explicitement bornées ; build conteneur non validé |
| Complétude | 3 | Pipeline, API, registre et tests fonctionnent ; GitHub, Docker, environnement vierge et navigateur restent ouverts |
| Clarté | 4 | Guides distincts et états PASS/BLOQUÉ ; une capture du parcours UI améliorerait la présentation |
| Utilisabilité | 3 | Démonstration locale active et archive exportable ; accès réseau et emplacement durable nécessaires pour refaire une installation propre |
| Concision | 4 | README utilisable directement, détails dans les guides ; une vidéo courte manque pour l’entretien |

Moyenne : **3,6/5**. Cette appréciation tient compte de la demande de livraison complète, qui n’est pas encore satisfaite.

Priorités : (1) restaurer les accès d’écriture, PyPI et Docker puis exécuter l’installation isolée et Compose ; (2) publier après réauthentification GitHub et contrôler la CI ; (3) tester et capturer le parcours navigateur. Les deux premiers écarts nécessitent une modification des accès de l’environnement, pas une approbation de code.

Auto-contrôle : les preuves et les limites sont consultables ; aucune fonctionnalité n’est déclarée vérifiée uniquement parce qu’un fichier existe.
