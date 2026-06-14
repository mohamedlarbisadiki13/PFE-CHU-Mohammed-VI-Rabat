# Note — Discordance du fichier météo EnergyPlus

## Problème identifié

Le texte du mémoire (§II.1.2 et §I.4) mentionne l'utilisation du fichier météo :

> **MAR_RK_RabatSale.AP.601350_TMYx.epw**
> Station : Rabat-Salé Aéroport · WMO #601350 · TMYx (Typical Meteorological Year)

Or, l'analyse du script `Annexe_F` et du rapport HTML de sortie EnergyPlus révèle que la simulation a effectivement utilisé :

> **MAR_Casablanca.Nouasser.601560_IWEC.epw**
> Station : Casablanca/Nouasser · WMO #601560 · IWEC (International Weather for Energy Calculations)

## Impact potentiel

| Paramètre         | Rabat-Salé TMYx | Casablanca IWEC | Écart estimé |
|-------------------|----------------|-----------------|--------------|
| T moyenne annuelle | ~17.5 °C       | ~17.2 °C        | −0.3 °C      |
| GHI annuel         | ~1 890 kWh/m²  | ~1 820 kWh/m²   | −3.7 %       |
| Humidité relative  | ~73 %          | ~76 %           | +3 pts       |

L'écart de GHI (~3.7 %) peut affecter les résultats PVsyst. L'impact sur la baseline thermique est modéré (<2 %) étant donné la proximité des deux stations (70 km).

## Actions requises avant soutenance

### Option A — Correction (recommandée)
1. Relancer la simulation EnergyPlus avec le fichier TMYx correct :
   `MAR_RK_RabatSale.AP.601350_TMYx.epw`
   (téléchargeable sur [climate.onebuilding.org](https://climate.onebuilding.org))
2. Mettre à jour les tableaux de résultats (§III.2.2 et §III.4)
3. Corriger la référence dans le script Annexe F

### Option B — Justification documentée (si manque de temps)
1. Ajouter une note de bas de page dans §II.1.2 expliquant la substitution
2. Quantifier l'impact dans les limites (§IV ou conclusion)
3. Corriger la référence dans le script Annexe F

## Fichiers concernés

- `01_bim2sim/config_teaser.json` → champ `"weather_file"`
- `01_bim2sim/run_simulation.py` → argument `--weather`
- Mémoire : §I.4, §II.1.2, Annexe F, en-tête rapport EnergyPlus HTML

## Statut

- [ ] Option A ou B choisie
- [ ] Simulation relancée / note ajoutée
- [ ] Mémoire mis à jour
