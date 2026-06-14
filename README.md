# PFE — GeoBIM & Simulation Énergétique · CHU Mohammed VI de Rabat

> Mémoire de fin d'études · 2025–2026  
> Spécialité : Géomatique / Efficacité Énergétique des Bâtiments  

---

## Contexte

Ce dépôt contient l'ensemble des scripts, configurations et données numériques associés au projet de fin d'études portant sur l'intégration GeoBIM et la simulation énergétique de l'IGH (Immeuble de Grande Hauteur) du CHU Mohammed VI de Rabat, bâtiment certifié **HQE Exceptionnel** (janvier 2026).

---

## Pipeline général

```
Maquettes Revit (IFC4 · 6 fichiers)
        │
        ▼
Réparation géométrique (Dynamo + ifcOpenShell)
        │
        ▼
bim2sim v0.3.0  ──►  EnergyPlus 9.4.0 (ILAS)
        │                    │s
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
├── 01_bim2sim/               # Config TEASER, scripts bim2sim, preprocessing IFC
├── 02_energyplus_postprocess/ # Calcul E_fans (SFP) + E_pompes (SPP)
├── 03_mms_georef/            # ICP, filtrage SOR, transformation Helmert Mercator→Merchich
├── 04_pvsyst_ahp/            # Matrice AHP Saaty, paramètres PVsyst S1 & S2
├── 05_weather/               # Fichier EPW TMYx Rabat-Salé + note discordance
└── annexes_compressed/       # Annexes allégées (JSON minifiés, notebooks)
```

---

## Versions & dépendances

| Outil | Version |
|---|---|
| Python | 3.10 |
| bim2sim | 0.3.0 |
| EnergyPlus | 9.4.0 |
| ifcOpenShell | 0.7.x |
| PVsyst | 7.4 |
| Meteonorm | 9 |
| Fichier météo | TMYx Rabat-Salé · WMO #601350 |

---

## Lancer les scripts

```bash
# 1. Installer les dépendances
pip install bim2sim ifcopenshell pandas numpy

# 2. Lancer la simulation bim2sim → EnergyPlus
python 01_bim2sim/run_simulation.py

# 3. Post-traitement ventilation + pompage
python 02_energyplus_postprocess/ventilation_calc.py
python 02_energyplus_postprocess/pumping_calc.py

# 4. Calcul AHP
python 04_pvsyst_ahp/ahp_saaty.py
```

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
