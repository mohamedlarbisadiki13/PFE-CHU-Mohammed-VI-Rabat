"""
run_simulation.py
=================
Pipeline bim2sim v0.3.0 → EnergyPlus 9.4.0
CHU Mohammed VI de Rabat — IGH (4 blocs, surface totale ~42 510 m²)

Usage:
    python run_simulation.py --ifc path/to/model.ifc --config config_teaser.json

Auteur : [Votre Nom] — PFE 2025-2026
"""

import argparse
import json
import logging
import os
from pathlib import Path

# bim2sim imports
import bim2sim
from bim2sim import Project
from bim2sim.plugins.PluginEnergyPlus.bim2sim_energyplus import PluginEnergyPlus
from bim2sim.tasks.common import LoadIFC, CheckIFC, CreateElements
from bim2sim.tasks.bps import (
    CreateSpaceBoundaries,
    EnrichMaterial,
    EnrichUseConditions,
    WeatherFilePath,
    RunEnergyPlusSimulation,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_bim2sim_pipeline(ifc_path: str, config: dict, output_dir: str = "outputs"):
    """
    Exécute le pipeline bim2sim complet :
      1. Chargement et vérification IFC
      2. Création des éléments BIM
      3. Génération des Space Boundaries 2B
      4. Enrichissement matériaux (depuis config_teaser.json)
      5. Enrichissement conditions d'usage (12 archétypes ASHRAE 170-2017)
      6. Affectation fichier météo TMYx Rabat-Salé
      7. Lancement simulation EnergyPlus
    """
    log.info("=== Démarrage pipeline bim2sim ===")
    log.info(f"Fichier IFC     : {ifc_path}")
    log.info(f"Moteur          : EnergyPlus {config.get('energyplus_version', '9.4.0')}")
    log.info(f"Fichier météo   : {config.get('weather_file', 'non défini')}")

    os.makedirs(output_dir, exist_ok=True)

    # --- Initialisation projet bim2sim ---
    project = Project.create(
        project_folder=output_dir,
        ifc_path=ifc_path,
        plugin=PluginEnergyPlus,
    )

    # --- Paramètres simulation ---
    project.sim_settings.weather_file_path = config["weather_file"]
    project.sim_settings.run_full_year = True
    project.sim_settings.simulation_mode = "ILAS"  # Ideal Loads Air System

    # --- Exécution du pipeline de tâches ---
    tasks = [
        LoadIFC,
        CheckIFC,
        CreateElements,
        CreateSpaceBoundaries,   # Space Boundaries 2B
        EnrichMaterial,          # Matériaux depuis JSON TEASER
        EnrichUseConditions,     # 12 archétypes + profils horaires 24h
        WeatherFilePath,
        RunEnergyPlusSimulation,
    ]

    for task_cls in tasks:
        log.info(f"  → Tâche : {task_cls.__name__}")
        task = task_cls(project)
        task.run()

    log.info("=== Simulation terminée ===")
    log.info(f"Résultats dans : {output_dir}/")
    return output_dir


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline bim2sim → EnergyPlus pour CHU Mohammed VI de Rabat"
    )
    parser.add_argument("--ifc", required=True, help="Chemin vers le fichier IFC4")
    parser.add_argument(
        "--config", default="config_teaser.json", help="Fichier de configuration JSON"
    )
    parser.add_argument("--output", default="outputs", help="Dossier de sortie")
    args = parser.parse_args()

    if not Path(args.ifc).exists():
        raise FileNotFoundError(f"Fichier IFC introuvable : {args.ifc}")

    config = load_config(args.config)
    log.info(f"Configuration chargée : {len(config['thermal_archetypes'])} archétypes thermiques")

    run_bim2sim_pipeline(
        ifc_path=args.ifc,
        config=config,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
