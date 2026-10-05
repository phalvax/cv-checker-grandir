# Programmes Stables

Ce dossier contient uniquement les scripts d exploitation quotidienne.

## Workflow Recommande
1. Deposer les nouveaux CV PDF dans `data/cv/incoming/`.
2. Lancer `./scripts/powershell/lancer_reception.ps1`.
3. Recuperer le resultat dans `outputs/latest/batch_results.csv`.
4. Les CV sont archives automatiquement dans `data/cv/processed/<run_name>/`.

## Scripts Disponibles
- `lancer_reception.ps1` : lance le traitement pro incoming -> processed/failed.
- `traiter_cv_reception.py` : version Python directe du traitement incoming.
- `generer_et_tester_synthetiques.ps1` : genere des CV synthetiques, les depose puis les traite.
- `lancer_api.ps1` : demarre l API FastAPI.
- `lancer_batch_reels.ps1` : batch legacy via endpoint API.

## Sorties
- Historique: `outputs/batch_history/batch_results_<run_name>.csv` et `.json`.
- Dernier run: `outputs/latest/batch_results.csv` et `.json`.

