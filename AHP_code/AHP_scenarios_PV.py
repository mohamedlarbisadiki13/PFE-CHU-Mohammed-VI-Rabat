# -*- coding: utf-8 -*-
"""
================================================================================
 AIDE MULTICRITERE A LA DECISION PAR LA METHODE AHP (Analytic Hierarchy Process)
 Comparaison des scenarios PV : Scenario 1 (Rooftop) vs Scenario 2 (BIPV)
--------------------------------------------------------------------------------
 Reference methodologique :
   Saaty, T.L. (1980). The Analytic Hierarchy Process. McGraw-Hill, New York.
   Saaty, R.W. (1987). The analytic hierarchy process - what it is and how it
   is used. Mathematical Modelling, 9(3-5), 161-176.
   DOI : 10.1016/0270-0255(87)90473-8
================================================================================
 Auteur : [Votre nom] - PFE Sciences Geomatiques & Ingenierie Topographique
================================================================================
"""
 
import os
import numpy as np
 
# =============================================================================
# 1) DEFINITION DES CRITERES
#    sens = +1 si le critere se MAXIMISE (mieux = plus grand)
#    sens = -1 si le critere se MINIMISE (mieux = plus petit)
# =============================================================================
criteres = [
    ("C1 - Production annuelle (kWh/an)",        +1),
    ("C2 - Taux de couverture (%)",              +1),
    ("C3 - LCOE (DH/kWh)",                       -1),
    ("C4 - Temps de retour (ans)",               -1),
    ("C5 - Reduction CO2 (tCO2/20ans)",          +1),
    ("C6 - Simplicite / robustesse (note /10)",  +1),
]
noms_criteres = [c[0] for c in criteres]
sens_criteres = np.array([c[1] for c in criteres])
n = len(criteres)
 
# =============================================================================
# 2) VALEURS REELLES DES 2 SCENARIOS (issues des rapports PVsyst + vos calculs)
#    -> C'est la matrice de PERFORMANCE (les donnees mesurees)
# =============================================================================
#                       C1        C2     C3     C4     C5      C6
perf = np.array([
    [573981.0,   17.72,  0.55,   4.7,   5794.0,  9.0],   # Scenario 1 (Rooftop)
    [910054.0,   28.09,  1.21,  16.6,  11550.0,  5.0],   # Scenario 2 (BIPV)
])
noms_scenarios = ["Scenario 1 - Rooftop", "Scenario 2 - BIPV"]
 
# Note C6 (simplicite) : note qualitative que VOUS attribuez (ici 9/10 pour le
# scenario simple en toiture, 5/10 pour le BIPV plus complexe). A ajuster.
 
# =============================================================================
# 3) MATRICE DE COMPARAISON PAR PAIRES DES CRITERES (jugements - echelle Saaty)
#    a[i][j] = importance du critere i PAR RAPPORT au critere j
#    Echelle de Saaty : 1=egal, 3=modere, 5=fort, 7=tres fort, 9=extreme
#    Reciprocite automatique : a[j][i] = 1/a[i][j]  (geree plus bas)
#    >>> C'EST LA SEULE PARTIE A AJUSTER SELON VOS PRIORITES <<<
#    (Contexte ici : hopital public -> priorite economique C3,C4)
# =============================================================================
#         C1    C2    C3    C4    C5    C6
A = np.array([
    [1,    1,   1/3,  1/3,   2,    3 ],   # C1 Production
    [1,    1,   1/3,  1/3,   2,    3 ],   # C2 Couverture
    [3,    3,    1,    1,    4,    5 ],   # C3 LCOE
    [3,    3,    1,    1,    4,    5 ],   # C4 Retour
    [1/2,  1/2, 1/4,  1/4,   1,    2 ],   # C5 CO2
    [1/3,  1/3, 1/5,  1/5,  1/2,   1 ],   # C6 Simplicite
], dtype=float)
 
