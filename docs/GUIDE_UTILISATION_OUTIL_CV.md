# Guide Utilisation Outil CV

## Objectif
Cet outil lit des CV PDF, extrait les informations candidat, calcule un score metier et produit un fichier `batch_results.csv` exploitable au quotidien.

## Organisation Des Dossiers
- `data/cv/incoming/` : dossier de depot des nouveaux CV a analyser.
- `data/cv/processed/<run_name>/` : archive automatique des CV traites avec succes.
- `data/cv/failed/<run_name>/` : archive des CV en erreur.
- `outputs/batch_history/` : historique de tous les batch CSV et JSON.
- `outputs/latest/` : derniere sortie disponible immediatement.
- `data/cv/real/` : stock historique de CV reels.
- `data/cv/generated/` : CV synthetiques de test.

## Flux Professionnel Recommande
1. Deposer les CV recus dans `data/cv/incoming/`.
2. Lancer le traitement:
```powershell
./scripts/powershell/lancer_reception.ps1
```
3. Ouvrir le resultat principal:
`outputs/latest/batch_results.csv`
4. Verifier les alertes dans la colonne `warnings`.
5. Les PDF traites sont automatiquement deplaces vers `data/cv/processed/<run_name>/`.

## Commandes Utiles
- Traitement d un sous lot:
```powershell
./scripts/powershell/lancer_reception.ps1 -IncomingDir data/cv/incoming/lot_20260218 -RunName lot_20260218
```
- Generation et test synthetique:
```powershell
./scripts/powershell/generer_et_tester_synthetiques.ps1 -Count 100 -Seed 20260218
```
- Demarrage API (mode endpoint):
```powershell
./scripts/powershell/lancer_api.ps1
```

## Resultats Produits
- `outputs/batch_history/batch_results_<run_name>.csv`
- `outputs/batch_history/batch_results_<run_name>.json`
- `outputs/latest/batch_results.csv`
- `outputs/latest/batch_results.json`

## Description Du CSV
Le dictionnaire des colonnes est fourni dans:
- `docs/references/batch_results_columns_guide.csv`
- `docs/references/batch_results_warnings_guide.csv`

## Bonnes Pratiques
- Deposer uniquement des PDF dans `incoming`.
- Traiter un lot puis verifier `warnings` avant decision finale.
- Conserver `outputs/batch_history/` pour l audit des traitements.
- Utiliser les CV synthetiques pour valider les evolutions avant production.

