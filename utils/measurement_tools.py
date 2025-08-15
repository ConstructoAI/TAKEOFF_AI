import math
import numpy as np
from typing import List, Dict, Tuple, Optional

class MeasurementTools:
    """Outils pour les calculs de mesures"""
    
    def __init__(self):
        self.conversion_factors = {
            'metric': {
                'mm': 0.001,
                'cm': 0.01,
                'm': 1.0,
                'km': 1000.0
            },
            'imperial': {
                'in': 0.0254,
                'ft': 0.3048,
                'yd': 0.9144,
                'mi': 1609.344
            }
        }
    
    def calculate_distance(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calcule la distance entre deux points"""
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
    
    def calculate_area_shoelace(self, points: List[Tuple[float, float]]) -> float:
        """Calcule l'aire d'un polygone avec la formule du lacet"""
        if len(points) < 3:
            return 0.0
        
        # S'assurer que le polygone est fermé
        if points[0] != points[-1]:
            points = points + [points[0]]
        
        # Formule du lacet
        area = 0.0
        for i in range(len(points) - 1):
            area += points[i][0] * points[i+1][1]
            area -= points[i+1][0] * points[i][1]
        
        return abs(area) / 2.0
    
    def calculate_perimeter(self, points: List[Tuple[float, float]], closed: bool = True) -> float:
        """Calcule le périmètre d'une forme"""
        if len(points) < 2:
            return 0.0
        
        perimeter = 0.0
        for i in range(len(points) - 1):
            perimeter += self.calculate_distance(points[i], points[i+1])
        
        # Fermer la forme si nécessaire
        if closed and len(points) > 2:
            perimeter += self.calculate_distance(points[-1], points[0])
        
        return perimeter
    
    def calculate_angle(self, p1: Tuple[float, float], p2: Tuple[float, float], 
                       p3: Tuple[float, float]) -> float:
        """Calcule l'angle entre trois points (p2 est le sommet)"""
        # Vecteurs
        v1 = (p1[0] - p2[0], p1[1] - p2[1])
        v2 = (p3[0] - p2[0], p3[1] - p2[1])
        
        # Produit scalaire
        dot_product = v1[0] * v2[0] + v1[1] * v2[1]
        
        # Normes
        norm1 = math.sqrt(v1[0]**2 + v1[1]**2)
        norm2 = math.sqrt(v2[0]**2 + v2[1]**2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        # Angle en radians puis en degrés
        cos_angle = dot_product / (norm1 * norm2)
        cos_angle = max(-1, min(1, cos_angle))  # Clamp pour éviter les erreurs
        angle_rad = math.acos(cos_angle)
        angle_deg = math.degrees(angle_rad)
        
        return angle_deg
    
    def convert_units(self, value: float, from_unit: str, to_unit: str, 
                     unit_system: str = 'metric') -> float:
        """Convertit entre différentes unités"""
        if from_unit == to_unit:
            return value
        
        # Convertir vers mètres d'abord
        factors = self.conversion_factors[unit_system]
        if from_unit in factors:
            value_in_meters = value * factors[from_unit]
        else:
            return value
        
        # Convertir vers l'unité cible
        if to_unit in factors:
            return value_in_meters / factors[to_unit]
        
        return value
    
    def apply_calibration(self, pixel_value: float, calibration: Dict) -> float:
        """Applique la calibration pour convertir des pixels en unités réelles"""
        cal_value = calibration.get('value', 1.0)
        return pixel_value * cal_value
    
    def format_measurement(self, value: float, unit: str, precision: int = 2) -> str:
        """Formate une mesure avec son unité"""
        if unit in ['m²', 'ft²', 'pi²']:
            # Unités de surface
            return f"{value:.{precision}f} {unit}"
        elif unit in ['°', 'deg']:
            # Angles
            return f"{value:.1f}°"
        else:
            # Unités linéaires
            return f"{value:.{precision}f} {unit}"
    
    def calculate_totals(self, measurements: List[Dict], catalog: Optional[object] = None) -> List[Dict]:
        """Calcule les totaux par produit"""
        totals = {}
        
        for measurement in measurements:
            product = measurement.get('product', {})
            product_name = product.get('name')
            
            if not product_name:
                continue
            
            # Obtenir les détails du produit
            category = product.get('category')
            product_data = None
            if catalog and category:
                product_data = catalog.get_product(category, product_name)
            
            if product_name not in totals:
                totals[product_name] = {
                    'name': product_name,
                    'category': category,
                    'quantity': 0,
                    'unit': measurement.get('unit', ''),
                    'measurements': [],
                    'price_unit': product_data.get('price_unit', '') if product_data else '',
                    'unit_price': product_data.get('price', 0) if product_data else 0
                }
            
            # Ajouter la mesure
            value = measurement.get('value', 0)
            totals[product_name]['quantity'] += value
            totals[product_name]['measurements'].append({
                'label': measurement.get('label', 'Sans nom'),
                'value': value,
                'type': measurement.get('type', '')
            })
        
        # Calculer les prix totaux
        result = []
        for product_name, data in totals.items():
            total_price = data['quantity'] * data['unit_price']
            
            result.append({
                'Produit': product_name,
                'Catégorie': data['category'] or 'Non catégorisé',
                'Quantité': f"{data['quantity']:.2f}",
                'Unité': data['unit'],
                'Prix unitaire': f"{data['unit_price']:.2f}$" if data['unit_price'] > 0 else 'N/D',
                'Prix total': f"{total_price:.2f}$" if total_price > 0 else 'N/D',
                'Nb mesures': len(data['measurements'])
            })
        
        return result
    
    def find_snap_point(self, cursor: Tuple[float, float], points: List[Tuple[float, float]], 
                       lines: List[Dict], threshold: float = 10) -> Optional[Tuple[float, float]]:
        """Trouve le point d'accrochage le plus proche"""
        min_distance = threshold
        snap_point = None
        
        # Vérifier les points existants
        for point in points:
            dist = self.calculate_distance(cursor, point)
            if dist < min_distance:
                min_distance = dist
                snap_point = point
        
        # Vérifier les lignes
        for line in lines:
            start = line['start']
            end = line['end']
            
            # Extrémités
            for point in [start, end]:
                dist = self.calculate_distance(cursor, point)
                if dist < min_distance:
                    min_distance = dist
                    snap_point = point
            
            # Milieu
            mid = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
            dist = self.calculate_distance(cursor, mid)
            if dist < min_distance:
                min_distance = dist
                snap_point = mid
            
            # Point le plus proche sur la ligne
            closest = self.closest_point_on_line(cursor, start, end)
            if closest:
                dist = self.calculate_distance(cursor, closest)
                if dist < min_distance:
                    min_distance = dist
                    snap_point = closest
        
        return snap_point
    
    def closest_point_on_line(self, point: Tuple[float, float], 
                             line_start: Tuple[float, float], 
                             line_end: Tuple[float, float]) -> Tuple[float, float]:
        """Trouve le point le plus proche sur une ligne"""
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        # Vecteur de la ligne
        dx = x2 - x1
        dy = y2 - y1
        
        # Cas dégénéré - la ligne est un point
        if dx == 0 and dy == 0:
            return line_start
        
        # Paramètre t pour le point le plus proche
        t = ((x0 - x1) * dx + (y0 - y1) * dy) / (dx * dx + dy * dy)
        
        # Limiter t entre 0 et 1
        t = max(0, min(1, t))
        
        # Point le plus proche
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy
        
        return (closest_x, closest_y)
    
    def is_orthogonal(self, p1: Tuple[float, float], p2: Tuple[float, float], 
                     tolerance: float = 5.0) -> Tuple[bool, Optional[Tuple[float, float]]]:
        """Vérifie si une ligne est presque orthogonale et retourne le point ajusté"""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        
        if abs(dx) == 0 or abs(dy) == 0:
            return True, p2
        
        angle = math.degrees(math.atan(abs(dy) / abs(dx)))
        
        # Proche de 0° (horizontal)
        if angle < tolerance:
            return True, (p2[0], p1[1])
        
        # Proche de 90° (vertical)
        if 90 - angle < tolerance:
            return True, (p1[0], p2[1])
        
        # Proche de 45°
        if abs(angle - 45) < tolerance:
            avg = (abs(dx) + abs(dy)) / 2
            new_dx = avg if dx > 0 else -avg
            new_dy = avg if dy > 0 else -avg
            return True, (p1[0] + new_dx, p1[1] + new_dy)
        
        return False, None