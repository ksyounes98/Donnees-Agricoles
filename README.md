# Donnees Agricoles

## Description du Projet

### Objectifs
L’objectif de ce projet est d’analyser les données agricoles pour calculer des métriques de risque et de visualiser ces données sur une carte interactive.

### Contexte
Le projet a été réalisé dans le cadre de [précisez le contexte].

### Problématique
Le projet vise à aider les agriculteurs et les décideurs à comprendre les risques associés à différentes parcelles agricoles en fonction de paramètres tels que le rendement, le pH, et la matière organique.

## Données Utilisées

### Sources des Données
Les données proviennent de fichiers CSV tels que :
- `feature_mouse_details.csv`
- `monitoring_daily.csv`
- `histories_columns.csv`
- `sols.csv`

### Description des Données
Les données incluent les paramètres suivants :
1. **Rendement** : Quantité produite par parcelle agricole.
2. **pH** : Niveau d'acidité ou d'alcalinité du sol.
3. **Matière Organique** : Pourcentage de matière organique dans le sol, influençant la fertilité.
4. **Température** : Mesurée quotidiennement pour analyser l'effet climatique.
5. **Humidité du Sol** : Taux d'humidité mesuré pour chaque parcelle.
6. **Type de Sol** : Classification du sol en fonction de ses caractéristiques.
7. **Historique de Production** : Données sur les rendements des années précédentes.
8. **Précipitations** : Quantité de pluie enregistrée sur chaque parcelle.
9. **Pesticides et Fertilisants Utilisés** : Quantité et type d'intrants appliqués.
10. **Autres Paramètres** : 
    - Texture du sol (argile, sable, limon).
    - Drainage du sol.
    - Profondeur racinaire.

### Prétraitement
Les étapes de prétraitement incluent :
1. **Nettoyage des Données** : Suppression ou imputation des valeurs manquantes.
2. **Normalisation** : Mise à l'échelle des données pour garantir une analyse uniforme.
3. **Filtrage** : Élimination des données aberrantes pour améliorer la qualité des analyses.
4. **Fusion des Sources** : Intégration des différentes sources de données en un seul ensemble cohérent.
