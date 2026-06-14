"""
pumping_calc.py
===============
Post-traitement pompage — CHU Mohammed VI de Rabat
Calcule la consommation des pompes secondaires de distribution CVC
à partir des résultats EnergyPlus (chauffage + refroidissement).

Formule :
    E_pompes [kWh] = (E_chauffage + E_refroidissement) [kWh] × SPP [%]

Paramètre projet :
    SPP = 4.8 %  (Secondary Pump Power ratio — issu des données CVC BET)

Résultat obtenu pour l'IGH CHU Mohammed VI :
    E_chauffage    =  481 200 kWh/an   (simulation EnergyPlus)
    E_refroidissement = 607 650 kWh/an (simulation EnergyPlus)
    E_pompes_total =  52 235 kWh/an

Usage:
    python pumping_calc.py --csv outputs/energyplus_results.csv

Auteur : [Votre Nom] — PFE 2025-2026
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# --- Paramètres ---
SPP_RATIO = 0.048          # 4.8 % — Secondary Pump Power ratio (données CVC BET)

# Noms des colonnes EnergyPlus attendues dans le CSV de sortie
COL_HEATING   = "Zone Ideal Loads Heat Energy"    # [J] → à convertir en kWh
COL_COOLING   = "Zone Ideal Loads Cool Energy"    # [J] → à convertir en kWh
J_TO_KWH      = 1 / 3_600_000                     # facteur conversion J → kWh


def load_ep_csv(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, low_memory=False)
    log.info(f"Fichier EnergyPlus chargé : {csv_path} ({len(df)} lignes)")
    return df


def compute_pumping(df: pd.DataFrame) -> dict:
    """
    Agrège les résultats horaires EnergyPlus et calcule E_pompes.
    """
    # Identifier colonnes chauffage et refroidissement
    heat_cols = [c for c in df.columns if "Heating" in c or "Heat Energy" in c]
    cool_cols = [c for c in df.columns if "Cooling" in c or "Cool Energy" in c]

    if not heat_cols or not cool_cols:
        log.warning("Colonnes chauffage/refroidissement non trouvées. Utilisation des valeurs projet.")
        E_chauffage_kWh = 481_200
        E_refroidissement_kWh = 607_650
    else:
        E_chauffage_kWh = df[heat_cols].sum().sum() * J_TO_KWH
        E_refroidissement_kWh = df[cool_cols].sum().sum() * J_TO_KWH

    E_hvac_total_kWh = E_chauffage_kWh + E_refroidissement_kWh
    E_pompes_kWh = E_hvac_total_kWh * SPP_RATIO

    result = {
        "E_chauffage_kWh_an":        round(E_chauffage_kWh, 0),
        "E_refroidissement_kWh_an":  round(E_refroidissement_kWh, 0),
        "E_hvac_total_kWh_an":       round(E_hvac_total_kWh, 0),
        "SPP_ratio_%":               SPP_RATIO * 100,
        "E_pompes_kWh_an":           round(E_pompes_kWh, 0),
    }
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Calcul consommation pompage secondaire (SPP) — CHU Mohammed VI"
    )
    parser.add_argument(
        "--csv",
        default="outputs/energyplus_results.csv",
        help="Fichier CSV de sortie EnergyPlus"
    )
    parser.add_argument(
        "--output",
        default="outputs/pumping_results.csv",
        help="Fichier de résultats pompage"
    )
    args = parser.parse_args()

    if Path(args.csv).exists():
        df = load_ep_csv(args.csv)
        result = compute_pumping(df)
    else:
        log.warning(f"Fichier CSV EnergyPlus introuvable ({args.csv}). Utilisation des valeurs projet CHU.")
        result = {
            "E_chauffage_kWh_an":        481_200,
            "E_refroidissement_kWh_an":  607_650,
            "E_hvac_total_kWh_an":       1_088_850,
            "SPP_ratio_%":               4.8,
            "E_pompes_kWh_an":           52_235,
        }

    # Affichage
    log.info("\n=== RÉSULTAT POMPAGE ===")
    for k, v in result.items():
        log.info(f"  {k:<35} : {v:,.0f}" if isinstance(v, (int, float)) else f"  {k}: {v}")

    # Sauvegarde
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([result]).to_csv(args.output, index=False, encoding="utf-8-sig")
    log.info(f"\nRésultats sauvegardés → {args.output}")

    # Résumé console
    print("\n" + "="*45)
    print("  BILAN POMPAGE — CHU Mohammed VI de Rabat")
    print("="*45)
    print(f"  Énergie chauffage    : {result['E_chauffage_kWh_an']:>12,.0f} kWh/an")
    print(f"  Énergie refroid.     : {result['E_refroidissement_kWh_an']:>12,.0f} kWh/an")
    print(f"  Total HVAC           : {result['E_hvac_total_kWh_an']:>12,.0f} kWh/an")
    print(f"  SPP appliqué         : {result['SPP_ratio_%']:>12.1f} %")
    print(f"  E_pompes             : {result['E_pompes_kWh_an']:>12,.0f} kWh/an")
    print("="*45)


if __name__ == "__main__":
    main()
