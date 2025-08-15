import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import math
from typing import List, Dict, Optional, Tuple
import time

def OptimizedPDFViewerFinal(pdf_processor, current_page: int, measurements: List[Dict],
                            selected_tool: str, calibration: Dict, detected_lines: Optional[List[Dict]] = None):
    """Visualiseur PDF optimisé - version finale sans double-clic"""
    
    # Initialiser l'état persistant avec une structure optimisée
    if 'pdf_viewer_state' not in st.session_state:
        st.session_state.pdf_viewer_state = {
            'pending_points': [],
            'last_tool': selected_tool,
            'last_page': current_page,
            'zoom_level': 1.5,
            'calibration_zoom': 1.0,
            'base_image': None,
            'base_image_key': None,
            'click_counter': 0,
            'force_refresh': False,
            'last_click_time': 0
        }
    
    state = st.session_state.pdf_viewer_state
    
    # Détection de changement d'outil ou de page
    tool_changed = state['last_tool'] != selected_tool
    page_changed = state['last_page'] != current_page
    
    if tool_changed or page_changed:
        state['pending_points'] = []
        state['last_tool'] = selected_tool
        state['last_page'] = current_page
        state['base_image'] = None
        state['force_refresh'] = True
    
    # Configuration des outils
    tool_configs = {
        'distance': {'points': 2, 'auto_complete': True, 'color': '#FF0000', 'name': '📏 Distance'},
        'angle': {'points': 3, 'auto_complete': True, 'color': '#FF00FF', 'name': '📐 Angle'},
        'area': {'points': 3, 'auto_complete': False, 'color': '#00FF00', 'name': '⬜ Surface'},
        'perimeter': {'points': 3, 'auto_complete': False, 'color': '#0000FF', 'name': '🔲 Périmètre'},
        'calibration': {'points': 2, 'auto_complete': True, 'color': '#FFA500', 'name': '🎯 Calibration'}
    }
    
    config = tool_configs.get(selected_tool, {})
    
    # Interface utilisateur compacte
    header_col1, header_col2, header_col3 = st.columns([6, 1, 1])
    
    with header_col1:
        st.markdown(f"**{config.get('name')}** - {len(state['pending_points'])} point(s) - Page {current_page + 1}")
    
    with header_col2:
        can_validate = (
            (selected_tool in ['area', 'perimeter'] and len(state['pending_points']) >= 3) or
            (config.get('auto_complete') and len(state['pending_points']) >= config.get('points', 0))
        )
        
        if can_validate and st.button("✅", key="validate_measure"):
            process_measurement_final(
                selected_tool, state['pending_points'], measurements,
                current_page, calibration, state['zoom_level']
            )
            state['pending_points'] = []
            state['base_image'] = None
            state['force_refresh'] = True
            st.rerun()
    
    with header_col3:
        if st.button("🔄", key="clear_points"):
            state['pending_points'] = []
            state['force_refresh'] = True
            st.rerun()
    
    # Contrôle du zoom
    zoom = st.slider(
        "🔍 Zoom", 0.5, 3.0, state['zoom_level'], 0.1,
        key="zoom_control",
        help="Alt+/- pour zoomer"
    )
    
    if zoom != state['zoom_level']:
        # Ajuster les points existants
        if state['pending_points']:
            zoom_ratio = zoom / state['zoom_level']
            state['pending_points'] = [(p[0] * zoom_ratio, p[1] * zoom_ratio) for p in state['pending_points']]
        
        state['zoom_level'] = zoom
        state['base_image'] = None
        state['force_refresh'] = True
    
    # Générer la clé unique pour l'image de base
    base_key = f"{current_page}_{zoom}_{len(measurements)}"
    
    # Créer ou récupérer l'image de base
    if state['base_image'] is None or state['base_image_key'] != base_key:
        page_image = pdf_processor.get_page_image(current_page, zoom=zoom)
        if page_image:
            state['base_image'] = create_base_image_final(
                page_image, measurements, current_page, detected_lines
            )
            state['base_image_key'] = base_key
    
    if state['base_image'] is None:
        st.error("Impossible de charger la page PDF")
        return
    
    # Créer l'image d'affichage
    display_image = state['base_image'].copy()
    if state['pending_points']:
        draw = ImageDraw.Draw(display_image, 'RGBA')
        draw_pending_points_final(draw, state['pending_points'], config.get('color', '#000000'), selected_tool)
    
    # Container principal pour l'image
    img_container = st.container()
    
    with img_container:
        # Clé unique pour forcer le rechargement si nécessaire
        img_key = f"pdf_{current_page}_{selected_tool}_{state['click_counter']}"
        
        if state['force_refresh']:
            img_key += f"_refresh_{time.time()}"
            state['force_refresh'] = False
        
        # Afficher l'image avec gestion des clics
        value = streamlit_image_coordinates(
            display_image,
            key=img_key
        )
        
        # Traiter le clic immédiatement
        if value is not None:
            # Vérifier le délai pour éviter les doubles clics
            current_time = time.time()
            if current_time - state['last_click_time'] > 0.3:  # 300ms de délai minimum
                state['last_click_time'] = current_time
                
                x, y = value["x"], value["y"]
                
                # Vérifier que ce n'est pas un point existant
                is_new_point = True
                for p in state['pending_points']:
                    if abs(p[0] - x) < 10 and abs(p[1] - y) < 10:
                        is_new_point = False
                        break
                
                if is_new_point:
                    # Ajouter le point
                    state['pending_points'].append((x, y))
                    state['click_counter'] += 1
                    
                    # Vérifier l'auto-complétion
                    if (config.get('auto_complete') and 
                        len(state['pending_points']) >= config.get('points', 0)):
                        
                        process_measurement_final(
                            selected_tool, state['pending_points'], measurements,
                            current_page, calibration, zoom
                        )
                        state['pending_points'] = []
                        state['base_image'] = None
                        time.sleep(0.1)  # Court délai pour assurer la synchronisation
                        st.rerun()
                    else:
                        # Forcer le rafraîchissement pour afficher le nouveau point
                        st.rerun()
    
    # Affichage des instructions
    if selected_tool in ['area', 'perimeter']:
        st.info("💡 Cliquez pour placer des points • **Enter** ou bouton ✅ pour valider • **Esc** pour annuler")
    else:
        st.info(f"💡 Cliquez {config.get('points', 0)} fois pour mesurer • **Esc** pour annuler")

