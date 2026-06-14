import ifcopenshell


def is_external(element):
    """Vérifie si l'élément est défini comme extérieur dans ses propriétés (Pset)."""
    if hasattr(element, 'IsDefinedBy') and element.IsDefinedBy:
        for definition in element.IsDefinedBy:
            if definition.is_a('IfcRelDefinesByProperties'):
                prop_set = definition.RelatingPropertyDefinition
                if prop_set.is_a('IfcPropertySet'):
                    for prop in prop_set.HasProperties:
                        if prop.Name == 'IsExternal':
                            # Retourne True ou False
                            return prop.NominalValue.wrappedValue
    return None


def get_materials(element):
    """Extrait la liste des matériaux (couches) associés à un élément IFC."""
    materials = []
    if hasattr(element, 'HasAssociations') and element.HasAssociations:
        for association in element.HasAssociations:
            if association.is_a('IfcRelAssociatesMaterial'):
                mat_select = association.RelatingMaterial
                if not mat_select:
                    continue

                # Matériau simple
                if mat_select.is_a('IfcMaterial'):
                    materials.append(mat_select.Name)
                # Murs multicouches ou dalles (le plus courant dans Revit)
                elif mat_select.is_a('IfcMaterialLayerSetUsage'):
                    for layer in mat_select.ForLayerSet.MaterialLayers:
                        materials.append(layer.Material.Name)
                elif mat_select.is_a('IfcMaterialLayerSet'):
                    for layer in mat_select.MaterialLayers:
                        materials.append(layer.Material.Name)
                # Listes de matériaux (souvent pour les portes/fenêtres)
                elif mat_select.is_a('IfcMaterialList'):
                    for mat in mat_select.Materials:
                        materials.append(mat.Name)
                elif mat_select.is_a('IfcMaterialConstituentSet'):
                    for constituent in mat_select.MaterialConstituents:
                        materials.append(constituent.Material.Name)

    return materials


def audit_ifc_materials(ifc_path):
    print(f"Chargement du fichier IFC : {ifc_path}...")
    try:
        model = ifcopenshell.open(ifc_path)
    except Exception as e:
        print(f"Erreur lors du chargement : {e}")
        return

    # Dictionnaire pour stocker les types de composition uniques trouvés
    # Format : {'Murs Extérieurs': { ('Beton', 'Isolant'): 15 (quantité) } }
    audit_results = {
        'Murs Extérieurs (Outer Walls)': {},
        'Murs Intérieurs (Inner Walls)': {},
        'Dalles / Planchers (Slabs/Floors)': {},
        'Toitures (Roofs)': {},
        'Fenêtres (Windows)': {},
        'Portes (Doors)': {}
    }

    # Liste des classes IFC à analyser
    element_classes = ['IfcWall', 'IfcWallStandardCase', 'IfcSlab', 'IfcRoof', 'IfcWindow', 'IfcDoor']

    print("Analyse des éléments en cours, veuillez patienter...\n" + "-" * 50)

    for cls in element_classes:
        elements = model.by_type(cls)
        for elem in elements:
            mats = get_materials(elem)
            # Convertir en tuple pour pouvoir l'utiliser comme clé de dictionnaire
            mats_tuple = tuple(mats) if mats else ('Aucun matériau défini',)

            # Catégorisation
            category = None
            if 'Wall' in cls:
                ext = is_external(elem)
                if ext is True:
                    category = 'Murs Extérieurs (Outer Walls)'
                else:
                    category = 'Murs Intérieurs (Inner Walls)'
            elif 'Slab' in cls:
                category = 'Dalles / Planchers (Slabs/Floors)'
            elif 'Roof' in cls:
                category = 'Toitures (Roofs)'
            elif 'Window' in cls:
                category = 'Fenêtres (Windows)'
            elif 'Door' in cls:
                category = 'Portes (Doors)'

            if category:
                if mats_tuple not in audit_results[category]:
                    audit_results[category][mats_tuple] = 0
                audit_results[category][mats_tuple] += 1

    # Affichage des résultats
    for category, compositions in audit_results.items():
        print(f"\n=== {category} ===")
        if not compositions:
            print("  -> Aucun élément trouvé de ce type.")
            continue

        # Trier par nombre d'occurrences (du plus fréquent au moins fréquent)
        sorted_comps = sorted(compositions.items(), key=lambda x: x[1], reverse=True)

        for comp, count in sorted_comps:
            materiaux_str = " + ".join(comp)
            print(f"  [{count} éléments] : {materiaux_str}")


if __name__ == '__main__':
    # Le chemin vers la maquette
    chemin_ifc = r'C:\Users\Administrateur\Documents\PFE_CHU_SADIKI\SIMULATION_ENERGITIQUE\IFCs\I5.ifc'
    audit_ifc_materials(chemin_ifc)
