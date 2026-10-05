# Organisation Des Fichiers

## Structure Principale
- `src/cv_checker/` : moteur API et scoring CV.
- `src/synthetic_cv_generator/` : generateur de CV synthetiques.
- `scripts/powershell/` : scripts de lancement operationnel.
- `scripts/python/` : scripts Python d orchestration.
- `data/cv/` : CV entrants, reels, traites, erreurs, synthetiques.
- `data/business/` : fichiers metier source (postes/candidatures).
- `data/db/` : bases SQLite.
- `outputs/` : exports batch et historiques.
- `docs/` : documentation utilisateur et references.
- `deliverables/` : livrables de rendu.

## Dossier CV
- `data/cv/incoming/` : depot des nouveaux CV a scanner.
- `data/cv/processed/<run_name>/` : CV traites et archives par run.
- `data/cv/failed/<run_name>/` : CV en erreur pendant un run.
- `data/cv/real/` : CV reels historiques.
- `data/cv/generated/latest/` : dernier dataset synthetique.
- `data/cv/generated/<run_name>/` : historique des datasets synthetiques.

## Resultats Batch
- `outputs/batch_history/` : historique des sorties horodatees.
- format standard : `batch_results_<run_name>.csv` et `.json`.
- `outputs/latest/batch_results.csv` : dernier CSV produit.
- `outputs/latest/batch_results.json` : dernier JSON produit.

## Commandes Quotidiennes
```powershell
# Traitement standard: prend les PDF dans incoming puis les deplace vers processed
./scripts/powershell/lancer_reception.ps1

# Variante: traiter un sous-dossier incoming specifique
./scripts/powershell/lancer_reception.ps1 -IncomingDir data/cv/incoming/mon_lot -RunName mon_lot

# Generer + tester automatiquement des CV synthetiques (depot incoming + traitement)
./scripts/powershell/generer_et_tester_synthetiques.ps1 -Count 100 -Seed 20260218
```

## Scripts Stables
- `scripts/powershell/lancer_reception.ps1` : workflow pro incoming -> processed/failed.
- `scripts/python/traiter_cv_reception.py` : script Python de traitement reception.
- `scripts/powershell/generer_et_tester_synthetiques.ps1` : test de robustesse sur CV generes.
- `scripts/powershell/lancer_api.ps1` : demarrage API FastAPI.
- `scripts/powershell/lancer_batch_reels.ps1` : batch legacy via endpoint API.