def create_base_image_final(page_image: Image.Image, measurements: List[Dict],
                           current_page: int, detected_lines: Optional[List[Dict]]) -> Image.Image:
    """Crée l'image de base avec toutes les mesures existantes"""
    img = page_image.copy()
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Dessiner les lignes détectées si activé
    if detected_lines and st.session_state.get('show_detected_lines', False):
        for line in detected_lines:
            start = tuple(map(int, line['start']))
            end = tuple(map(int, line['end']))
            draw.line([start, end], fill=(200, 200, 200, 100), width=1)
    
    # Dessiner toutes les mesures de la page courante
    for measurement in measurements:
        if measurement.get('page') == current_page:
            draw_measurement_final(draw, measurement)
    
    return img

def draw_pending_points_final(draw: ImageDraw.Draw, points: List[Tuple], 
                             color: str, tool: str):
    """Dessine les points en cours de placement"""
    if not points:
        return
    
    # Convertir la couleur
    color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    color_rgba = color_rgb + (180,)
    
    # Dessiner les lignes entre les points
    if len(points) > 1:
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=color_rgba, width=3)
        
        # Ligne de fermeture pour area/perimeter
        if tool in ['area', 'perimeter'] and len(points) >= 3:
            # Ligne pointillée
            draw_dashed_line_final(draw, points[-1], points[0], color_rgba)
    
    # Dessiner les points
    for i, point in enumerate(points):
        x, y = point
        
        # Cercle blanc de fond
        draw.ellipse([x-10, y-10, x+10, y+10], fill='white', outline='white')
        
        # Point coloré
        draw.ellipse([x-8, y-8, x+8, y+8], fill=color_rgba, outline='black', width=2)
        
        # Numéro du point
        draw.text((x+12, y-8), str(i+1), fill='black')

def draw_dashed_line_final(draw: ImageDraw.Draw, start: Tuple, end: Tuple, color: Tuple):
    """Dessine une ligne pointillée"""
    x1, y1 = start
    x2, y2 = end
    
    length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    if length == 0:
        return
    
    segments = int(length / 10)
    if segments == 0:
        segments = 1
    
    for i in range(0, segments, 2):
        t1 = i / segments
        t2 = min((i + 1) / segments, 1)
        
        sx = x1 + t1 * (x2 - x1)
        sy = y1 + t1 * (y2 - y1)
        ex = x1 + t2 * (x2 - x1)
        ey = y1 + t2 * (y2 - y1)
        
        draw.line([(sx, sy), (ex, ey)], fill=color, width=2)

