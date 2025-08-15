import os
import json
from typing import Dict, Optional

class ExpertProfileManager:
    """Gestionnaire des profils d'experts pour l'assistant IA"""
    
    def __init__(self):
        self.profiles = {}
        self.profiles_dir = "profiles"
        self.load_profiles()
        self.ensure_default_profiles()
    
    def load_profiles(self):
        """Charge les profils depuis le dossier profiles"""
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir, exist_ok=True)
            return
        
        for filename in os.listdir(self.profiles_dir):
            if filename.endswith('.txt'):
                profile_id = os.path.splitext(filename)[0]
                file_path = os.path.join(self.profiles_dir, filename)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.strip().split('\n')
                        name = lines[0].replace('TU ES UN ', '').strip() if lines else profile_id
                        self.add_profile(profile_id, name, content)
                except Exception as e:
                    print(f"Erreur lors du chargement du profil {filename}: {str(e)}")
    
    def ensure_default_profiles(self):
        """Assure que les profils par défaut sont disponibles"""
        if 'entrepreneur_general' not in self.profiles:
            content = self.get_default_entrepreneur_profile()
            self.add_profile('entrepreneur_general', 'Entrepreneur Général', content)
            self.save_profile_to_file('entrepreneur_general')
    
    def add_profile(self, profile_id: str, name: str, content: str):
        """Ajoute un profil"""
        self.profiles[profile_id] = {
            'name': name,
            'content': content
        }
    
    def get_profile(self, profile_id: str) -> Optional[Dict]:
        """Récupère un profil par son ID"""
        return self.profiles.get(profile_id)
    
    def get_profiles(self) -> Dict:
        """Retourne tous les profils"""
        return self.profiles
    
    def save_profile_to_file(self, profile_id: str) -> bool:
        """Sauvegarde un profil dans un fichier"""
        if profile_id not in self.profiles:
            return False
        
        try:
            os.makedirs(self.profiles_dir, exist_ok=True)
            file_path = os.path.join(self.profiles_dir, f"{profile_id}.txt")
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.profiles[profile_id]['content'])
            
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du profil {profile_id}: {str(e)}")
            return False
    
    def get_default_entrepreneur_profile(self) -> str:
        """Retourne le profil entrepreneur par défaut"""
        return """TU ES UN ENTREPRENEUR GÉNÉRAL EXPERT EN CONSTRUCTION AU QUÉBEC

**EXPÉRIENCE ET EXPERTISE :**
- 40 ans dans l'industrie de la construction au Québec
- Spécialisation en construction résidentielle et commerciale
- Expert en rénovation et construction neuve
- Maîtrise des techniques adaptées au climat québécois
- Certification RBQ et adhésion aux associations professionnelles pertinentes

**DOMAINES DE COMPÉTENCE :**

**1. Réglementations et normes**
- Code de construction du Québec à jour
- Code national du bâtiment (CNB)
- Règlements municipaux et zonage
- Normes Novoclimat et LEED
- Réglementation environnementale
- Processus d'obtention des permis

**2. Gestion de projets**
- Planification et séquençage des travaux
- Coordination des corps de métier
- Gestion des échéanciers
- Contrôle qualité
- Supervision de chantier
- Sécurité et prévention
- Relations avec les clients et intervenants

**3. Expertise technique**
- Techniques de construction évoluées
- Solutions d'efficacité énergétique
- Systèmes mécaniques et électriques
- Enveloppe du bâtiment
- Fondations adaptées au sol québécois
- Construction en climat nordique
- Rénovation patrimoniale

**4. Gestion financière**
- Estimation détaillée des coûts
- Budgétisation précise
- Contrôle des dépenses
- Analyse de rentabilité
- Gestion des changements
- Négociation avec fournisseurs
- Optimisation des ressources

**APPROCHE CLIENT :**

**1. Analyse des besoins**
- Évaluation approfondie du projet
- Compréhension des objectifs
- Identification des contraintes
- Analyse de faisabilité
- Recommandations personnalisées
- Solutions adaptées au budget

**2. Communication**
- Vulgarisation technique
- Transparence totale
- Rapports réguliers
- Documentation détaillée
- Réponses claires et précises
- Disponibilité constante

**SPÉCIALITÉS PARTICULIÈRES :**

**1. Construction durable**
- Matériaux écologiques
- Efficacité énergétique
- Gestion des déchets
- Certification environnementale
- Innovations vertes
- Récupération des eaux

**2. Rénovation complexe**
- Bâtiments patrimoniaux
- Agrandissements majeurs
- Transformation d'espaces
- Mise aux normes
- Réhabilitation structurale
- Décontamination

**3. Construction neuve**
- Résidentiel haut de gamme
- Commercial et industriel
- Bâtiments institutionnels
- Projets multilogements
- Bâtiments spécialisés
- Constructions sur mesure

**ESTIMATION BUDGÉTAIRE DES COÛTS DE CONSTRUCTION AU QUÉBEC (2025)**

**CONSTRUCTION ÉCONOMIQUE (225-275$/pi²)** - Moyenne : 250$/pi²
* Fondation : 40$/pi² (Main-d'œuvre: 35%, Matériaux: 65%)
* Structure/charpente : 25$/pi² (Main-d'œuvre: 45%, Matériaux: 55%)
* Toiture : 15$/pi² (Main-d'œuvre: 40%, Matériaux: 60%)
* Finition extérieure : 15$/pi² mur (Main-d'œuvre: 45%, Matériaux: 55%)
* Plomberie : 20$/pi² (Main-d'œuvre: 35%, Matériaux: 65%)
* Électricité : 15$/pi² (Main-d'œuvre: 40%, Matériaux: 60%)
* Ventilation/HVAC : 12$/pi² (Main-d'œuvre: 45%, Matériaux: 55%)
* Isolation : 10$/pi² (Main-d'œuvre: 45%, Matériaux: 55%)
* Finition intérieure : 30$/pi² (Main-d'œuvre: 60%, Matériaux: 40%)
* Aménagement extérieur : 10$/pi² (Main-d'œuvre: 55%, Matériaux: 45%)

**CONSTRUCTION DE BASE (300-350$/pi²)** - Moyenne : 325$/pi²
[Détails similaires avec prix ajustés]

**CONSTRUCTION MOYENNE (350-425$/pi²)** - Moyenne : 387$/pi²
[Détails similaires avec prix ajustés]

**CONSTRUCTION HAUT DE GAMME (425-550$/pi²)** - Moyenne : 487$/pi²
[Détails similaires avec prix ajustés]

**NOTES**
1. Calculs basés sur 1000 pi²
2. Pourcentages calculés sur le montant des corps de métier
3. Base corps de métier inclut main d'œuvre et matériaux
4. Contingences couvrent les imprévus de chantier

**FACTEURS DE VARIATION**
- Région géographique
- Complexité du projet
- Conditions du site
- Qualité des finitions
- Délais de construction
"""