# Indice aleatoire RI de Saaty (1987) selon la taille n de la matrice
RI_TABLE = {1:0.00, 2:0.00, 3:0.58, 4:0.90, 5:1.12,
            6:1.24, 7:1.32, 8:1.41, 9:1.45, 10:1.49}
 
 
# =============================================================================
# FONCTIONS DE CALCUL AHP
# =============================================================================
def poids_par_vecteur_propre(A):
    """Calcule les poids = vecteur propre principal normalise (methode exacte
    de Saaty), et renvoie aussi lambda_max pour le test de coherence."""
    valeurs, vecteurs = np.linalg.eig(A)
    idx = np.argmax(valeurs.real)          # plus grande valeur propre
    lambda_max = valeurs.real[idx]
    w = vecteurs[:, idx].real
    w = w / w.sum()                        # normalisation (somme = 1)
    return np.abs(w), lambda_max
 
 
def ratio_coherence(A, lambda_max):
    """Calcule l'indice (CI) et le ratio (CR) de coherence de Saaty.
    Regle : la matrice est acceptable si CR < 0.10."""
    n = A.shape[0]
    CI = (lambda_max - n) / (n - 1)
    RI = RI_TABLE.get(n, 1.49)
    CR = CI / RI if RI > 0 else 0.0
    return CI, RI, CR
 
 
def normaliser_performance(perf, sens):
    """Normalise la matrice de performance entre 0 et 1.
    - critere a maximiser : (x - min) / (max - min)
    - critere a minimiser : (max - x) / (max - min)
    Resultat : 1 = meilleur, 0 = moins bon, sur chaque colonne."""
    P = perf.astype(float).copy()
    norm = np.zeros_like(P)
    for j in range(P.shape[1]):
        col = P[:, j]
        cmin, cmax = col.min(), col.max()
        etendue = (cmax - cmin) if (cmax - cmin) != 0 else 1.0
        if sens[j] > 0:                    # maximiser
            norm[:, j] = (col - cmin) / etendue
        else:                              # minimiser
            norm[:, j] = (cmax - col) / etendue
    return norm
 
 
# =============================================================================
# EXECUTION DE LA PROCEDURE AHP
# =============================================================================
print("=" * 74)
print("   AIDE MULTICRITERE A LA DECISION - METHODE AHP (Saaty, 1980 / 1987)")
print("=" * 74)
 
# --- Etape A : poids des criteres ---
poids, lambda_max = poids_par_vecteur_propre(A)
CI, RI, CR = ratio_coherence(A, lambda_max)
 
print("\n[ETAPE A] POIDS DES CRITERES (vecteur propre principal)")
print("-" * 74)
for nom, w in zip(noms_criteres, poids):
    print(f"   {nom:<42s} : {w*100:6.2f} %")
print(f"\n   Somme des poids ............... : {poids.sum()*100:6.2f} %")
 
# --- Etape B : controle de coherence ---
print("\n[ETAPE B] CONTROLE DE COHERENCE DES JUGEMENTS (Saaty)")
print("-" * 74)
print(f"   lambda_max .................... : {lambda_max:.4f}")
print(f"   Indice de coherence  CI ....... : {CI:.4f}")
print(f"   Indice aleatoire     RI (n={n}) . : {RI:.2f}")
print(f"   Ratio de coherence   CR ....... : {CR:.4f}")
if CR < 0.10:
    print("   >>> CR < 0.10  =>  JUGEMENTS COHERENTS ET VALIDES (OK)")
else:
    print("   >>> CR >= 0.10 =>  INCOHERENT : revoyez la matrice A !")
 
# --- Etape C : normalisation des performances ---
norm = normaliser_performance(perf, sens_criteres)
print("\n[ETAPE C] MATRICE DE PERFORMANCE NORMALISEE (1 = meilleur)")
print("-" * 74)
entete = "   " + " " * 22 + "".join(f"{c.split(' - ')[0]:>9s}" for c in noms_criteres)
print(entete)
for i, nom in enumerate(noms_scenarios):
    ligne = "".join(f"{norm[i,j]:9.3f}" for j in range(n))
    print(f"   {nom:<22s}{ligne}")
 
