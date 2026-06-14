import json


def calculer_energie_pompes(fichier_json, spp_ratio):
    """
    Calcule la consommation électrique des pompes (eau chaude / eau glacée)
    basé sur la charge thermique totale et un ratio SPP (Specific Pump Power).
    """
    print("--- DÉMARRAGE DU POST-TRAITEMENT HYDRAULIQUE ---")

    # 1. Chargement des données depuis le fichier JSON
    try:
        with open(fichier_json, 'r', encoding='utf-8') as file:
            data = json.load(file)
            print(f"Fichier '{fichier_json}' chargé avec succès pour le projet : {data['projet']}\n")
    except FileNotFoundError:
        print(f"Erreur : Le fichier '{fichier_json}' est introuvable.")
        return

    # 2. Extraction des besoins thermiques (en kWh)
    e_chauffage = data['resultats_annuels_kWh']['chauffage_total']
    e_froid = data['resultats_annuels_kWh']['froid_total']

    e_thermique_totale = e_chauffage + e_froid

    # 3. Calcul analytique de l'énergie de pompage (en kWh)
    # Formule : E_pompes = E_thermique * SPP
    e_pompes_chaud = e_chauffage * spp_ratio
    e_pompes_froid = e_froid * spp_ratio

    e_pompes_totale = e_thermique_totale * spp_ratio

    # 4. Affichage des résultats pour le bilan final
    print("--- RÉSULTATS DU BILAN ANNUEL ---")
    print(f"Paramètre SPP (Pompes à Vitesse Variable - HQE) : {spp_ratio * 100}%")
    print("-" * 45)
    print(f"Besoins Thermiques Chauffage      : {e_chauffage:,.0f} kWh".replace(',', ' '))
    print(f"Énergie Électrique Pompes (Chaud) : {e_pompes_chaud:,.0f} kWh".replace(',', ' '))
    print("-" * 45)
    print(f"Besoins Thermiques Froid          : {e_froid:,.0f} kWh".replace(',', ' '))
    print(f"Énergie Électrique Pompes (Froid) : {e_pompes_froid:,.0f} kWh".replace(',', ' '))
    print("-" * 45)
    print(f"ÉNERGIE THERMIQUE GLOBALE         : {e_thermique_totale:,.0f} kWh".replace(',', ' '))
    print(f"ÉNERGIE ÉLECTRIQUE POMPES GLOBALE : {e_pompes_totale:,.0f} kWh".replace(',', ' '))
    print("-" * 45)


# === EXÉCUTION DU SCRIPT ===
if __name__ == "__main__":
    # Nom du fichier d'entrée
    fichier_input = r"C:\Users\Administrateur\Documents\PFE_CHU_SADIKI\SIMULATION_ENERGITIQUE\FANS\donnees_thermiques.json"

    # Ratio SPP défini à 4.8% (ASHRAE 90.1 Appendix G)
    ratio_spp_projet = 0.048

    calculer_energie_pompes(fichier_input, ratio_spp_projet)
