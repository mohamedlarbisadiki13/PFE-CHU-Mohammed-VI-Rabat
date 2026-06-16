# PFE — GeoBIM & Simulation Énergétique · CHU Mohammed VI de Rabat

> Mémoire de fin d'études · 2025–2026  
> Spécialité : Sciences Géomatiques et Ingénierie Topographique  

---

## Contexte

Ce dépôt contient l'ensemble des scripts, configurations et données numériques associés au projet de fin d'études portant sur l'intégration GeoBIM et la simulation énergétique de l'IGH (Immeuble de Grande Hauteur) du CHU Mohammed VI de Rabat, bâtiment certifié **HQE Exceptionnel** (janvier 2026).

---

## Pipeline général

```
Maquettes Revit (IFC4 · 6 fichiers)
        │
        ▼
Réparation géométrique (Revit + Dynamo + ifcOpenShell)
        │
        ▼
bim2sim v0.1.0  ──►  EnergyPlus 9.4.0 (ILAS)
        │                    │
        ▼                    ▼
12 archétypes thermiques   Post-traitement ventilation (SFP)
(TEASER JSON)              + pompage (SPP)
                                │
                                ▼
                     Baseline : 3 239 530 kWh/an
                               76.2 kWh/m²/an
                               (validation BET : −1.4 %)
                                │
                                ▼
                    PVsyst + Meteonorm TMY
                    ┌──────────┴──────────┐
                 S1 Rooftop            S2 BIPV
                 412 kWc               857 kWc
                 573 981 kWh/an        910 054 kWh/an
                    └──────────┬──────────┘
                               ▼
                        AHP Saaty (6 critères)
                        CR = 0.012 → S1 recommandé
                        Score S1 = 0.678
```

---

## Structure du dépôt

```
├── 01_bim2sim/
│   ├── run_simulation.py        # Orchestration bim2sim → EnergyPlus
│   ├── ifc_extract_layers.py    # Extraction des couches/matériaux IFC (ifcOpenShell)
│   ├── config_teaser.json       # Configuration TEASER (archétypes, matériaux)
│   └── TypeElements_IWU.json    # Bibliothèque d'éléments types
├── 02_energyplus_postprocess/
│   ├── ventilation_calc.py      # Calcul E_ventilation (SFP, EN 13779)
│   ├── pumping_calc.py          # Calcul E_pompage (ratio SPP)
│   └── ventilation_config.json  # Paramètres aérauliques par archétype
├── 03_weather/
│   └── MAR_RK_Rabat-Sale.AP.601350_TMYx.epw   # Fichier météo TMYx Rabat-Salé
├── 04_AHP_code/
│   └── AHP_scenarios_PV.py      # Analyse multicritère AHP (Saaty)
└── 05_pvsyst_rapports/
    ├── PV_toitures_Project_Report.pdf     # Rapport PVsyst — Scénario 1 (Rooftop)
    └── BIPV_toitures_Project_Report.pdf   # Rapport PVsyst — Scénario 2 (BIPV)
```

> **Note** : le script de réparation géométrique (Dynamo/Revit, cf. Annexe A du mémoire) n'est pas encore versionné dans ce dépôt — seule l'extraction des couches IFC post-réparation (`ifc_extract_layers.py`) y figure actuellement.

---

## Versions & dépendances

| Outil | Version |
|---|---|
| Python | 3.10 |
| bim2sim | 0.1.0 |
| EnergyPlus | 9.4.0 |
| ifcOpenShell | 0.7.x |
| PVsyst | 7.4 |
| Meteonorm | 9 |
| Fichier météo | TMYx Rabat-Salé · WMO #601350 |

---

## Résultats clés

| Indicateur | Valeur |
|---|---|
| Consommation baseline | 3 239 530 kWh/an |
| Intensité énergétique | 76.2 kWh/m²/an |
| Écart vs. BET (77.31 kWh/m²/an) | −1.4 % ✓ |
| Production S1 (rooftop 412 kWc) | 573 981 kWh/an · PR 71.95 % |
| Production S2 (BIPV 857 kWc) | 910 054 kWh/an · PR 67.02 % |
| Retour sur investissement S1 | 4.7 ans |
| Scénario recommandé (AHP) | **S1 — Score 0.678** |

---

## Auteurs

- **[Mohamed larbi Sadiki]**  
- **[Yahya Lasfar]**  

Encadré par : [Pr. Ishrak Rached] · [IAV Hassan II]

---

## Licence

[MIT](LICENSE) — libre utilisation avec attribution.