def draw_measurement_final(draw: ImageDraw.Draw, measurement: Dict):
    """Dessine une mesure complète sur l'image"""
    m_type = measurement.get('type')
    points = measurement.get('points', [])
    color = measurement.get('color', '#FF0000')
    
    if not points:
        return
    
    # Ajuster les points selon le zoom actuel
    current_zoom = st.session_state.pdf_viewer_state.get('zoom_level', 1.0)
    measurement_zoom = measurement.get('zoom_level', 1.0)
    zoom_ratio = current_zoom / measurement_zoom
    
    adjusted_points = [(p[0] * zoom_ratio, p[1] * zoom_ratio) for p in points]
    
    color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    color_rgba = color_rgb + (200,)
    
    if m_type == 'distance' and len(adjusted_points) >= 2:
        # Ligne
        draw.line([adjusted_points[0], adjusted_points[1]], fill=color_rgba, width=4)
        
        # Points aux extrémités
        for p in adjusted_points:
            draw.ellipse([p[0]-6, p[1]-6, p[0]+6, p[1]+6], 
                        fill=color_rgba, outline='white', width=2)
        
        # Label au milieu
        mid_x = (adjusted_points[0][0] + adjusted_points[1][0]) / 2
        mid_y = (adjusted_points[0][1] + adjusted_points[1][1]) / 2
        label = f"{measurement.get('label', '')}: {measurement.get('value', 0):.2f} {measurement.get('unit', '')}"
        draw_label_final(draw, (mid_x, mid_y), label)
    
    elif m_type in ['area', 'perimeter'] and len(adjusted_points) >= 3:
        # Remplissage pour l'aire
        if m_type == 'area':
            draw.polygon(adjusted_points, fill=color_rgba[:3] + (50,))
        
        # Contour
        for i in range(len(adjusted_points)):
            j = (i + 1) % len(adjusted_points)
            draw.line([adjusted_points[i], adjusted_points[j]], fill=color_rgba, width=3)
        
        # Points aux sommets
        for p in adjusted_points:
            draw.ellipse([p[0]-5, p[1]-5, p[0]+5, p[1]+5], 
                        fill=color_rgba, outline='white')
        
        # Label au centre
        center_x = sum(p[0] for p in adjusted_points) / len(adjusted_points)
        center_y = sum(p[1] for p in adjusted_points) / len(adjusted_points)
        label = f"{measurement.get('label', '')}: {measurement.get('value', 0):.2f} {measurement.get('unit', '')}"
        draw_label_final(draw, (center_x, center_y), label)
    
    elif m_type == 'angle' and len(adjusted_points) >= 3:
        # Lignes de l'angle
        draw.line([adjusted_points[0], adjusted_points[1]], fill=color_rgba, width=3)
        draw.line([adjusted_points[1], adjusted_points[2]], fill=color_rgba, width=3)
        
        # Arc d'angle
        draw_angle_arc_final(draw, adjusted_points[0], adjusted_points[1], 
                            adjusted_points[2], color_rgba)
        
        # Points
        for i, p in enumerate(adjusted_points):
            size = 8 if i == 1 else 6
            draw.ellipse([p[0]-size, p[1]-size, p[0]+size, p[1]+size], 
                        fill=color_rgba, outline='white')
        
        # Label
        label = f"{measurement.get('label', 'Angle')}: {measurement.get('value', 0):.1f}°"
        draw_label_final(draw, adjusted_points[1], label, offset=(20, -20))

