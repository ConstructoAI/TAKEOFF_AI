import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import streamlit as st

class ProjectManager:
    """Gestionnaire pour sauvegarder et charger les projets"""
    
    def __init__(self):
        self.recent_file = "recent.json"
        self.max_recent = 10
    
    def save_project(self, filepath: str, project_data: Dict) -> bool:
        """Sauvegarde un projet au format .tak"""
        try:
            # Ajouter les métadonnées
            project_data['metadata'] = {
                'version': '2.0',
                'created': datetime.now().isoformat(),
                'app': 'TAKEOFF AI Streamlit'
            }
            
            # Sauvegarder en JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=2, ensure_ascii=False)
            
            # Ajouter aux projets récents
            self.add_recent_project(filepath)
            
            return True
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde: {str(e)}")
            return False
    
    def load_project(self, filepath: str) -> Optional[Dict]:
        """Charge un projet depuis un fichier .tak"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                project_data = json.load(f)
            
            # Vérifier la version
            metadata = project_data.get('metadata', {})
            version = metadata.get('version', '1.0')
            
            # Ajouter aux projets récents
            self.add_recent_project(filepath)
            
            return project_data
        except Exception as e:
            st.error(f"Erreur lors du chargement: {str(e)}")
            return None
    
    def get_recent_projects(self) -> List[str]:
        """Retourne la liste des projets récents"""
        if os.path.exists(self.recent_file):
            try:
                with open(self.recent_file, 'r', encoding='utf-8') as f:
                    recent = json.load(f)
                    # Filtrer les fichiers qui existent encore
                    return [p for p in recent if os.path.exists(p)]
            except:
                return []
        return []
    
    def add_recent_project(self, filepath: str):
        """Ajoute un projet à la liste des récents"""
        recent = self.get_recent_projects()
        
        # Retirer si déjà présent
        if filepath in recent:
            recent.remove(filepath)
        
        # Ajouter en début
        recent.insert(0, filepath)
        
        # Limiter le nombre
        recent = recent[:self.max_recent]
        
        # Sauvegarder
        try:
            with open(self.recent_file, 'w', encoding='utf-8') as f:
                json.dump(recent, f, indent=2)
        except:
            pass
    
    def clear_recent_projects(self):
        """Efface la liste des projets récents"""
        try:
            if os.path.exists(self.recent_file):
                os.remove(self.recent_file)
        except:
            pass
    
    def export_to_csv(self, measurements: List[Dict], filepath: str) -> bool:
        """Exporte les mesures au format CSV"""
        try:
            import csv
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if measurements:
                    # En-têtes
                    fieldnames = ['Type', 'Nom', 'Valeur', 'Unité', 'Page', 
                                 'Produit', 'Catégorie', 'Prix unitaire', 'Quantité']
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    # Données
                    for m in measurements:
                        product = m.get('product', {})
                        row = {
                            'Type': m.get('type', ''),
                            'Nom': m.get('label', ''),
                            'Valeur': f"{m.get('value', 0):.2f}",
                            'Unité': m.get('unit', ''),
                            'Page': m.get('page', 0) + 1,
                            'Produit': product.get('name', ''),
                            'Catégorie': product.get('category', ''),
                            'Prix unitaire': f"{product.get('price', 0):.2f}",
                            'Quantité': f"{m.get('value', 0):.2f}"
                        }
                        writer.writerow(row)
            
            return True
        except Exception as e:
            st.error(f"Erreur lors de l'export CSV: {str(e)}")
            return False
    
    def export_to_txt(self, project_data: Dict, measurements: List[Dict], 
                     catalog, filepath: str) -> bool:
        """Exporte le projet au format texte"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                # En-tête
                f.write("=" * 60 + "\n")
                f.write("RAPPORT D'ESTIMATION - TAKEOFF AI\n")
                f.write("=" * 60 + "\n\n")
                
                # Informations du projet
                f.write("INFORMATIONS DU PROJET\n")
                f.write("-" * 30 + "\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                f.write(f"Fichier PDF: {project_data.get('filename', 'N/D')}\n")
                cal = project_data.get('calibration', {})
                f.write(f"Calibration: {cal.get('value', 1.0):.2f} {cal.get('unit', 'cm')}\n")
                f.write(f"Nombre de mesures: {len(measurements)}\n\n")
                
                # Mesures par type
                f.write("MESURES DÉTAILLÉES\n")
                f.write("-" * 30 + "\n")
                
                # Grouper par type
                by_type = {}
                for m in measurements:
                    m_type = m.get('type', 'unknown')
                    if m_type not in by_type:
                        by_type[m_type] = []
                    by_type[m_type].append(m)
                
                for m_type, items in by_type.items():
                    f.write(f"\n{m_type.upper()} ({len(items)} mesures)\n")
                    for m in items:
                        label = m.get('label', 'Sans nom')
                        value = m.get('value', 0)
                        unit = m.get('unit', '')
                        product = m.get('product', {}).get('name', 'Aucun produit')
                        f.write(f"  - {label}: {value:.2f} {unit} [{product}]\n")
                
                # Totaux par produit
                f.write("\n\nTOTAUX PAR PRODUIT\n")
                f.write("-" * 30 + "\n")
                
                totals = {}
                for m in measurements:
                    product = m.get('product', {})
                    product_name = product.get('name')
                    if product_name:
                        if product_name not in totals:
                            totals[product_name] = {
                                'quantity': 0,
                                'unit': m.get('unit', ''),
                                'price': product.get('price', 0)
                            }
                        totals[product_name]['quantity'] += m.get('value', 0)
                
                grand_total = 0
                for product_name, data in totals.items():
                    qty = data['quantity']
                    price = data['price']
                    total = qty * price
                    grand_total += total
                    f.write(f"{product_name}: {qty:.2f} {data['unit']} x {price:.2f}$ = {total:.2f}$\n")
                
                f.write(f"\nTOTAL GÉNÉRAL: {grand_total:.2f}$\n")
            
            return True
        except Exception as e:
            st.error(f"Erreur lors de l'export TXT: {str(e)}")
            return False
    
    def export_to_json(self, data: Dict, filepath: str) -> bool:
        """Exporte les données au format JSON"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"Erreur lors de l'export JSON: {str(e)}")
            return False