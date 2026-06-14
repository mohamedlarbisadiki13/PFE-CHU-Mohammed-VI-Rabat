import json
import os
import ifcopenshell
import ifcopenshell.util.element

# ==========================================
# 1. CONFIGURATION DES CHEMINS
# ==========================================
CHEMIN_JSON_MAPPING = r"C:\Users\Administrateur\Documents\PFE_CHU_SADIKI\SIMULATION_ENERGITIQUE\Custom_Usage\CustomUsage_1.json"

# NOUVEAU : Chemin vers ton fichier de configuration des ventilateurs
CHEMIN_JSON_FANS = r"C:\Users\Administrateur\Documents\PFE_CHU_SADIKI\SIMULATION_ENERGITIQUE\Fans\fans_config_correct.json"

CHEMINS_IFC = {
    "IFC_I4": r"C:\Users\Administrateur\Documents\PFE_CHU_SADIKI\SIMULATION_ENERGITIQUE\IFCs\IFC_VALIDE\I4.ifc",
    "IFC_I12": r"C:\Users\Administrateur\Documents\PFE_CHU_SADIKI\SIMULATION_ENERGITIQUE\Simulation_BIM2SIM\EP12_V\ifc\arch\I12.ifc",
    "IFC_I20": r"C:\Users\Administrateur\Documents\PFE_CHU_SADIKI\SIMULATION_ENERGITIQUE\IFCs\I20_V.ifc",
    "IFC_I25": r"C:\Users\Administrateur\Documents\PFE_CHU_SADIKI\SIMULATION_ENERGITIQUE\IFCs\I25_V.ifc"
}


