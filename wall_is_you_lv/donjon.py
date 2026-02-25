from fltk import *
import random

# Initialisation globale (à mettre AVANT les fonctions)
taille_case = 100
stock_tresor = 3
tresor_pose = None
donjon = []      
aventurier = []  
dragons = []     
intention = []

# 1. GESTION DU DONJON ET DES SALLES
SYMBOLES = {
    #4 passages
    '╬': (True, True, True, True),

    #3 passages (T) 
    '╠': (True, True, True, False), # Ouvert Haut, Droite, Bas
    '╦': (False, True, True, True), # Ouvert Droite, Bas, Gauche
    '╣': (True, False, True, True), # Ouvert Haut, Bas, Gauche
    '╩': (True, True, False, True), # Ouvert Haut, Droite, Gauche

    #2 passages (Angles et Lignes)
    '╔': (False, True, True, False), # Angle Haut-Gauche (vers Droite et Bas)
    '╗': (False, False, True, True), # Angle Haut-Droite
    '╚': (True, True, False, False), # Angle Bas-Gauche
    '╝': (True, False, False, True), # Angle Bas-Droite
    '═': (False, True, False, True), # Horizontal
    '║': (True, False, True, False), # Vertical

    #1 passage (Culs-de-sac / Extrémités)
    '╥': (False, False, True, False), # Pointe vers le Bas
    '╨': (True, False, False, False), # Pointe vers le Haut
    '╡': (False, False, False, True), # Pointe vers la Gauche
    '╞': (False, True, False, False)  # Pointe vers la Droite
}

SYMBOLES_INVERSE = {v: k for k, v in SYMBOLES.items()}

IMAGES_SALLES = {
    (True, True, True, True): '11b.png',   
    (True, True, True, False): '14b.png',  # T ouvert à Droite
    (False, True, True, True): '12b.png',  # T ouvert en Bas
    (True, False, True, True): '15b.png',  # T ouvert à Gauche
    (True, True, False, True): '13b.png',  # T ouvert en Haut
    (False, True, True, False): '9b.png',  # Angle Droite-Bas
    (False, False, True, True): '8b.png',  # Angle Bas-Gauche
    (True, True, False, False): '10b.png', # Angle Haut-Droite
    (True, False, False, True): '7b.png',  # Angle Haut-Gauche
    (False, True, False, True): '5b.png',  # Horizontal
    (True, False, True, False): '6b.png',  # Vertical
    (False, False, True, False): '1b.png', # Cul-de-sac Bas
    (True, False, False, False): '2b.png', # Cul-de-sac Haut
    (False, False, False, True): '3b.png', # Cul-de-sac Gauche
    (False, True, False, False): '4b.png'  # Cul-de-sac Droite
}

def sauvegarder_partie(nom_fichier):
    """
    Enregistre l'état actuel du jeu dans un fichier.
    """
    with open(nom_fichier, 'w', encoding='utf-8') as f:
        # 1. Écriture de la grille du donjon
        for lig in range(len(donjon)):
            ligne_str = ""
            for colonne in range(len(donjon[0])):
                salle = donjon[lig][colonne]
                symbole = SYMBOLES_INVERSE.get(salle, '╬')
                ligne_str += symbole + " "
            f.write(ligne_str.strip() + "\n")
        
        # 2. Position de l'aventurier
        f.write(f"A {aventurier[0][0]} {aventurier[0][1]}\n")
        
        # 3. Position des dragons
        for d in dragons:
            f.write(f"D {d[0][0]} {d[0][1]} {d[1]}\n")
    print("Partie sauvegardée dans", nom_fichier)

def tourner(salle):
    """
    Fait pivoter une salle de 90 degrés dans le sens horaire.
    """
    nouvelle_salle= (salle[3], salle[0], salle[1], salle[2])
    return nouvelle_salle

