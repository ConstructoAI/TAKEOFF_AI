import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

class ProductCatalog:
    """Gestionnaire du catalogue de produits"""
    
    def __init__(self):
        self.catalog_file = "product_catalog.json"
        self.catalog = {}
        self.is_dirty = False
        self.load_catalog()
        self.ensure_default_catalog()
    
    def load_catalog(self):
        """Charge le catalogue depuis le fichier JSON"""
        if os.path.exists(self.catalog_file):
            try:
                with open(self.catalog_file, 'r', encoding='utf-8') as f:
                    self.catalog = json.load(f)
                self.is_dirty = False
            except Exception as e:
                print(f"Erreur lors du chargement du catalogue: {str(e)}")
                self.catalog = {}
    
    def ensure_default_catalog(self):
        """Assure qu'un catalogue par défaut existe"""
        if not self.catalog:
            self.catalog = self.get_default_catalog()
            self.save_catalog()
    
    def save_catalog(self):
        """Sauvegarde le catalogue dans le fichier JSON"""
        try:
            with open(self.catalog_file, 'w', encoding='utf-8') as f:
                json.dump(self.catalog, f, indent=2, ensure_ascii=False)
            self.is_dirty = False
            return True
        except Exception as e:
            print(f"Erreur lors de la sauvegarde du catalogue: {str(e)}")
            return False
    
    def get_categories(self) -> List[str]:
        """Retourne la liste des catégories"""
        return list(self.catalog.keys())
    
    def get_products_by_category(self, category: str) -> Dict[str, Dict]:
        """Retourne les produits d'une catégorie"""
        return self.catalog.get(category, {})
    
    def get_product(self, category: str, product_name: str) -> Optional[Dict]:
        """Récupère un produit spécifique"""
        if category in self.catalog and product_name in self.catalog[category]:
            return self.catalog[category][product_name]
        return None
    
    def add_product(self, category: str, name: str, dimensions: str, 
                   price: float, unit: str = "pi²", color: str = "#CCCCCC") -> bool:
        """Ajoute un nouveau produit"""
        if category not in self.catalog:
            self.catalog[category] = {}
        
        self.catalog[category][name] = {
            'dimensions': dimensions,
            'price': price,
            'price_unit': unit,
            'color': color
        }
        
        self.is_dirty = True
        return True
    
    def update_product(self, category: str, old_name: str, new_name: str,
                      dimensions: str, price: float, unit: str, color: str) -> bool:
        """Met à jour un produit existant"""
        if category not in self.catalog or old_name not in self.catalog[category]:
            return False
        
        # Si le nom change, on doit déplacer le produit
        if old_name != new_name:
            self.catalog[category][new_name] = self.catalog[category].pop(old_name)
        
        self.catalog[category][new_name] = {
            'dimensions': dimensions,
            'price': price,
            'price_unit': unit,
            'color': color
        }
        
        self.is_dirty = True
        return True
    
    def delete_product(self, category: str, product_name: str) -> bool:
        """Supprime un produit"""
        if category in self.catalog and product_name in self.catalog[category]:
            del self.catalog[category][product_name]
            
            # Supprimer la catégorie si elle est vide
            if not self.catalog[category]:
                del self.catalog[category]
            
            self.is_dirty = True
            return True
        return False
    
    def add_category(self, category: str) -> bool:
        """Ajoute une nouvelle catégorie"""
        if category not in self.catalog:
            self.catalog[category] = {}
            self.is_dirty = True
            return True
        return False
    
    def delete_category(self, category: str) -> bool:
        """Supprime une catégorie et tous ses produits"""
        if category in self.catalog:
            del self.catalog[category]
            self.is_dirty = True
            return True
        return False
    
    def export_catalog(self, file_path: str) -> bool:
        """Exporte le catalogue vers un fichier"""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.catalog, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur lors de l'export du catalogue: {str(e)}")
            return False
    
    def import_catalog(self, file_path: str) -> bool:
        """Importe un catalogue depuis un fichier"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                new_catalog = json.load(f)
            
            # Valider la structure
            if isinstance(new_catalog, dict):
                self.catalog = new_catalog
                self.is_dirty = True
                self.save_catalog()
                return True
            return False
        except Exception as e:
            print(f"Erreur lors de l'import du catalogue: {str(e)}")
            return False
    
    def search_products(self, query: str) -> List[tuple]:
        """Recherche des produits par nom"""
        results = []
        query_lower = query.lower()
        
        for category, products in self.catalog.items():
            for product_name, product_data in products.items():
                if query_lower in product_name.lower():
                    results.append((category, product_name, product_data))
        
        return results
    
    def export_catalog_to_string(self) -> str:
        """Exporte le catalogue vers une chaîne JSON"""
        import json
        return json.dumps(self.catalog, indent=2, ensure_ascii=False)
    
    def import_catalog_from_file(self, file_obj) -> bool:
        """Importe un catalogue depuis un objet fichier Streamlit"""
        try:
            import json
            content = file_obj.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
            new_catalog = json.loads(content)
            
            if isinstance(new_catalog, dict):
                self.catalog = new_catalog
                self.is_dirty = True
                self.save_catalog()
                return True
            return False
        except Exception as e:
            print(f"Erreur lors de l'import du catalogue: {str(e)}")
            return False
    
    def get_default_catalog(self) -> Dict:
        """Retourne un catalogue par défaut"""
        return {
            "Béton": {
                "Béton 25 MPa": {
                    "dimensions": "Par mètre cube",
                    "price": 150.0,
                    "price_unit": "m³",
                    "color": "#808080"
                },
                "Béton 30 MPa": {
                    "dimensions": "Par mètre cube",
                    "price": 165.0,
                    "price_unit": "m³",
                    "color": "#696969"
                },
                "Béton 35 MPa": {
                    "dimensions": "Par mètre cube",
                    "price": 180.0,
                    "price_unit": "m³",
                    "color": "#606060"
                }
            },
            "Acier d'armature": {
                "Barre 10M": {
                    "dimensions": "10mm dia",
                    "price": 0.85,
                    "price_unit": "m",
                    "color": "#B87333"
                },
                "Barre 15M": {
                    "dimensions": "15mm dia",
                    "price": 1.90,
                    "price_unit": "m",
                    "color": "#B87333"
                },
                "Barre 20M": {
                    "dimensions": "20mm dia",
                    "price": 3.40,
                    "price_unit": "m",
                    "color": "#B87333"
                },
                "Treillis métallique 152x152 MW9.1": {
                    "dimensions": "6x6 - 10/10",
                    "price": 2.50,
                    "price_unit": "pi²",
                    "color": "#8B7355"
                }
            },
            "Coffrages": {
                "Contreplaqué 3/4\"": {
                    "dimensions": "4'x8'x3/4\"",
                    "price": 45.0,
                    "price_unit": "feuille",
                    "color": "#DEB887"
                },
                "Madrier 2x10": {
                    "dimensions": "2\"x10\"x8'",
                    "price": 12.0,
                    "price_unit": "pièce",
                    "color": "#D2691E"
                }
            },
            "Isolation": {
                "Laine minérale R-12": {
                    "dimensions": "16\" c/c x 4'",
                    "price": 0.85,
                    "price_unit": "pi²",
                    "color": "#FFB6C1"
                },
                "Laine minérale R-20": {
                    "dimensions": "16\" c/c x 6'",
                    "price": 1.25,
                    "price_unit": "pi²",
                    "color": "#FFA0B4"
                },
                "Polystyrène extrudé 2\"": {
                    "dimensions": "2'x8'x2\"",
                    "price": 25.0,
                    "price_unit": "panneau",
                    "color": "#87CEEB"
                }
            },
            "Gypse": {
                "Gypse régulier 1/2\"": {
                    "dimensions": "4'x8'x1/2\"",
                    "price": 12.0,
                    "price_unit": "feuille",
                    "color": "#F5F5F5"
                },
                "Gypse résistant à l'eau 1/2\"": {
                    "dimensions": "4'x8'x1/2\"",
                    "price": 18.0,
                    "price_unit": "feuille",
                    "color": "#90EE90"
                },
                "Gypse coupe-feu 5/8\"": {
                    "dimensions": "4'x8'x5/8\"",
                    "price": 16.0,
                    "price_unit": "feuille",
                    "color": "#FFB6C1"
                }
            },
            "Toiture": {
                "Bardeau d'asphalte": {
                    "dimensions": "Paquet couvre 33.3 pi²",
                    "price": 30.0,
                    "price_unit": "paquet",
                    "color": "#8B4513"
                },
                "Membrane élastomère": {
                    "dimensions": "Rouleau 1m x 10m",
                    "price": 85.0,
                    "price_unit": "rouleau",
                    "color": "#2F4F4F"
                },
                "Membrane TPO 60 mil": {
                    "dimensions": "Rouleau 10' x 100'",
                    "price": 650.0,
                    "price_unit": "rouleau",
                    "color": "#F8F8FF"
                }
            }
        }