# ==========================================
# 2. CHARGEMENT DES JSON
# ==========================================
def charger_mapping(chemin_json):
    with open(chemin_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    espace_vers_profil = {}
    for profil, liste_espaces in data['usage_definitions'].items():
        for espace in liste_espaces:
            espace_vers_profil[espace.strip()] = profil

    return espace_vers_profil


def charger_config_fans(chemin_json):
    if not os.path.exists(chemin_json):
        print(f"⚠️ Fichier de config des ventilateurs introuvable : {chemin_json}")
        return {}
    with open(chemin_json, 'r', encoding='utf-8') as f:
        return json.load(f)


# ==========================================
# 3. EXTRACTIONS DES QUANTITÉS
# ==========================================
def obtenir_quantites(space):
    """Extrait la surface et le volume d'un IfcSpace."""
    psets = ifcopenshell.util.element.get_psets(space)
    quantities = psets.get("Qto_SpaceBaseQuantities") or psets.get("BaseQuantities") or {}

    surface = quantities.get("NetFloorArea") or quantities.get("GrossFloorArea") or 0.0
    volume = quantities.get("NetVolume") or quantities.get("GrossVolume") or 0.0

    return float(surface), float(volume)


# ==========================================
# 4. TRAITEMENT PRINCIPAL
# ==========================================
def analyser_ifcs():
    print("--- Démarrage de l'analyse BIM/BEM (Groupement par Hauteur avec compensation Faux Plafond) ---")

    if not os.path.exists(CHEMIN_JSON_MAPPING):
        print(f"❌ ERREUR : Le fichier JSON n'a pas été trouvé au chemin :\n{CHEMIN_JSON_MAPPING}")
        return

    mapping = charger_mapping(CHEMIN_JSON_MAPPING)
    config_fans = charger_config_fans(CHEMIN_JSON_FANS)

    # Structure : resultats_globaux[nom_ifc][hauteur][nom_profil] = {data}
    resultats_globaux = {}

    for nom_ifc, chemin_ifc in CHEMINS_IFC.items():
        if not os.path.exists(chemin_ifc):
            print(f"⚠️ Fichier IFC introuvable ignoré : {chemin_ifc}")
            continue

        print(f"\n📂 Ouverture et lecture de : {nom_ifc}...")
        modele = ifcopenshell.open(chemin_ifc)
        espaces = modele.by_type("IfcSpace")

        resultats_ifc = {}
        espaces_non_trouves = 0

        for space in espaces:
            long_name = space.LongName if space.LongName else ""
            name = space.Name if space.Name else ""

            nom_complet_1 = f"{long_name} {name}".strip()
            nom_complet_2 = f"{name} {long_name}".strip()
            nom_seul = long_name.strip() if long_name else name.strip()

            profil_trouve = mapping.get(nom_complet_1) or mapping.get(nom_complet_2) or mapping.get(nom_seul)

            if profil_trouve:
                surface, volume_brut = obtenir_quantites(space)

                if surface > 0.1 and volume_brut > 0.1:
                    # Calcul de la hauteur brute (dalle à dalle)
                    hauteur_piece = round(volume_brut / surface, 2)

                    # NOUVEAU : Déduction de 50cm pour le plénum (faux plafond)
                    # On utilise max(0.0, ...) au cas où un espace technique ferait moins de 50cm
                    hauteur_utile = max(0.0, hauteur_piece - 0.75)

                    # NOUVEAU : Recalcul du volume utile (sans le plénum)
                    volume_utile = surface * hauteur_utile
                else:
                    hauteur_piece = 0.0
                    volume_utile = 0.0

                if hauteur_piece > 0:
                    # On continue de grouper par hauteur_piece (la hauteur architecturale)
                    if hauteur_piece not in resultats_ifc:
                        resultats_ifc[hauteur_piece] = {}

                    if profil_trouve not in resultats_ifc[hauteur_piece]:
                        resultats_ifc[hauteur_piece][profil_trouve] = {
                            "surface_totale": 0.0,
                            "volume_total": 0.0,  # On va y stocker le volume utile
                            "nombre_locaux": 0
                        }

                    resultats_ifc[hauteur_piece][profil_trouve]["surface_totale"] += surface
                    resultats_ifc[hauteur_piece][profil_trouve]["volume_total"] += volume_utile
                    resultats_ifc[hauteur_piece][profil_trouve]["nombre_locaux"] += 1
            else:
                espaces_non_trouves += 1

        resultats_globaux[nom_ifc] = resultats_ifc
        print(f"✅ Terminé pour {nom_ifc} (Espaces ignorés ou non mappés : {espaces_non_trouves})")

    # ==========================================
    # 5. CALCUL AUTOMATIQUE DE L'ÉNERGIE DES VENTILATEURS (E_fans)
    # ==========================================
    print("\n\n" + "=" * 70)
    print("⚡ CALCUL AUTOMATIQUE DE L'ÉNERGIE DES VENTILATEURS (SFP)")
    print("=" * 70)

    # Agréger les volumes totaux (qui sont maintenant les volumes utiles) par profil
    volumes_par_profil = {}
    for nom_ifc, hauteurs in resultats_globaux.items():
        for hsp, profils in hauteurs.items():
            for profil, data in profils.items():
                if profil not in volumes_par_profil:
                    volumes_par_profil[profil] = 0.0
                volumes_par_profil[profil] += data['volume_total']

    energie_totale_batiment = 0.0
    resultats_energie = {}

    for profil, volume in sorted(volumes_par_profil.items()):
        # Récupérer les données du JSON ou utiliser des valeurs par défaut si non trouvé
        params = config_fans.get(profil, {"ACH": 3.0, "SFP": 0.3, "H": 8760, "foisonnement": 1.0})

        ach = params.get("ACH", 3.0)
        sfp = params.get("SFP", 0.3)  # Basé sur tes modifications précédentes
        h = params.get("H", 8760)
        foisonnement = params.get("foisonnement", 1.0)

        # Calcul (avec le volume utile sans faux plafond)
        e_brut = (volume * ach / 3600) * sfp * h
        e_fans = e_brut * foisonnement

        resultats_energie[profil] = e_fans
        energie_totale_batiment += e_fans

    # ==========================================
    # 6. BILAN FINAL
    # ==========================================
    print("\n📈 BILAN ÉNERGÉTIQUE GLOBAL DES VENTILATEURS")
    print("-" * 70)
    for profil, energie in sorted(resultats_energie.items()):
        print(f" - {profil[:35]:<35} : {energie:,.2f} kWh/an".replace(',', ' '))
    print("-" * 70)
    print(f" 🟢 TOTAL IGH : {energie_totale_batiment:,.2f} kWh/an".replace(',', ' '))
    print("=" * 70)


if __name__ == '__main__':
    analyser_ifcs()