def connecte(salle1, salle2, direction):
    """
    Vérifie si un passage existe entre deux salles adjacentes.
    salle1: tuple de la salle de départ.
    salle2: tuple de la salle d'arrivée.
    direction: entier (0:H, 1:D, 2:B, 3:G).
    return: booléen qui indiquent si le passage est ouvert des deux côtés.
    """
    if direction == 0:
        return salle1[0] and salle2[2]
    elif direction == 1:
        return salle1[1] and salle2[3]
    elif direction == 2:
        return salle1[2] and salle2[0]
    elif direction == 3:
        return salle1[3] and salle2[1]
    return False

def tour_aventurier():
    global dragons, aventurier, tresor_pose, mode, intention
    
    for pos in intention[1:]:
        aventurier[0] = pos
        dessiner_jeu()
        mise_a_jour()
        attente(0.0001)

        # 1. Gestion du trésor : s'il le voit, il le ramasse et s'arrête 
        if tresor_pose == pos:
            tresor_pose = None
            print("Trésor récupéré !")
            break 

        dragon_present = None
        for d in dragons:
            if d[0] == pos:
                dragon_present = d
                break
        
        if dragon_present:
            if aventurier[1] >= dragon_present[1]:
                aventurier[1] += 1
                print(f"Dragon vaincu ! Niveau : {aventurier[1]}")
                dragons.remove(dragon_present)
            else:
                # Défaite 
                attente(0.5)
                afficher_defaite()
                mode = 'MENU'
                return

    if len(dragons) == 0:
        dessiner_jeu()
        mise_a_jour()
        attente(0.5)
        afficher_victoire()
    else:
        deplacer_dragons()

def deplacer_dragons():
    """
    Déplace chaque dragon d'une case de manière aléatoire.
    Le dragon ne peut se déplacer que vers une case connectée.
    """
    global dragons, mode
    for drag in dragons:
        ligne, colonne = drag[0]
        possibles = []
        
        directions = [(-1, 0, 0), (0, 1, 1), (1, 0, 2), (0, -1, 3)]
        
        for dligne, dcolonne, di in directions:
            nligne, ncolonne = ligne + dligne, colonne + dcolonne
            if 0 <= nligne < len(donjon) and 0 <= ncolonne < len(donjon[0]):
                if connecte(donjon[ligne][colonne], donjon[nligne][ncolonne], di):
                    possibles.append((nligne, ncolonne))

        if possibles:
            drag[0] = random.choice(possibles) 
            
        if drag[0] == aventurier[0]:
            if aventurier[1] < drag[1]:
                print("GAME OVER") # Défaite
                mode = 'MENU'


def charger_niveau(nom_fichier):
    """
    Charge la configuration d'un donjon depuis un fichier texte.
    Lit les symboles de salles, les positions de l'aventurier ('A'),
    les dragons normaux ('D') et les dragons spéciaux ('S').
    """
    try:
        with open(nom_fichier, 'r', encoding='utf-8') as f:
            lignes = f.readlines()
    except FileNotFoundError:
        print(f"Erreur : Le fichier {nom_fichier} est introuvable.")
        return [], [(0,0), 1], []

    nouveau_donjon = []
    nouveau_dragon = []
    nouvel_aventurier = [(0, 0), 1]  # Position par défaut et niveau initial

    for ligne in lignes:
        elements = ligne.split()
        if not elements:
            continue
        
        # L'Aventurier
        if elements[0] == 'A':
            lig = int(elements[1])
            col = int(elements[2])
            # On peut aussi lire le niveau de départ si présent
            nouvel_aventurier = [(lig, col), 1]
            
        # Dragon 
        elif elements[0] == 'D':
            lig = int(elements[1])
            col = int(elements[2])
            niv = int(elements[3])
            # Format : [ (position), niveau, type ]
            nouveau_dragon.append([(lig, col), niv, "normal"])

            
        # Les Salles du Donjon
        else:
            ligne_salles = []
            for symbole in elements:
                if symbole in SYMBOLES:
                    ligne_salles.append(SYMBOLES[symbole])
                else:
                    # Case vide ou inconnue (mur plein)
                    ligne_salles.append((False, False, False, False)) 
            nouveau_donjon.append(ligne_salles)
            
    return nouveau_donjon, nouvel_aventurier, nouveau_dragon