# --- Etape D : score global pondere ---
scores = norm.dot(poids)        # produit matriciel : somme(poids * perf_norm)
print("\n[ETAPE D] SCORE GLOBAL PONDERE DE CHAQUE SCENARIO")
print("-" * 74)
classement = np.argsort(scores)[::-1]
for rang, i in enumerate(classement, start=1):
    etoile = "  <== SCENARIO OPTIMAL" if rang == 1 else ""
    print(f"   {rang}. {noms_scenarios[i]:<24s} : score = {scores[i]:.4f}{etoile}")
 
ecart = abs(scores[0] - scores[1]) / max(scores) * 100
print(f"\n   Ecart relatif entre les deux scenarios : {ecart:.1f} %")
 
# --- Detail de la contribution de chaque critere au score ---
print("\n[DETAIL] CONTRIBUTION DE CHAQUE CRITERE AU SCORE (poids x perf_norm)")
print("-" * 74)
print("   " + " " * 22 + "".join(f"{c.split(' - ')[0]:>9s}" for c in noms_criteres))
for i, nom in enumerate(noms_scenarios):
    contrib = norm[i, :] * poids
    ligne = "".join(f"{contrib[j]:9.3f}" for j in range(n))
    print(f"   {nom:<22s}{ligne}")
 
print("\n" + "=" * 74)
print("  CONCLUSION : le scenario au score le plus eleve est retenu comme")
print("  scenario optimal, conformement a la procedure AHP de Saaty (1980).")
print("=" * 74)
 
 
# =============================================================================
# 5) GRAPHIQUES (optionnel - pour illustrer dans le rapport)
# =============================================================================
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
 
    # Dossier de sortie = le dossier ou se trouve ce script
    DOSSIER = os.path.dirname(os.path.abspath(__file__))
    BLUE, ORANGE = "#2E75B6", "#C55A11"
 
    # -- Graphe 1 : poids des criteres --
    fig, ax = plt.subplots(figsize=(8, 4))
    ordre = np.argsort(poids)
    ax.barh([noms_criteres[i].split(' - ')[1] for i in ordre],
            [poids[i]*100 for i in ordre], color=BLUE, edgecolor="white")
    for i, idx in enumerate(ordre):
        ax.text(poids[idx]*100 + 0.4, i, f"{poids[idx]*100:.1f} %",
                va="center", fontsize=9)
    ax.set_xlabel("Poids du critere (%)")
    ax.set_title(f"Poids des criteres par AHP  (CR = {CR:.3f} < 0,10)",
                 fontweight="bold", color="#1F4E79")
    plt.tight_layout()
    plt.savefig(os.path.join(DOSSIER, "AHP_poids.png"), dpi=150, facecolor="white")
    plt.close()
 
    # -- Graphe 2 : scores globaux --
    fig, ax = plt.subplots(figsize=(6, 4))
    cols = [BLUE, ORANGE]
    b = ax.bar(noms_scenarios, scores, color=cols, edgecolor="white", width=0.5)
    for bi, s in zip(b, scores):
        ax.text(bi.get_x()+bi.get_width()/2, s+0.01, f"{s:.3f}",
                ha="center", fontweight="bold")
    ax.set_ylabel("Score global pondere")
    ax.set_ylim(0, 1)
    ax.set_title("Score AHP global des deux scenarios",
                 fontweight="bold", color="#1F4E79")
    plt.tight_layout()
    plt.savefig(os.path.join(DOSSIER, "AHP_scores.png"), dpi=150, facecolor="white")
    plt.close()
 
    print("\nGraphiques enregistres dans le dossier du script :")
    print("   -> " + os.path.join(DOSSIER, "AHP_poids.png"))
    print("   -> " + os.path.join(DOSSIER, "AHP_scores.png"))
except ImportError:
    print("\n(matplotlib non installe : graphiques ignores)")