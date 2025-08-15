# 📋 MANUEL D'UTILISATION - TAKEOFF AI

**Version 1.0 - Janvier 2025**  
**Système d'estimation de construction avec Intelligence Artificielle**

---

## 📑 Table des matières

1. [Introduction](#introduction)
2. [Installation et configuration](#installation-et-configuration)
3. [Interface utilisateur](#interface-utilisateur)
4. [Gestion des projets](#gestion-des-projets)
5. [Outils de mesure](#outils-de-mesure)
6. [Catalogue de produits](#catalogue-de-produits)
7. [Assistant IA](#assistant-ia)
8. [Exports et rapports](#exports-et-rapports)
9. [Paramètres avancés](#paramètres-avancés)
10. [Dépannage](#dépannage)
11. [FAQ](#faq)
12. [Support et contact](#support-et-contact)

---

## 🎯 Introduction

### Qu'est-ce que TAKEOFF AI ?

TAKEOFF AI est une application web professionnelle dédiée à l'estimation de construction. Elle combine la puissance de l'intelligence artificielle Claude d'Anthropic avec des outils de mesure précis pour analyser vos plans de construction et générer automatiquement des estimations de coûts.

### À qui s'adresse cette application ?

- **Architectes** : Analyse des surfaces, validation des dimensions
- **Entrepreneurs généraux** : Estimation des matériaux et coûts
- **Estimateurs** : Quantification précise des travaux
- **Ingénieurs** : Calculs techniques et vérifications
- **Maîtres d'ouvrage** : Contrôle des budgets et devis

### Principales fonctionnalités

✅ **Visualisation PDF avancée** avec zoom et navigation  
✅ **5 outils de mesure** : distance, surface, périmètre, angle, calibration  
✅ **Assistant IA intégré** avec 60+ profils d'experts métier  
✅ **Catalogue de produits** personnalisable avec prix  
✅ **Gestion de projets** avec sauvegarde et export  
✅ **Rapports automatisés** en CSV, JSON, PDF  

---

## ⚙️ Installation et configuration

### Prérequis système

- **Système d'exploitation** : Windows 10/11, macOS 10.15+, Linux Ubuntu 18.04+
- **Python** : Version 3.8 ou supérieure
- **Mémoire RAM** : 4 GB minimum (8 GB recommandé)
- **Espace disque** : 2 GB libre
- **Connexion internet** : Requise pour l'assistant IA

### Installation locale

#### Option 1 : Installation directe

```bash
# Cloner le projet
git clone https://github.com/votre-repo/takeoff-ai.git
cd takeoff-ai

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement (Windows)
venv\Scripts\activate

# Activer l'environnement (macOS/Linux)
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

#### Option 2 : Utilisation sur Hugging Face Spaces

1. Rendez-vous sur : `https://huggingface.co/spaces/votre-username/takeoff-ai`
2. L'application se lance automatiquement dans votre navigateur
3. Aucune installation requise

### Configuration de l'API Claude

#### Obtenir une clé API Anthropic

1. **Créer un compte** sur [console.anthropic.com](https://console.anthropic.com/)
2. **Générer une clé API** dans les paramètres
3. **Noter la clé** (elle ne sera affichée qu'une fois)

#### Configurer la clé dans l'application

**Méthode 1 : Interface utilisateur**
1. Ouvrir TAKEOFF AI
2. Dans la barre latérale, section "Configuration"
3. Saisir votre clé API dans le champ "Clé API Claude"
4. Cliquer sur "Valider"

**Méthode 2 : Variable d'environnement**
```bash
# Windows
set ANTHROPIC_API_KEY=votre_cle_api_ici

# macOS/Linux
export ANTHROPIC_API_KEY=votre_cle_api_ici
```

**Méthode 3 : Fichier .env**
```
# Créer un fichier .env dans le dossier racine
ANTHROPIC_API_KEY=votre_cle_api_ici
```

---

## 🖥️ Interface utilisateur

### Vue d'ensemble

L'interface TAKEOFF AI est organisée en plusieurs zones principales :

```
┌─────────────────────────────────────────────────────────┐
│                    TAKEOFF AI                           │
│        Système d'estimation de construction             │
├─────────────────┬───────────────────────┬───────────────┤
│                 │                       │               │
│   BARRE        │    OUTILS ET          │   ASSISTANT   │
│   LATÉRALE     │    MESURES            │   IA          │
│                 │                       │               │
│   • Menu       │   📐 Mesures          │   🤖 Chat     │
│   • Config     │   📦 Catalogue        │   💡 Conseils │
│   • Profils    │   📊 Totaux           │   📄 Analyse  │
│   • Projets    │   ⚙️ Options          │               │
│                 │                       │               │
├─────────────────┴───────────────────────┴───────────────┤
│                                                         │
│                    DOCUMENT PDF                         │
│                                                         │
│   [◀] Page 1/10 [▶]     📄 plan.pdf     📏 Cal: 1.5cm │
│                                                         │
│   ┌─────────────────────────────────────────────────┐   │
│   │                                                 │   │
│   │              PLAN DE CONSTRUCTION               │   │
│   │                                                 │   │
│   │         [Votre PDF s'affiche ici]              │   │
│   │                                                 │   │
│   └─────────────────────────────────────────────────┘   │
│                                                         │
├─────────────────────────────────────────────────────────┤
│  Outil: Distance  │  Produit: Béton 25MPa  │ Cal: 1.5cm │
└─────────────────────────────────────────────────────────┘
```

### Barre latérale

#### Menu fichier
- **🆕 Nouveau projet** : Crée un projet vierge
- **📁 Ouvrir projet** : Charge un fichier .tak existant
- **💾 Sauvegarder** : Export du projet en cours
- **📋 Projets récents** : Accès rapide aux derniers projets

#### Configuration
- **🔑 Clé API Claude** : Configuration de l'assistant IA
- **👤 Profil expert** : Sélection du profil métier
- **📏 Système d'unités** : Métrique ou impérial
- **🎯 Accrochage** : Paramètres de précision

### Zone principale

#### Onglets des outils
- **📐 Mesures** : Outils de mesure et gestion
- **📦 Catalogue** : Produits et matériaux
- **📊 Totaux** : Récapitulatifs et calculs
- **⚙️ Options** : Paramètres d'affichage

#### Visualiseur PDF
- **Navigation** : Boutons précédent/suivant
- **Zoom** : Curseur de 0.5x à 3x
- **Coordonnées** : Clic pour placer des points
- **Mesures** : Affichage des annotations

---

## 📁 Gestion des projets

### Créer un nouveau projet

1. **Cliquer** sur "🆕 Nouveau projet"
2. **Charger un PDF** via le bouton "Charger un PDF"
3. **Sélectionner** votre fichier de plan
4. Le projet est automatiquement initialisé

### Calibrer l'échelle

> ⚠️ **Important** : La calibration est essentielle pour obtenir des mesures précises.

1. **Sélectionner** l'outil "Calibration"
2. **Cliquer** sur deux points d'une distance connue sur le plan
3. **Saisir** la distance réelle dans la boîte de dialogue
4. **Choisir** l'unité (mm, cm, m, in, ft)
5. **Valider** pour appliquer la calibration

**Exemple :** Si vous mesurez un mur de 5 mètres représenté par 100 pixels, la calibration sera de 0.05 m/pixel.

### Sauvegarder un projet

#### Sauvegarde manuelle
1. **Cliquer** sur "💾 Sauvegarder projet"
2. **Cliquer** sur "📥 Télécharger le projet"
3. Le fichier `.tak` est téléchargé

#### Sauvegarde automatique
- Les mesures sont sauvées automatiquement
- L'état du projet est conservé dans la session

### Ouvrir un projet existant

1. **Cliquer** sur "📁 Ouvrir un projet"
2. **Sélectionner** votre fichier `.tak`
3. Le projet se charge avec toutes les mesures

### Projets récents

Les 5 derniers projets ouverts apparaissent dans la liste "📋 Projets récents" pour un accès rapide.

---

## 📐 Outils de mesure

### Vue d'ensemble des outils

TAKEOFF AI propose 5 outils de mesure professionnels :

| Outil | Icône | Usage | Points requis | Résultat |
|-------|-------|-------|---------------|----------|
| Distance | 📏 | Mesures linéaires | 2 | Longueur |
| Surface | 📐 | Aires et superficies | 3+ | m² ou pi² |
| Périmètre | 📏 | Contours ouverts | 3+ | Longueur totale |
| Angle | 📐 | Angles entre lignes | 3 | Degrés (°) |
| Calibration | 🎯 | Définir l'échelle | 2 | Facteur d'échelle |

### Outil Distance

**Usage** : Mesurer des longueurs, largeurs, hauteurs

**Procédure** :
1. Sélectionner l'outil "Distance"
2. Cliquer sur le point de départ
3. Cliquer sur le point d'arrivée
4. La mesure s'affiche automatiquement

**Applications** :
- Dimensions de pièces
- Longueurs de murs
- Espacements entre éléments
- Vérification de cotes

### Outil Surface

**Usage** : Calculer des aires de formes quelconques

**Procédure** :
1. Sélectionner l'outil "Surface"
2. Cliquer sur chaque sommet du polygone
3. Cliquer sur "Valider" ou compléter le contour
4. L'aire est calculée via la formule du lacet

**Applications** :
- Surfaces habitables
- Aires de planchers
- Superficies de toitures
- Zones de revêtement

**💡 Astuce** : Pour les formes complexes, procédez par découpage en polygones simples.

### Outil Périmètre

**Usage** : Mesurer des contours et périmètres

**Procédure** :
1. Sélectionner l'outil "Périmètre"
2. Cliquer sur chaque point du contour
3. La longueur totale s'accumule automatiquement

**Applications** :
- Périmètres de bâtiments
- Longueurs de clôtures
- Contours de terrains
- Linéaires de finition

### Outil Angle

**Usage** : Mesurer des angles entre deux lignes

**Procédure** :
1. Sélectionner l'outil "Angle"
2. Cliquer sur le premier point
3. Cliquer sur le sommet de l'angle
4. Cliquer sur le troisième point
5. L'angle est calculé automatiquement

**Applications** :
- Angles de toiture
- Coupes d'assemblage
- Vérification d'orthogonalité
- Contrôle géométrique

### Mode orthogonal (ORTHO)

Le mode orthogonal contraint les mesures aux angles standards.

**Activation** :
- Cocher "Mode Ortho" dans les options
- Maintenir `Shift` pendant le tracé

**Angles disponibles** : 0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°

**Avantages** :
- Mesures précises sur plans techniques
- Respect des normes architecturales
- Gain de temps sur les tracés répétitifs

### Système d'accrochage

L'accrochage automatique améliore la précision des mesures.

**Points d'accrochage** :
- Extrémités de lignes existantes
- Intersections de lignes
- Milieux de segments
- Points de mesures précédentes

**Configuration** :
- Activer/désactiver dans les paramètres
- Ajuster le seuil de sensibilité (5-50 pixels)

---

## 📦 Catalogue de produits

### Structure du catalogue

Le catalogue organise les produits par catégories hiérarchiques :

```
📦 Catalogue de produits
├── 🏗️ Béton
│   ├── Béton 25 MPa (150$/m³)
│   ├── Béton 30 MPa (165$/m³)
│   └── Béton 35 MPa (180$/m³)
├── 🔩 Acier d'armature
│   ├── Barre 10M (0.85$/m)
│   ├── Barre 15M (1.90$/m)
│   └── Treillis métallique (2.50$/pi²)
├── 📏 Coffrages
├── 🧱 Isolation
├── 🏠 Gypse
└── 🏠 Toiture
```

### Utiliser le catalogue

#### Sélectionner un produit
1. Aller dans l'onglet "📦 Catalogue"
2. Choisir une catégorie
3. Cliquer sur le produit souhaité
4. Le produit devient actif pour les prochaines mesures

#### Associer un produit à une mesure

**Méthode automatique** :
- Sélectionner un produit avant de mesurer
- L'association se fait automatiquement

**Méthode manuelle** :
- Effectuer la mesure
- Choisir le produit dans la boîte de dialogue
- Valider l'association

### Gérer le catalogue

#### Ajouter un produit
1. Ouvrir l'onglet "📦 Catalogue"
2. Cliquer sur "➕ Ajouter produit"
3. Remplir les informations :
   - Nom du produit
   - Catégorie
   - Dimensions
   - Prix unitaire
   - Unité de mesure
   - Couleur d'affichage

#### Modifier un produit
1. Cliquer sur "✏️" à côté du produit
2. Modifier les champs souhaités
3. Sauvegarder les modifications

#### Supprimer un produit
1. Cliquer sur "🗑️" à côté du produit
2. Confirmer la suppression

#### Import/Export du catalogue

**Exporter** :
1. Onglet "Catalogue" → "📤 Exporter"
2. Choisir le format (JSON recommandé)
3. Télécharger le fichier

**Importer** :
1. Onglet "Catalogue" → "📥 Importer"
2. Sélectionner votre fichier JSON
3. Valider l'import

---

## 🤖 Assistant IA

### Configuration de l'assistant

L'assistant IA utilise Claude d'Anthropic pour fournir des conseils d'expert.

#### Profils d'experts disponibles

TAKEOFF AI propose plus de 60 profils spécialisés :

**Construction générale** :
- Entrepreneur général
- Architecte
- Ingénieur structure
- Technologue

**Corps de métiers** :
- Électricien
- Plombier
- Maçon/Briqueteur
- Charpentier
- Couvreur

**Spécialités** :
- CVCA/HVAC
- Ascenseurs
- Décontamination
- LEED/Efficacité énergétique

**Calculs techniques** :
- Calculs de poutres
- Calculs de colonnes
- Calculs de linteaux
- Calculs de fondations

#### Sélectionner un profil
1. Barre latérale → "👤 Profil Expert"
2. Choisir le profil adapté à votre projet
3. L'assistant adapte ses réponses au domaine d'expertise

### Utiliser l'assistant IA

#### Interface de chat
- Zone de conversation avec historique
- Champ de saisie en bas
- Boutons d'actions rapides

#### Poser des questions
1. Taper votre question dans le champ de saisie
2. Appuyer sur Entrée ou cliquer sur Envoyer
3. L'assistant analyse le contexte et répond

**Exemples de questions** :
- "Quel type de béton recommandes-tu pour cette dalle ?"
- "Comment calculer la quantité d'armature nécessaire ?"
- "Quels sont les codes à respecter pour cette structure ?"

#### Actions automatiques

**📄 Analyser PDF** :
- Extrait et analyse le texte du plan
- Identifie les éléments techniques
- Propose des recommandations

**💡 Suggestions** :
- Analyse les mesures existantes
- Suggère des mesures complémentaires
- Optimise l'estimation

**🗑️ Effacer chat** :
- Remet à zéro la conversation
- Conserve le profil sélectionné

### Contexte intelligent

L'assistant IA dispose automatiquement des informations suivantes :

- **Projet actuel** : Nom du fichier, calibration
- **Mesures effectuées** : Types, quantités, produits associés
- **Profil expert** : Spécialisation et expertise
- **Historique** : Conversations précédentes

Cette contextualisation permet des réponses précises et pertinentes.

---

## 📊 Exports et rapports

### Types d'exports disponibles

TAKEOFF AI propose plusieurs formats d'export pour s'adapter à vos workflows :

| Format | Extension | Usage | Contenu |
|--------|-----------|-------|---------|
| CSV | `.csv` | Tableurs | Mesures détaillées |
| JSON | `.json` | Applications | Données structurées |
| TXT | `.txt` | Rapports | Résumé lisible |
| TAK | `.tak` | TAKEOFF AI | Projet complet |

### Export des mesures

#### Procédure d'export
1. Onglet "⚙️ Options"
2. Section "📤 Export"
3. Choisir le format souhaité
4. Cliquer sur "📥 Exporter les données"
5. Le fichier se télécharge automatiquement

#### Contenu des exports

**Format CSV** :
```csv
Type,Nom,Valeur,Unité,Page,Produit,Catégorie,Prix unitaire
distance,Distance_1,5.50,m,1,Béton 25 MPa,Béton,150.00
area,Surface_1,25.30,m²,1,Gypse régulier,Gypse,12.00
```

**Format JSON** :
```json
{
  "project": {
    "filename": "plan_maison.pdf",
    "measurements": [
      {
        "type": "distance",
        "label": "Distance_1",
        "value": 5.50,
        "unit": "m",
        "product": {
          "name": "Béton 25 MPa",
          "price": 150.00
        }
      }
    ]
  }
}
```

### Rapports de totaux

#### Accéder aux totaux
1. Onglet "📊 Totaux"
2. Visualiser le tableau récapitulatif
3. Consulter le total général

#### Contenu du rapport
- **Par produit** : Quantités et prix totaux
- **Par catégorie** : Regroupement logique
- **Total général** : Somme globale du projet

#### Export des totaux
- **📥 Télécharger CSV** : Format tableur
- **📥 Télécharger JSON** : Format données

### Impression et PDF

Pour imprimer ou créer un PDF :

1. **Navigateur** → Ctrl+P (Cmd+P sur Mac)
2. **Destination** → "Enregistrer au format PDF"
3. **Options** → Ajuster la mise en page
4. **Imprimer** → Générer le PDF

---

## ⚙️ Paramètres avancés

### Options d'affichage

#### Transparence des mesures
- **Réglage global** : Curseur -50 à +50
- **Par type** : Niveaux prédéfinis optimisés
- **Temps réel** : Ajustement immédiat

#### Couleurs personnalisées
- **Distance** : Rouge (#FF0000) par défaut
- **Surface** : Vert (#00FF00) par défaut  
- **Périmètre** : Bleu (#0000FF) par défaut
- **Angle** : Magenta (#FF00FF) par défaut
- **Calibration** : Orange (#FFA500) par défaut

#### Grille et guides
- **Afficher la grille** : Aide au positionnement
- **Lignes détectées** : Extraction automatique
- **Guides orthogonaux** : Mode ORTHO visuel

### Système d'unités

#### Métrique (par défaut)
- **Linéaire** : mm, cm, m, km
- **Surface** : mm², cm², m², km²
- **Angle** : Degrés (°)

#### Impérial
- **Linéaire** : in, ft, yd, mi
- **Surface** : in², ft², yd², mi²
- **Angle** : Degrés (°)

### Accrochage intelligent

#### Paramètres d'accrochage
- **Activer** : Case à cocher
- **Seuil** : 5-50 pixels (10 par défaut)
- **Types** : Points, lignes, intersections

#### Priorités d'accrochage
1. Points de mesures existants
2. Extrémités de lignes détectées
3. Intersections calculées
4. Milieux de segments

### Performance et cache

#### Optimisations automatiques
- **Cache d'images** : Réutilisation des rendus
- **Zoom adaptatif** : Qualité vs vitesse
- **Nettoyage mémoire** : Libération automatique

#### Recommandations
- **Fichiers PDF** : Limiter à 50 MB
- **Nombre de mesures** : Max 1000 par projet
- **Résolution d'écran** : 1920x1080 minimum

---

## 🔧 Dépannage

### Problèmes courants

#### L'application ne se lance pas

**Symptômes** :
- Erreur Python au démarrage
- Page blanche dans le navigateur

**Solutions** :
1. Vérifier l'installation Python (3.8+)
2. Réinstaller les dépendances : `pip install -r requirements.txt`
3. Vérifier les ports : `streamlit run app.py --server.port 8502`

#### PDF ne s'affiche pas

**Symptômes** :
- Message "Erreur chargement PDF"
- Image vide ou noire

**Solutions** :
1. Vérifier le format PDF (pas de protection)
2. Réduire la taille du fichier (< 50 MB)
3. Convertir en PDF/A si nécessaire

#### Assistant IA ne répond pas

**Symptômes** :
- Message d'erreur API
- Pas de réponse aux questions

**Solutions** :
1. Vérifier la clé API Anthropic
2. Contrôler la connexion internet
3. Vérifier les crédits API restants

#### Mesures imprécises

**Symptômes** :
- Dimensions incorrectes
- Calculs erronés

**Solutions** :
1. Recalibrer l'échelle
2. Utiliser une référence connue
3. Augmenter le zoom pour plus de précision

### Messages d'erreur

#### "Clé API Anthropic requise"
- Configurer la variable ANTHROPIC_API_KEY
- Saisir la clé dans l'interface

#### "Erreur lors du chargement du PDF"
- Vérifier l'intégrité du fichier
- Essayer un autre PDF de test

#### "Aucune mesure effectuée"
- Effectuer au moins une mesure
- Vérifier la calibration

### Limites techniques

#### Formats de fichiers
- **Supportés** : PDF standard, PDF/A
- **Non supportés** : PDF protégés, images scannées de mauvaise qualité

#### Taille des projets
- **PDF** : 50 MB maximum
- **Mesures** : 1000 par projet
- **Historique IA** : 100 messages

#### Navigateurs compatibles
- **Recommandés** : Chrome 90+, Firefox 88+, Safari 14+
- **Non supportés** : Internet Explorer

---

## ❓ FAQ

### Questions générales

**Q : TAKEOFF AI est-il gratuit ?**
R : L'application est gratuite, mais l'assistant IA nécessite une clé API Anthropic payante.

**Q : Mes données sont-elles sécurisées ?**
R : Oui, les données restent locales ou en session. Aucune sauvegarde permanente sur serveur.

**Q : Puis-je utiliser TAKEOFF AI hors ligne ?**
R : Partiellement. Les mesures fonctionnent hors ligne, mais l'assistant IA nécessite internet.

### Questions techniques

**Q : Quelle précision puis-je attendre ?**
R : La précision dépend de la calibration et du zoom. Typiquement ±1-2% avec une bonne calibration.

**Q : Puis-je importer mes propres produits ?**
R : Oui, via l'import/export du catalogue au format JSON.

**Q : Les projets sont-ils compatibles entre versions ?**
R : Oui, le format .tak maintient la rétrocompatibilité.

### Questions métier

**Q : Quels codes de construction sont intégrés ?**
R : L'assistant IA connaît les codes québécois, canadiens et certains codes internationaux.

**Q : Puis-je calculer des quantités de matériaux complexes ?**
R : Oui, l'IA peut aider avec des calculs avancés selon le profil d'expert sélectionné.

**Q : Comment gérer les variations de prix ?**
R : Mettez à jour le catalogue ou appliquez des facteurs de majoration via l'IA.

---

## 📞 Support et contact

### Documentation en ligne

- **Site officiel** : [À compléter]
- **Documentation technique** : README.md du projet
- **Tutoriels vidéo** : [À compléter]
- **Base de connaissances** : [À compléter]

### Communauté

- **Forum utilisateurs** : [À compléter]
- **Discord** : [À compléter]
- **GitHub Issues** : Pour les bugs et suggestions
- **LinkedIn** : Actualités et mises à jour

### Support technique

**Email** : support@takeoff-ai.com  
**Heures** : Lun-Ven 9h-17h (EST)  
**Langue** : Français, Anglais

### Formation et consulting

Des services de formation et d'accompagnement sont disponibles :

- **Formation initiale** : 4h, tous niveaux
- **Formation avancée** : 8h, usage professionnel
- **Consulting** : Intégration sur mesure
- **Support premium** : Assistance prioritaire

---

## 📄 Annexes

### Raccourcis clavier

| Raccourci | Action |
|-----------|--------|
| `Ctrl + N` | Nouveau projet |
| `Ctrl + O` | Ouvrir projet |
| `Ctrl + S` | Sauvegarder |
| `Shift + Clic` | Mode orthogonal |
| `Échap` | Annuler mesure en cours |
| `Ctrl + Z` | Annuler dernière action |

### Formats de fichiers

#### Format .tak (Projet TAKEOFF AI)
```json
{
  "version": "1.0",
  "filename": "plan.pdf",
  "calibration": {"value": 0.05, "unit": "m"},
  "measurements": [...],
  "created": "2025-01-31T10:30:00Z"
}
```

#### Format catalogue.json
```json
{
  "Béton": {
    "Béton 25 MPa": {
      "dimensions": "Par mètre cube",
      "price": 150.0,
      "price_unit": "m³",
      "color": "#808080"
    }
  }
}
```

### Codes d'erreur

| Code | Description | Solution |
|------|-------------|----------|
| ERR_001 | PDF corrompu | Vérifier le fichier |
| ERR_002 | API IA inaccessible | Vérifier la connexion |
| ERR_003 | Calibration manquante | Effectuer la calibration |
| ERR_004 | Mémoire insuffisante | Fermer autres applications |

---

**© 2025 TAKEOFF AI - Tous droits réservés**  
**Développé par Sylvain Leduc - Constructo AI**

*Ce manuel couvre la version 1.0 de TAKEOFF AI. Pour les mises à jour, consultez la documentation en ligne.*