donjon = [
    [(False, True, True, False), (False, False, True, False) ],
    [(True, True, False, False), (True, False, True, False) ]
]
taille_case = 100
donjon, aventurier, dragons = charger_niveau('niveau1.txt')

def generer_niveau_aleatoire(nb_lignes, nb_colonnes):
    """
    Génère un labyrinthe parfait (toujours soluble) et place
    l'aventurier et des dragons.
    """
    # 1. Initialisation d'une grille vide (tout fermé = False)
    # Format temporaire : [Haut, Droite, Bas, Gauche] modifiable
    grille = [[[False, False, False, False] for _ in range(nb_colonnes)] for _ in range(nb_lignes)]
    visites = [[False for _ in range(nb_colonnes)] for _ in range(nb_lignes)]
    
    # 2. Algorithme de génération
    stack = [(0, 0)] # On commence en haut à gauche
    visites[0][0] = True
    
    while stack:
        l, c = stack[-1] # Position actuelle
        
        # Trouver les voisins non visités
        voisins = []
        directions = [(-1, 0, 0, 2), (0, 1, 1, 3), (1, 0, 2, 0), (0, -1, 3, 1)]
        
        for dl, dc, mur_ici, mur_laba in directions:
            nl, nc = l + dl, c + dc
            if 0 <= nl < nb_lignes and 0 <= nc < nb_colonnes and not visites[nl][nc]:
                voisins.append((nl, nc, mur_ici, mur_laba))
        
        if voisins:
            # Choisir un voisin au hasard
            nl, nc, mur_ici, mur_laba = random.choice(voisins)
            
            # Ouvrir les murs entre la case actuelle et le voisin
            grille[l][c][mur_ici] = True
            grille[nl][nc][mur_laba] = True
            
            # Marquer comme visité et empiler
            visites[nl][nc] = True
            stack.append((nl, nc))
        else:
            stack.pop()
            
    # 3. Conversion de la grille en Tuples
    nouveau_donjon = []
    for l in range(nb_lignes):
        ligne_salles = []
        for c in range(nb_colonnes):
            # On transforme la liste [True, False...] en tuple (True, False...)
            ligne_salles.append(tuple(grille[l][c]))
        nouveau_donjon.append(ligne_salles)

    # 4. Placement de l'aventurier (en haut à gauche par défaut)
    nouvel_aventurier = [(0, 0), 1] 

    # 5. Placement des dragons aléatoire mais pas sur l'aventurier
    nouveaux_dragons = []
    # On met un nombre de dragons proportionnel à la taille 
    nb_dragons = max(1, (nb_lignes * nb_colonnes) // 10)
    
    candidats = []
    for l in range(nb_lignes):
        for c in range(nb_colonnes):
            if (l, c) != (0, 0): 
                candidats.append((l, c))
    
    positions_dragons = random.sample(candidats, nb_dragons)
    
    for pos in positions_dragons:
        # 1 chance sur 5 d'être un dragon spécial
        type_dragon = "special" if random.random() < 0.2 else "normal"
        niveau_dragon = random.randint(1, 2) 
        nouveaux_dragons.append([pos, niveau_dragon, type_dragon])

    return nouveau_donjon, nouvel_aventurier, nouveaux_dragons

def dessiner_jeu():
    efface_tout()
    taille_case = 100

    for lig in range(len(donjon)):
        for colonne in range(len(donjon[0])):
            x = colonne * taille_case
            y = lig * taille_case
            salle = donjon[lig][colonne]
            
            # 1. Dessin de l'image de la salle 
            nom_img = IMAGES_SALLES.get(salle)
            if nom_img:
                chemin_complet = "IMAGES WALL IS YOU/" + nom_img
                image(x + 50, y + 50, chemin_complet, largeur=100, hauteur=100)
            
            # Bordure de la case
            rectangle(x, y, x + taille_case, y + taille_case, couleur='black')

    # 2. Dessin des Dragons avec l'image 
    for dragon in dragons:
        pos_d, niveau_d, type_d = dragon[0], dragon[1], dragon[2]
        x_d, y_d = pos_d[1] * taille_case + 50, pos_d[0] * taille_case + 50
            
        image(x_d, y_d, "dragon.png", largeur=80, hauteur=80)
        texte(x_d, y_d, str(niveau_d), couleur='white', ancrage='center', taille=15)

    # 3. Dessin de l'Aventurier avec l'image 
    pos_a, niveau_a = aventurier[0], aventurier[1]
    x_a, y_a = pos_a[1] * taille_case + 50, pos_a[0] * taille_case + 50
    image(x_a, y_a, "aventurier.png", largeur=80, hauteur=80)
    texte(x_a, y_a, str(niveau_a), couleur='white', ancrage='center', taille=15)
    if tresor_pose is not None :
        l_tresor = tresor_pose[0]
        c_tresor = tresor_pose[1]
        x_tresor = c_tresor * taille_case + 50
        y_tresor = l_tresor * taille_case + 50
        image(x_tresor, y_tresor, "diamond blue.png", largeur=45, hauteur=40)
    
    for i in range(len(intention)- 1):
        pos = intention[i]
        lig1 = pos[0]
        col1 = pos[1]
        case_arrivee = intention[i + 1]
        lig2 = case_arrivee[0]
        col2 = case_arrivee[1]
        x1 = col1 * taille_case + 50
        y1 = lig1 * taille_case + 50
        x2 = col2 * taille_case + 50
        y2 = lig2 * taille_case + 50
        ligne(x1, y1, x2, y2, couleur='red', epaisseur=5)

    largeur = largeur_fenetre()
    hauteur = hauteur_fenetre()

    # Rectangle de fond sur toute la largeur
    rectangle(0, 400, largeur, hauteur, couleur='black', remplissage='lightgray')

    texte(10, 410, "CLIC G : Tourner salle", taille=10)
    texte(10, 430, "CLIC D : Poser trésor", taille=10)
    
    milieu = largeur // 2
    texte(milieu, 410, "ESPACE : Tour aventurier", taille=10)
    texte(milieu, 430, "S : Sauvegarder", taille=10)
    
    texte(10, 460, "ESC : Menu | R : Recommencer", taille=10, couleur='red')

def dessiner_menu():
    efface_tout()
    milieu = largeur_fenetre() // 2 
    
    texte(milieu, 80, "WALL IS YOU", ancrage='center', taille=30, couleur='blue')
    
    texte(milieu, 150, "--- NOUVELLE PARTIE ---", ancrage='center', taille=14, couleur='black')
    texte(milieu, 180, "[A] Niveau 1", ancrage='center', taille=12, couleur='purple')
    texte(milieu, 210, "[B] Niveau 2", ancrage='center', taille=12, couleur='purple')
    texte(milieu, 240, "[H] Niveau Aléatoire", ancrage='center', taille=12, couleur='red') 
    
    texte(milieu, 300, "--- CONTINUER ---", ancrage='center', taille=14, couleur='black')
    texte(milieu, 330, "[C] Charger sauvegarde.txt", ancrage='center', taille=12, couleur='darkgreen')

def calculer_automatique():
    global intention
    depart = aventurier[0]
    file = [(depart, [depart])]
    visites = [depart]
    
    meilleur_chemin = None
    niveau_max = -1

    while len(file) > 0:
        curr, chemin = file.pop(0)
        l, c = curr
        
        if tresor_pose == curr:
            intention = chemin
            return

        for d_pos, d_niv, d_type in dragons:
            if d_pos == curr and d_niv > niveau_max:
                niveau_max = d_niv
                meilleur_chemin = chemin

        dirs = [(-1, 0, 0), (0, 1, 1), (1, 0, 2), (0, -1, 3)]
        for dl, dc, di in dirs:
            nl, nc = l + dl, c + dc
            if 0 <= nl < len(donjon) and 0 <= nc < len(donjon[0]):
                if (nl, nc) not in visites:
                
                    if connecte(donjon[l][c], donjon[nl][nc], di):
                        visites.append((nl, nc))
                        file.append(((nl, nc), chemin + [(nl, nc)]))
    
    if meilleur_chemin:
        intention = meilleur_chemin
    else:
        intention = [depart] 


def afficher_victoire():
    global mode
    efface_tout()
    texte(300, 185, "VICTOIRE !", couleur='gold', ancrage='center', taille=40)
    texte(300, 225, "Cliquez pour continuer", couleur='black', ancrage='center', taille=10)
    
    mise_a_jour()
    attend_ev() 
    mode = 'MENU'

def afficher_defaite():
    global mode
    efface_tout()
    texte(300, 185, "GAME OVER...", couleur='red', ancrage='center', taille=40)
    texte(300, 225, "Cliquez pour continuer", couleur='black', ancrage='center', taille=10)
    
    mise_a_jour()
    attend_ev() 
    mode = 'MENU'

# 3. LE PROGRAMME PRINCIPAL 

cree_fenetre(600, 500)

mode = 'MENU'  

while True:
    # 1. GESTION DE L'AFFICHAGE SELON LE MODE
    if mode == 'MENU':
        dessiner_menu()
    elif mode == 'JEU':
        dessiner_jeu()
    
    mise_a_jour()

    # 2. GESTION DES ÉVÉNEMENTS
    ev = donne_ev()
    ty = type_ev(ev)

    if ty == 'Quitte':
        break

    # SI ON EST DANS LE MENU 
    if mode == 'MENU':
        if ty == 'Touche':
            t = touche(ev)
            
            # Chargement Niveau 1
            if t == 'a':
                res = charger_niveau('niveau1.txt')
                # On vérifie que le donjon n'est pas vide (len > 0)
                if len(res[0]) > 0: 
                    donjon, aventurier, dragons = res
                    intention = [aventurier[0]]
                    mode = 'JEU'
            
            # Chargement Niveau 2
            elif t == 'b':
                res = charger_niveau('niveau2.txt')
                if len(res[0]) > 0: # Si le fichier existe et n'est pas vide
                    donjon, aventurier, dragons = res
                    intention = [aventurier[0]]
                    mode = 'JEU'
                else:
                    print("Impossible de lancer le niveau 2 : fichier manquant ou vide.")

            elif t == 'h':
                # On génère 4 lignes et 6 colonnes pour que ça rentre dans l'écran
                donjon, aventurier, dragons = generer_niveau_aleatoire(4, 6)
                
                intention = [aventurier[0]]
                stock_tresor = 3
                tresor_pose = None
                mode = 'JEU'

            # Chargement Sauvegarde
            elif t == 'c':
                try:
                    res = charger_niveau('sauvegarde.txt')
                    if len(res[0]) > 0:
                        donjon, aventurier, dragons = res
                        intention = [aventurier[0]]
                        mode = 'JEU'
                except:
                    print("Aucune sauvegarde trouvée.")
    

    # SI ON EST DANS LE JEU
    elif mode == 'JEU':
        calculer_automatique()
        dessiner_jeu()
        if ty == 'Touche':
            t = touche(ev)
            if t == 'Escape': 
                mode = 'MENU'
            elif t == 'space':
                tour_aventurier()
                intention = [aventurier[0]]
            elif t == 's': # 's' pour Sauvegarder 
                sauvegarder_partie("sauvegarde.txt")

        elif ty == 'ClicGauche': 
            mx, my = abscisse(ev), ordonnee(ev)
            colonne, lig = mx // taille_case, my // taille_case

            if 0 <= lig < len(donjon) and 0 <= colonne < len(donjon[0]):
                donjon[lig][colonne] = tourner(donjon[lig][colonne])
                calculer_automatique()
                 
        
        elif ty == 'ClicDroit': # Pose du trésor 
            mx, my = abscisse(ev), ordonnee(ev)
            colonne, lig = mx // taille_case, my // taille_case
            if stock_tresor > 0 and tresor_pose is None:
                tresor_pose = (lig, colonne)
                stock_tresor -= 1
                print("Trésor posé ! Il en reste :", stock_tresor)
            else:
                print("Impossible de poser un trésor (plus de stock ou déjà posé)")
ferme_fenetre()