def draw_label_final(draw: ImageDraw.Draw, position: Tuple[float, float], 
                    text: str, offset: Tuple[int, int] = (0, 0)):
    """Dessine un label avec fond blanc"""
    x, y = position
    x += offset[0]
    y += offset[1]
    
    # Calculer la taille du texte
    bbox = draw.textbbox((0, 0), text)
    width = bbox[2] - bbox[0] + 8
    height = bbox[3] - bbox[1] + 4
    
    # Dessiner le fond
    draw.rectangle([x - width//2, y - 2, x + width//2, y + height],
                  fill=(255, 255, 255, 240), outline='black')
    
    # Dessiner le texte
    draw.text((x - width//2 + 4, y), text, fill='black')

def draw_angle_arc_final(draw: ImageDraw.Draw, p1: Tuple, p2: Tuple, p3: Tuple, color: Tuple):
    """Dessine l'arc pour représenter l'angle"""
    angle1 = math.degrees(math.atan2(p1[1] - p2[1], p1[0] - p2[0]))
    angle2 = math.degrees(math.atan2(p3[1] - p2[1], p3[0] - p2[0]))
    
    radius = 35
    bbox = [p2[0] - radius, p2[1] - radius, p2[0] + radius, p2[1] + radius]
    
    start = min(angle1, angle2)
    end = max(angle1, angle2)
    
    if end - start > 180:
        start, end = end, start + 360
    
    draw.arc(bbox, start, end, fill=color, width=2)

def process_measurement_final(tool: str, points: List[Tuple], measurements: List[Dict],
                             current_page: int, calibration: Dict, zoom_level: float):
    """Traite et enregistre une mesure complète"""
    if not points:
        return
    
    # Calculer la calibration ajustée selon le zoom
    calibration_zoom = st.session_state.pdf_viewer_state.get('calibration_zoom', 1.0)
    zoom_ratio = zoom_level / calibration_zoom if calibration_zoom != 0 else 1.0
    adjusted_cal = calibration.get('value', 1.0) / zoom_ratio
    
    measurement = None
    
    if tool == 'distance' and len(points) >= 2:
        dist = math.sqrt((points[1][0] - points[0][0])**2 + 
                        (points[1][1] - points[0][1])**2)
        measurement = {
            'type': 'distance',
            'points': points[:2],
            'page': current_page,
            'value': dist * adjusted_cal,
            'unit': calibration.get('unit', 'cm'),
            'label': f"Distance_{len([m for m in measurements if m['type'] == 'distance']) + 1}",
            'color': '#FF0000',
            'zoom_level': zoom_level
        }
    
    elif tool == 'area' and len(points) >= 3:
        # Calcul de l'aire par la formule du lacet
        area = 0.0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        area = abs(area) / 2.0
        
        measurement = {
            'type': 'area',
            'points': points[:],
            'page': current_page,
            'value': area * adjusted_cal * adjusted_cal,
            'unit': f"{calibration.get('unit', 'cm')}²",
            'label': f"Surface_{len([m for m in measurements if m['type'] == 'area']) + 1}",
            'color': '#00FF00',
            'zoom_level': zoom_level
        }
    
    elif tool == 'perimeter' and len(points) >= 3:
        # Calcul du périmètre
        perim = 0.0
        for i in range(len(points)):
            j = (i + 1) % len(points)
            perim += math.sqrt((points[j][0] - points[i][0])**2 + 
                              (points[j][1] - points[i][1])**2)
        
        measurement = {
            'type': 'perimeter',
            'points': points[:],
            'page': current_page,
            'value': perim * adjusted_cal,
            'unit': calibration.get('unit', 'cm'),
            'label': f"Périmètre_{len([m for m in measurements if m['type'] == 'perimeter']) + 1}",
            'color': '#0000FF',
            'zoom_level': zoom_level
        }
    
    elif tool == 'angle' and len(points) >= 3:
        # Calcul de l'angle
        v1 = (points[0][0] - points[1][0], points[0][1] - points[1][1])
        v2 = (points[2][0] - points[1][0], points[2][1] - points[1][1])
        
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        det = v1[0] * v2[1] - v1[1] * v2[0]
        
        angle = abs(math.degrees(math.atan2(det, dot)))
        
        measurement = {
            'type': 'angle',
            'points': points[:3],
            'page': current_page,
            'value': angle,
            'unit': '°',
            'label': f"Angle_{len([m for m in measurements if m['type'] == 'angle']) + 1}",
            'color': '#FF00FF',
            'zoom_level': zoom_level
        }
    
    elif tool == 'calibration' and len(points) >= 2:
        dist = math.sqrt((points[1][0] - points[0][0])**2 + 
                        (points[1][1] - points[0][1])**2)
        st.session_state.calibration_distance = dist
        st.session_state.show_calibration_dialog = True
        st.session_state.pdf_viewer_state['calibration_zoom'] = zoom_level
        return
    
    if measurement:
        measurements.append(measurement)
        st.session_state.temp_measurement = measurement
        st.session_state.temp_measurement_index = len(measurements) - 1
        st.success(f"✅ {measurement['label']}: {measurement['value']:.2f} {measurement['unit']}")