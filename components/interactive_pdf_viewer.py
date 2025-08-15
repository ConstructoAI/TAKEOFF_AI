import streamlit as st
from streamlit_drawable_canvas import st_canvas
import numpy as np
from PIL import Image, ImageDraw
import json
from typing import List, Dict, Optional, Tuple
import math

class InteractivePDFViewer:
    """Visualiseur PDF interactif avec support des mesures"""
    
    def __init__(self):
        self.stroke_width = 3
        self.point_radius = 5
        self.font_size = 14
        
    def render(self, pdf_processor, current_page: int, measurements: List[Dict],
               selected_tool: str, calibration: Dict, 
               snap_enabled: bool = True, snap_threshold: int = 10,
               detected_lines: List[Dict] = None):
        """Affiche le visualiseur PDF interactif"""
        
        # Obtenir l'image de la page
        page_image = pdf_processor.get_page_image(current_page)
        
        if not page_image:
            st.error("Impossible de charger la page PDF")
            return None
        
        # Préparer l'image de fond avec les mesures existantes
        background = self._prepare_background(
            page_image, measurements, current_page, detected_lines
        )
        
        # Configuration du canvas selon l'outil
        drawing_mode = self._get_drawing_mode(selected_tool)
        stroke_color = self._get_tool_color(selected_tool)
        
        # Canvas interactif
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=self.stroke_width,
            stroke_color=stroke_color,
            background_image=background,
            update_streamlit=True,
            height=background.height,
            width=background.width,
            drawing_mode=drawing_mode,
            point_display_radius=self.point_radius,
            key=f"canvas_{current_page}_{selected_tool}",
        )
        
        # Traiter les données du canvas
        if canvas_result.json_data is not None:
            return self._process_canvas_data(
                canvas_result.json_data,
                selected_tool,
                current_page,
                calibration,
                snap_enabled,
                snap_threshold,
                detected_lines
            )
        
        return None
    
    def _prepare_background(self, base_image: Image.Image, measurements: List[Dict],
                           current_page: int, detected_lines: Optional[List[Dict]]) -> Image.Image:
        """Prépare l'image de fond avec les mesures existantes"""
        # Créer une copie
        img = base_image.copy()
        draw = ImageDraw.Draw(img, 'RGBA')
        
        # Dessiner les lignes détectées si disponibles
        if detected_lines:
            for line in detected_lines:
                start = tuple(map(int, line['start']))
                end = tuple(map(int, line['end']))
                draw.line([start, end], fill=(200, 200, 200, 100), width=1)
        
        # Dessiner les mesures existantes
        for measurement in measurements:
            if measurement.get('page') != current_page:
                continue
            
            self._draw_measurement(draw, measurement)
        
        return img
    
    def _draw_measurement(self, draw: ImageDraw.Draw, measurement: Dict):
        """Dessine une mesure sur l'image"""
        m_type = measurement.get('type')
        points = measurement.get('points', [])
        color = measurement.get('color', '#FF0000')
        
        if not points:
            return
        
        # Convertir la couleur
        color_rgb = self._hex_to_rgb(color)
        color_rgba = color_rgb + (200,)
        
        if m_type == 'distance' and len(points) >= 2:
            # Ligne
            p1, p2 = points[0], points[1]
            draw.line([tuple(p1), tuple(p2)], fill=color_rgba, width=self.stroke_width)
            
            # Points
            for p in [p1, p2]:
                self._draw_point(draw, p, color_rgba)
            
            # Label
            if measurement.get('label') and measurement.get('value'):
                mid_point = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                label = f"{measurement['label']}: {measurement['value']:.2f} {measurement.get('unit', '')}"
                self._draw_label(draw, mid_point, label)
        
        elif m_type in ['area', 'perimeter'] and len(points) >= 3:
            # Polygone
            polygon_points = [tuple(p) for p in points]
            
            if m_type == 'area':
                # Remplir avec transparence
                draw.polygon(polygon_points, fill=color_rgba[:3] + (50,), 
                           outline=color_rgba, width=self.stroke_width)
            else:
                # Juste le contour
                for i in range(len(polygon_points)):
                    next_i = (i + 1) % len(polygon_points)
                    draw.line([polygon_points[i], polygon_points[next_i]], 
                            fill=color_rgba, width=self.stroke_width)
            
            # Points
            for p in points:
                self._draw_point(draw, p, color_rgba)
            
            # Label au centre
            if measurement.get('label') and measurement.get('value'):
                center = self._get_polygon_center(points)
                label = f"{measurement['label']}: {measurement['value']:.2f} {measurement.get('unit', '')}"
                self._draw_label(draw, center, label)
        
        elif m_type == 'angle' and len(points) >= 3:
            # Lignes de l'angle
            p1, p2, p3 = points[:3]
            draw.line([tuple(p1), tuple(p2)], fill=color_rgba, width=self.stroke_width)
            draw.line([tuple(p2), tuple(p3)], fill=color_rgba, width=self.stroke_width)
            
            # Arc d'angle
            self._draw_angle_arc(draw, p1, p2, p3, color_rgba)
            
            # Points
            for p in [p1, p2, p3]:
                self._draw_point(draw, p, color_rgba)
            
            # Label
            if measurement.get('value'):
                label = f"{measurement.get('label', 'Angle')}: {measurement['value']:.1f}°"
                self._draw_label(draw, p2, label)
    
    def _draw_point(self, draw: ImageDraw.Draw, point: Tuple[float, float], color):
        """Dessine un point"""
        x, y = point
        r = self.point_radius
        draw.ellipse([x-r, y-r, x+r, y+r], fill=color, outline='white')
    
    def _draw_label(self, draw: ImageDraw.Draw, position: Tuple[float, float], text: str):
        """Dessine un label avec fond"""
        x, y = position
        
        # Obtenir la taille du texte
        bbox = draw.textbbox((x, y), text)
        padding = 4
        
        # Dessiner le fond
        draw.rectangle(
            [bbox[0]-padding, bbox[1]-padding, bbox[2]+padding, bbox[3]+padding],
            fill=(255, 255, 255, 200)
        )
        
        # Dessiner le texte
        draw.text((x, y), text, fill='black')
    
    def _draw_angle_arc(self, draw: ImageDraw.Draw, p1: Tuple, p2: Tuple, p3: Tuple, color):
        """Dessine un arc pour visualiser l'angle"""
        # Calculer l'angle et les vecteurs
        v1 = (p1[0] - p2[0], p1[1] - p2[1])
        v2 = (p3[0] - p2[0], p3[1] - p2[1])
        
        # Angles des vecteurs
        angle1 = math.degrees(math.atan2(v1[1], v1[0]))
        angle2 = math.degrees(math.atan2(v2[1], v2[0]))
        
        # Rayon de l'arc
        radius = 30
        
        # Boîte englobante pour l'arc
        bbox = [p2[0] - radius, p2[1] - radius, p2[0] + radius, p2[1] + radius]
        
        # Dessiner l'arc
        start_angle = min(angle1, angle2)
        end_angle = max(angle1, angle2)
        
        # S'assurer que l'arc prend le chemin le plus court
        if end_angle - start_angle > 180:
            start_angle, end_angle = end_angle, start_angle + 360
        
        draw.arc(bbox, start_angle, end_angle, fill=color, width=2)
    
    def _get_polygon_center(self, points: List[Tuple]) -> Tuple[float, float]:
        """Calcule le centre d'un polygone"""
        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
        return (x, y)
    
    def _hex_to_rgb(self, hex_color: str) -> Tuple[int, int, int]:
        """Convertit une couleur hexadécimale en RGB"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _get_drawing_mode(self, tool: str) -> str:
        """Retourne le mode de dessin pour l'outil"""
        modes = {
            'distance': 'line',
            'area': 'polygon',
            'perimeter': 'polygon',
            'angle': 'line',
            'calibration': 'line'
        }
        return modes.get(tool, 'point')
    
    def _get_tool_color(self, tool: str) -> str:
        """Retourne la couleur par défaut pour l'outil"""
        colors = {
            'distance': '#FF0000',
            'area': '#00FF00',
            'perimeter': '#0000FF',
            'angle': '#FF00FF',
            'calibration': '#FFA500'
        }
        return colors.get(tool, '#000000')
    
    def _process_canvas_data(self, json_data: Dict, tool: str, page: int,
                           calibration: Dict, snap_enabled: bool,
                           snap_threshold: int, detected_lines: Optional[List[Dict]]) -> Optional[Dict]:
        """Traite les données du canvas pour créer une mesure"""
        objects = json_data.get('objects', [])
        
        if not objects:
            return None
        
        # Obtenir le dernier objet dessiné
        last_object = objects[-1]
        
        # Extraire les points selon le type d'objet
        points = self._extract_points(last_object)
        
        if not points:
            return None
        
        # Appliquer l'accrochage si activé
        if snap_enabled and detected_lines:
            points = self._apply_snapping(points, detected_lines, snap_threshold)
        
        # Créer la mesure selon l'outil
        measurement = self._create_measurement(tool, points, page, calibration)
        
        return measurement
    
    def _extract_points(self, canvas_object: Dict) -> List[Tuple[float, float]]:
        """Extrait les points d'un objet canvas"""
        obj_type = canvas_object.get('type')
        
        if obj_type == 'line':
            # Ligne simple
            x1 = canvas_object.get('x1', 0)
            y1 = canvas_object.get('y1', 0)
            x2 = canvas_object.get('x2', 0)
            y2 = canvas_object.get('y2', 0)
            return [(x1, y1), (x2, y2)]
        
        elif obj_type == 'path':
            # Chemin (polygone)
            path = canvas_object.get('path', [])
            points = []
            
            for cmd in path:
                if len(cmd) >= 3 and cmd[0] in ['M', 'L']:
                    points.append((cmd[1], cmd[2]))
            
            return points
        
        elif obj_type == 'rect':
            # Rectangle
            left = canvas_object.get('left', 0)
            top = canvas_object.get('top', 0)
            width = canvas_object.get('width', 0)
            height = canvas_object.get('height', 0)
            
            return [
                (left, top),
                (left + width, top),
                (left + width, top + height),
                (left, top + height)
            ]
        
        return []
    
    def _apply_snapping(self, points: List[Tuple], lines: List[Dict], 
                       threshold: int) -> List[Tuple]:
        """Applique l'accrochage aux lignes détectées"""
        snapped_points = []
        
        for point in points:
            # Chercher le point d'accrochage le plus proche
            min_dist = threshold
            snap_point = point
            
            for line in lines:
                # Vérifier les extrémités
                for end_point in [line['start'], line['end']]:
                    dist = self._distance(point, end_point)
                    if dist < min_dist:
                        min_dist = dist
                        snap_point = tuple(end_point)
                
                # Vérifier le point le plus proche sur la ligne
                closest = self._closest_point_on_line(
                    point, line['start'], line['end']
                )
                dist = self._distance(point, closest)
                if dist < min_dist:
                    min_dist = dist
                    snap_point = closest
            
            snapped_points.append(snap_point)
        
        return snapped_points
    
    def _distance(self, p1: Tuple, p2: Tuple) -> float:
        """Calcule la distance entre deux points"""
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
    
    def _closest_point_on_line(self, point: Tuple, line_start: Tuple, 
                              line_end: Tuple) -> Tuple[float, float]:
        """Trouve le point le plus proche sur une ligne"""
        x0, y0 = point
        x1, y1 = line_start
        x2, y2 = line_end
        
        dx = x2 - x1
        dy = y2 - y1
        
        if dx == 0 and dy == 0:
            return line_start
        
        t = ((x0 - x1) * dx + (y0 - y1) * dy) / (dx * dx + dy * dy)
        t = max(0, min(1, t))
        
        return (x1 + t * dx, y1 + t * dy)
    
    def _create_measurement(self, tool: str, points: List[Tuple], 
                          page: int, calibration: Dict) -> Dict:
        """Crée une mesure à partir des points"""
        measurement = {
            'type': tool,
            'points': points,
            'page': page,
            'timestamp': st.session_state.get('measurement_counter', 0)
        }
        
        # Incrémenter le compteur
        if 'measurement_counter' not in st.session_state:
            st.session_state.measurement_counter = 0
        st.session_state.measurement_counter += 1
        
        # Calculer la valeur selon le type
        cal_factor = calibration.get('value', 1.0)
        
        if tool == 'distance' and len(points) >= 2:
            pixel_distance = self._distance(points[0], points[1])
            measurement['value'] = pixel_distance * cal_factor
            measurement['unit'] = calibration.get('unit', 'cm')
            measurement['label'] = f"Distance_{st.session_state.measurement_counter}"
        
        elif tool == 'area' and len(points) >= 3:
            pixel_area = self._calculate_polygon_area(points)
            measurement['value'] = pixel_area * cal_factor * cal_factor
            measurement['unit'] = f"{calibration.get('unit', 'cm')}²"
            measurement['label'] = f"Surface_{st.session_state.measurement_counter}"
        
        elif tool == 'perimeter' and len(points) >= 3:
            pixel_perimeter = self._calculate_perimeter(points, closed=True)
            measurement['value'] = pixel_perimeter * cal_factor
            measurement['unit'] = calibration.get('unit', 'cm')
            measurement['label'] = f"Périmètre_{st.session_state.measurement_counter}"
        
        elif tool == 'angle' and len(points) >= 3:
            angle = self._calculate_angle(points[0], points[1], points[2])
            measurement['value'] = angle
            measurement['unit'] = '°'
            measurement['label'] = f"Angle_{st.session_state.measurement_counter}"
        
        elif tool == 'calibration' and len(points) >= 2:
            pixel_distance = self._distance(points[0], points[1])
            measurement['value'] = pixel_distance
            measurement['unit'] = 'px'
            measurement['label'] = "Calibration"
        
        # Couleur par défaut
        measurement['color'] = self._get_tool_color(tool)
        
        return measurement
    
    def _calculate_polygon_area(self, points: List[Tuple]) -> float:
        """Calcule l'aire d'un polygone (formule du lacet)"""
        n = len(points)
        area = 0.0
        
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        
        return abs(area) / 2.0
    
    def _calculate_perimeter(self, points: List[Tuple], closed: bool = True) -> float:
        """Calcule le périmètre d'une forme"""
        perimeter = 0.0
        
        for i in range(len(points) - 1):
            perimeter += self._distance(points[i], points[i + 1])
        
        if closed and len(points) > 2:
            perimeter += self._distance(points[-1], points[0])
        
        return perimeter
    
    def _calculate_angle(self, p1: Tuple, p2: Tuple, p3: Tuple) -> float:
        """Calcule l'angle entre trois points (p2 est le sommet)"""
        v1 = (p1[0] - p2[0], p1[1] - p2[1])
        v2 = (p3[0] - p2[0], p3[1] - p2[1])
        
        dot_product = v1[0] * v2[0] + v1[1] * v2[1]
        
        norm1 = math.sqrt(v1[0]**2 + v1[1]**2)
        norm2 = math.sqrt(v2[0]**2 + v2[1]**2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        cos_angle = dot_product / (norm1 * norm2)
        cos_angle = max(-1, min(1, cos_angle))
        
        return math.degrees(math.acos(cos_angle))