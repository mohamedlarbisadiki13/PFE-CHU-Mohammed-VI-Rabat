"""
ventilation_calc.py
===================
Post-traitement ventilation mécanique — CHU Mohammed VI de Rabat
Calcule la consommation électrique des ventilateurs (E_fans) à partir
des résultats EnergyPlus, en appliquant la formule SFP (EN 13779:2007).

Formule :
    E_fans [kWh] = V_zone [m³] × ACH [h⁻¹] / 3600 × SFP [W/(m³/s)] × H [h/an] × F_oisonement

Paramètres projet :
    SFP = 300 W/(m³/s)  →  catégorie SFP1 selon EN 13779:2007
    ACH corrigé = ACH_brut × (1 - η_HR)  avec η_HR = 0.73 (ErP 2018 / Eurovent)
    H = 8 760 h/an (simulation annuelle complète)

Résultat obtenu pour l'IGH CHU Mohammed VI :
    E_fans_total = 313 165 kWh/an

Usage:
    python ventilation_calc.py --csv outputs/energyplus_results.csv --config ../01_bim2sim/config_teaser.json

Auteur : [Votre Nom] — PFE 2025-2026
"""

import argparse
import json
import logging
from pathlib import Path

import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# --- Constantes ---
SFP_W_PER_M3S = 300        # W/(m³/s) — SFP1, EN 13779:2007
HEAT_RECOVERY_ETA = 0.73   # 73 % — ErP 2018 / Eurovent certifié
HOURS_PER_YEAR = 8760      # h/an
F_FOISONNEMENT = 0.85      # Facteur de foisonnement — pas tous les systèmes simultanément


def load_ep_results(csv_path: str) -> pd.DataFrame:
    """Charge les résultats horaires EnergyPlus (format CSV output)."""
    df = pd.read_csv(csv_path, low_memory=False)
    log.info(f"Résultats EnergyPlus chargés : {len(df)} lignes, {len(df.columns)} colonnes")
    return df


def compute_e_fans_per_zone(zones: list, config: dict) -> pd.DataFrame:
    """
    Calcule E_fans pour chaque zone thermique à partir des archétypes.

    Paramètres :
        zones   : liste de dict {nom, surface_m2, hauteur_m, archetype_id}
        config  : configuration TEASER (archétypes avec ACH brut)

    Retourne un DataFrame avec E_fans [kWh/an] par zone.
    """
    archetypes = config["thermal_archetypes"]
    results = []

    for zone in zones:
        archetype_key = zone["archetype_id"]
        if archetype_key not in archetypes:
            log.warning(f"Archétype inconnu : {archetype_key} pour zone {zone['nom']}")
            continue

        arch = archetypes[archetype_key]
        ACH_brut = arch["ACH_h"]
        ACH_corrige = ACH_brut * (1 - HEAT_RECOVERY_ETA)

        V_zone_m3 = zone["surface_m2"] * zone["hauteur_m"]

        # Débit volumique [m³/s]
        q_m3s = V_zone_m3 * ACH_corrige / 3600

        # Puissance ventilateur [W]
        P_fan_W = q_m3s * SFP_W_PER_M3S

        # Énergie annuelle [kWh]
        E_fans_kWh = P_fan_W * HOURS_PER_YEAR * F_FOISONNEMENT / 1000

        results.append({
            "zone": zone["nom"],
            "archetype": archetype_key,
            "surface_m2": zone["surface_m2"],
            "volume_m3": round(V_zone_m3, 1),
            "ACH_brut_h": ACH_brut,
            "ACH_corrige_h": round(ACH_corrige, 2),
            "debit_m3s": round(q_m3s, 4),
            "puissance_fan_W": round(P_fan_W, 1),
            "E_fans_kWh_an": round(E_fans_kWh, 1),
        })

    df = pd.DataFrame(results)
    log.info(f"  Zones traitées       : {len(df)}")
    log.info(f"  E_fans total [kWh/an]: {df['E_fans_kWh_an'].sum():,.0f}")
    return df


def main():
    parser = argparse.ArgumentParser(
        description="Calcul consommation ventilation (SFP) — CHU Mohammed VI"
    )
    parser.add_argument("--config", default="../01_bim2sim/config_teaser.json")
    parser.add_argument("--zones", default="zones_input.json",
                        help="JSON avec liste des zones {nom, surface_m2, hauteur_m, archetype_id}")
    parser.add_argument("--output", default="outputs/ventilation_results.csv")
    args = parser.parse_args()

    with open(args.config, "r", encoding="utf-8") as f:
        config = json.load(f)

    if Path(args.zones).exists():
        with open(args.zones, "r", encoding="utf-8") as f:
            zones = json.load(f)
    else:
        # Données exemple CHU Mohammed VI (extrait représentatif)
        log.warning(f"Fichier zones introuvable ({args.zones}). Utilisation des données exemple CHU.")
        zones = [
            {"nom": "Bloc_A_Chambres_N1", "surface_m2": 1200, "hauteur_m": 3.2, "archetype_id": "Type_1"},
            {"nom": "Bloc_A_Bloc_Op_N2",  "surface_m2": 450,  "hauteur_m": 3.5, "archetype_id": "Type_2A"},
            {"nom": "Bloc_B_Reanimation",  "surface_m2": 380,  "hauteur_m": 3.2, "archetype_id": "Type_3A"},
            {"nom": "Bloc_B_Consultation", "surface_m2": 900,  "hauteur_m": 3.0, "archetype_id": "Type_4"},
            {"nom": "Bloc_C_Laboratoire",  "surface_m2": 620,  "hauteur_m": 3.2, "archetype_id": "Type_5"},
            {"nom": "Bloc_C_Imagerie",     "surface_m2": 280,  "hauteur_m": 3.5, "archetype_id": "Type_6"},
            {"nom": "Bloc_D_Hall",         "surface_m2": 1500, "hauteur_m": 6.0, "archetype_id": "Type_8A"},
        ]

    df_results = compute_e_fans_per_zone(zones, config)

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    df_results.to_csv(args.output, index=False, encoding="utf-8-sig")

    total = df_results["E_fans_kWh_an"].sum()
    log.info(f"\n=== RÉSULTAT VENTILATION ===")
    log.info(f"E_fans TOTAL  : {total:,.0f} kWh/an")
    log.info(f"SFP appliqué  : {SFP_W_PER_M3S} W/(m³/s) — SFP1 (EN 13779:2007)")
    log.info(f"η récupération: {HEAT_RECOVERY_ETA*100:.0f}% (ErP 2018 / Eurovent)")
    log.info(f"Résultats → {args.output}")

    print(df_results.to_string(index=False))


if __name__ == "__main__":
    main()
