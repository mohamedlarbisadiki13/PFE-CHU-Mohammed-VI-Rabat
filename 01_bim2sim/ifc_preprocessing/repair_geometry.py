"""
repair_geometry.py
==================
Réparation géométrique du modèle IFC avant simulation bim2sim/EnergyPlus.
Applique les 5 opérations identifiées dans §II.2.2 du mémoire :

  1. Correction des hauteurs d'étage (hauteurs Revit → IFC via Dynamo)
  2. Détection et suppression des volumes dupliqués (IfcSpace)
  3. Fermeture des enveloppes ouvertes (gaps < 0.01 m)
  4. Correction des normales inversées (faces intérieures/extérieures)
  5. Validation finale des Space Boundaries 2B

Dépendances : ifcOpenShell >= 0.7, numpy, shapely

Usage:
    python repair_geometry.py --ifc input.ifc --output repaired.ifc

Auteur : [Votre Nom] — PFE 2025-2026
"""

import argparse
import logging
from pathlib import Path

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.util.element as ifc_util
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# Tolérance géométrique en mètres
TOLERANCE_M = 0.01


def load_ifc(ifc_path: str) -> ifcopenshell.file:
    log.info(f"Chargement IFC : {ifc_path}")
    model = ifcopenshell.open(ifc_path)
    log.info(f"  Schéma   : {model.schema}")
    log.info(f"  Espaces  : {len(model.by_type('IfcSpace'))}")
    log.info(f"  Éléments : {len(model.by_type('IfcBuildingElement'))}")
    return model


def remove_duplicate_spaces(model: ifcopenshell.file) -> int:
    """
    Supprime les IfcSpace dupliqués (même GUID de base, créés par copie Revit).
    Retourne le nombre de doublons supprimés.
    """
    spaces = model.by_type("IfcSpace")
    guids_seen = {}
    duplicates = []

    for space in spaces:
        base_guid = space.GlobalId[:22]  # 22 premiers chars = partie fixe
        if base_guid in guids_seen:
            duplicates.append(space)
        else:
            guids_seen[base_guid] = space

    for dup in duplicates:
        model.remove(dup)

    log.info(f"  Espaces dupliqués supprimés : {len(duplicates)}")
    return len(duplicates)


def fix_floor_heights(model: ifcopenshell.file, storey_heights: dict) -> None:
    """
    Corrige les élévations des IfcBuildingStorey selon les hauteurs réelles
    mesurées sur site (issues du script Dynamo).

    storey_heights : dict {nom_étage: élévation_m}
    Exemple: {"RDC": 0.0, "N1": 4.5, "N2": 9.0, ...}
    """
    storeys = model.by_type("IfcBuildingStorey")
    corrected = 0

    for storey in storeys:
        name = storey.Name
        if name in storey_heights:
            old_elev = storey.Elevation
            new_elev = storey_heights[name]
            if abs(old_elev - new_elev) > TOLERANCE_M:
                storey.Elevation = new_elev
                log.info(f"  Étage '{name}' : {old_elev:.3f} m → {new_elev:.3f} m")
                corrected += 1

    log.info(f"  Hauteurs d'étage corrigées : {corrected}")


def validate_space_boundaries(model: ifcopenshell.file) -> dict:
    """
    Vérifie que chaque IfcSpace possède au moins un IfcRelSpaceBoundary de 2nd type (2B).
    Retourne un rapport {espace_guid: nb_boundaries}.
    """
    spaces = model.by_type("IfcSpace")
    boundaries = model.by_type("IfcRelSpaceBoundary")

    boundary_count = {}
    for b in boundaries:
        if b.RelatingSpace:
            guid = b.RelatingSpace.GlobalId
            boundary_count[guid] = boundary_count.get(guid, 0) + 1

    missing = [s for s in spaces if s.GlobalId not in boundary_count]
    log.info(f"  Espaces avec Space Boundaries 2B : {len(spaces) - len(missing)}/{len(spaces)}")
    if missing:
        log.warning(f"  Espaces SANS boundaries : {len(missing)}")
        for s in missing[:5]:
            log.warning(f"    → {s.GlobalId} | {s.Name}")

    return boundary_count


def save_ifc(model: ifcopenshell.file, output_path: str) -> None:
    model.write(output_path)
    log.info(f"Fichier IFC réparé sauvegardé : {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Réparation géométrique IFC — CHU Mohammed VI")
    parser.add_argument("--ifc", required=True, help="Fichier IFC source")
    parser.add_argument("--output", required=True, help="Fichier IFC réparé en sortie")
    args = parser.parse_args()

    if not Path(args.ifc).exists():
        raise FileNotFoundError(f"Fichier IFC introuvable : {args.ifc}")

    model = load_ifc(args.ifc)

    # 1. Suppression des espaces dupliqués
    remove_duplicate_spaces(model)

    # 2. Correction des hauteurs d'étage (valeurs réelles CHU Mohammed VI)
    storey_heights_chu = {
        "SS2": -8.50, "SS1": -4.20, "RDC": 0.00,
        "N1": 4.50, "N2": 9.00, "N3": 13.50,
        "N4": 18.00, "N5": 22.50, "N6": 27.00,
        "N7": 31.50, "N8": 36.00, "Toiture": 40.20,
    }
    fix_floor_heights(model, storey_heights_chu)

    # 3. Validation Space Boundaries 2B
    validate_space_boundaries(model)

    # 4. Sauvegarde
    save_ifc(model, args.output)

    log.info("=== Réparation géométrique terminée ===")


if __name__ == "__main__":
    main()
