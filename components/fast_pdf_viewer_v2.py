import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import math
from typing import List, Dict, Optional, Tuple
import time

def FastPDFViewerV2(pdf_processor, current_page: int, measurements: List[Dict],
                    selected_tool: str, calibration: Dict, detected_lines: Optional[List[Dict]] = None):
    """Visualiseur PDF optimisé avec mise à jour rapide"""
    
    # Initialiser l'état persistant
    if 'pdf_fast_state' not in st.session_state:
        st.session_state.pdf_fast_state = {
            'pending_points': [],
            'last_tool': selected_tool,
            'last_page': current_page,
            'click_count': 0,
            'zoom_level': 1.5,
            'calibration_zoom': 1.0,
            'last_coordinates': None,
            'processing': False,
            'base_image': None,
            'base_image_key': None
        }
    
    state = st.session_state.pdf_fast_state
    
    # Réinitialiser si changement d'outil ou de page
    if state['last_tool'] != selected_tool or state['last_page'] != current_page:
        state['pending_points'] = []
        state['last_tool'] = selected_tool
        state['last_page'] = current_page
        state['click_count'] = 0
        state['last_coordinates'] = None
    
    # Configuration de l'outil
    tool_configs = {
        'distance': {'points': 2, 'auto_complete': True, 'color': '#FF0000', 'name': '📏 Distance'},
        'angle': {'points': 3, 'auto_complete': True, 'color': '#FF00FF', 'name': '📐 Angle'},
        'area': {'points': 3, 'auto_complete': False, 'color': '#00FF00', 'name': '⬜ Surface'},
        'perimeter': {'points': 3, 'auto_complete': False, 'color': '#0000FF', 'name': '🔲 Périmètre'},
        'calibration': {'points': 2, 'auto_complete': True, 'color': '#FFA500', 'name': '🎯 Calibration'}
    }
    
    config = tool_configs.get(selected_tool, {})
    
    # Interface utilisateur
    col1, col2, col3 = st.columns([8, 1, 1])
    
    with col1:
        st.markdown(f"**{config.get('name', selected_tool)}** - {len(state['pending_points'])} points")
        if selected_tool in ['area', 'perimeter']:
            st.caption("Cliquez pour placer des points • Double-clic ou Enter pour fermer")
    
    with col2:
        can_validate = (
            (selected_tool in ['area', 'perimeter'] and len(state['pending_points']) >= 3) or
            (config.get('auto_complete') and len(state['pending_points']) >= config.get('points', 0))
        )
        
        if can_validate and st.button("✅", key="validate_fast", help="Valider"):
            process_measurement_complete(
                selected_tool, state['pending_points'], measurements,
                current_page, calibration, state['zoom_level']
            )
            state['pending_points'] = []
            state['click_count'] = 0
            state['base_image'] = None  # Force redraw
            st.rerun()
    
    with col3:
        if st.button("🔄", key="clear_fast", help="Effacer"):
            state['pending_points'] = []
            state['click_count'] = 0
            state['last_coordinates'] = None
            st.rerun()
    
    # Contrôle du zoom (slider uniquement pour éviter les reloads)
    zoom_level = st.slider(
        "🔍 Zoom",
        min_value=0.5,
        max_value=3.0,
        value=state['zoom_level'],
        step=0.1,
        key='zoom_slider_fast',
        help="Utilisez Alt+/- pour zoomer rapidement"
    )
    
    if zoom_level != state['zoom_level']:
        state['zoom_level'] = zoom_level
        state['base_image'] = None
    
    # Générer une clé unique pour le cache d'image
    image_key = f"{current_page}_{zoom_level}_{len(measurements)}_{selected_tool}"
    
    # Obtenir ou créer l'image de base
    if state['base_image_key'] != image_key or state['base_image'] is None:
        page_image = pdf_processor.get_page_image(current_page, zoom=zoom_level)
        if page_image:
            state['base_image'] = draw_base_image_fast(
                page_image, measurements, current_page, detected_lines
            )
            state['base_image_key'] = image_key
    
    if state['base_image'] is None:
        st.error("Impossible de charger la page PDF")
        return
    
    # Créer l'image d'affichage avec les points en cours
    display_image = state['base_image'].copy()
    if state['pending_points']:
        draw_pending_points_fast(display_image, state['pending_points'], 
                                config.get('color', '#000000'), selected_tool)
    
    # Container pour l'image
    img_container = st.container()
    
    with img_container:
        # Créer une clé unique qui change avec les points
        img_key = f"pdf_{current_page}_{selected_tool}_{state['click_count']}"
        
        # Image cliquable
        coordinates = streamlit_image_coordinates(
            display_image,
            key=img_key
        )
        
        # Traiter le clic
        if coordinates is not None:
            # Éviter le double traitement
            coord_tuple = (coordinates["x"], coordinates["y"])
            if coord_tuple != state['last_coordinates']:
                state['last_coordinates'] = coord_tuple
                
                # Ajouter le point
                state['pending_points'].append(coord_tuple)
                state['click_count'] += 1
                
                # Auto-complétion
                if (config.get('auto_complete') and 
                    len(state['pending_points']) >= config.get('points', 0)):
                    
                    process_measurement_complete(
                        selected_tool, state['pending_points'], measurements,
                        current_page, calibration, zoom_level
                    )
                    state['pending_points'] = []
                    state['click_count'] = 0
                    state['base_image'] = None
                    time.sleep(0.1)  # Petit délai pour éviter les conflits
                    st.rerun()
                else:
                    # Forcer un refresh léger
                    st.rerun()
    
    # Instructions
    st.info(f"""
    💡 **Conseils** :
    - Cliquez sur l'image pour placer des points
    - **Escape** : Annuler la mesure en cours
    - **Enter** : Valider (pour surface/périmètre)
    - **Alt +/-** : Zoomer/Dézoomer
    """)

def draw_base_image_fast(base_image: Image.Image, measurements: List[Dict], 
                        current_page: int, detected_lines: Optional[List[Dict]]) -> Image.Image:
    """Dessine l'image de base avec les mesures existantes"""
    img = base_image.copy()
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Lignes détectées
    if detected_lines and st.session_state.get('show_detected_lines', False):
        for line in detected_lines:
            start = tuple(map(int, line['start']))
            end = tuple(map(int, line['end']))
            draw.line([start, end], fill=(200, 200, 200, 100), width=1)
    
    # Mesures existantes
    for measurement in measurements:
        if measurement.get('page') == current_page:
            draw_measurement_fast(draw, measurement)
    
    return img

def draw_pending_points_fast(img: Image.Image, points: List[Tuple], color: str, tool: str):
    """Dessine les points en cours"""
    draw = ImageDraw.Draw(img, 'RGBA')
    
    if not points:
        return
    
    color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    color_rgba = color_rgb + (180,)
    
    # Dessiner les lignes
    if len(points) > 1:
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=color_rgba, width=3)
        
        # Ligne de fermeture pour area/perimeter
        if tool in ['area', 'perimeter'] and len(points) >= 3:
            # Ligne pointillée pour la fermeture
            draw_dashed_line_fast(draw, points[-1], points[0], color_rgba)
    
    # Dessiner les points
    for i, point in enumerate(points):
        x, y = point
        size = 8
        
        # Cercle blanc de fond
        draw.ellipse([x-size-2, y-size-2, x+size+2, y+size+2], 
                    fill='white', outline='white')
        
        # Point coloré
        draw.ellipse([x-size, y-size, x+size, y+size], 
                    fill=color_rgba, outline='black', width=2)
        
        # Numéro du point
        draw.text((x+size+5, y-size), str(i+1), fill='black')

def draw_dashed_line_fast(draw: ImageDraw.Draw, start: Tuple, end: Tuple, color: Tuple):
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

def process_measurement_complete(tool: str, points: List[Tuple], measurements: List[Dict],
                               current_page: int, calibration: Dict, zoom_level: float):
    """Traite et enregistre la mesure"""
    if not points:
        return
    
    # Ajuster la calibration selon le zoom
    calibration_zoom = st.session_state.pdf_fast_state.get('calibration_zoom', 1.0)
    zoom_ratio = zoom_level / calibration_zoom if calibration_zoom != 0 else 1.0
    adjusted_calibration = calibration.get('value', 1.0) / zoom_ratio
    
    measurement = None
    
    if tool == 'distance' and len(points) >= 2:
        pixel_dist = math.sqrt((points[1][0] - points[0][0])**2 + 
                              (points[1][1] - points[0][1])**2)
        measurement = {
            'type': 'distance',
            'points': points[:2],
            'page': current_page,
            'value': pixel_dist * adjusted_calibration,
            'unit': calibration.get('unit', 'cm'),
            'label': f"Distance_{len([m for m in measurements if m['type'] == 'distance']) + 1}",
            'color': '#FF0000',
            'zoom_level': zoom_level
        }
    
    elif tool == 'area' and len(points) >= 3:
        area = calculate_polygon_area(points)
        measurement = {
            'type': 'area',
            'points': points[:],
            'page': current_page,
            'value': area * adjusted_calibration * adjusted_calibration,
            'unit': f"{calibration.get('unit', 'cm')}²",
            'label': f"Surface_{len([m for m in measurements if m['type'] == 'area']) + 1}",
            'color': '#00FF00',
            'zoom_level': zoom_level
        }
    
    elif tool == 'perimeter' and len(points) >= 3:
        perim = calculate_perimeter(points)
        measurement = {
            'type': 'perimeter',
            'points': points[:],
            'page': current_page,
            'value': perim * adjusted_calibration,
            'unit': calibration.get('unit', 'cm'),
            'label': f"Périmètre_{len([m for m in measurements if m['type'] == 'perimeter']) + 1}",
            'color': '#0000FF',
            'zoom_level': zoom_level
        }
    
    elif tool == 'angle' and len(points) >= 3:
        angle = calculate_angle(points[0], points[1], points[2])
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
        pixel_dist = math.sqrt((points[1][0] - points[0][0])**2 + 
                              (points[1][1] - points[0][1])**2)
        st.session_state.calibration_distance = pixel_dist
        st.session_state.show_calibration_dialog = True
        st.session_state.pdf_fast_state['calibration_zoom'] = zoom_level
        return
    
    if measurement:
        measurements.append(measurement)
        st.session_state.temp_measurement = measurement
        st.session_state.temp_measurement_index = len(measurements) - 1
        st.success(f"✅ {measurement['label']}: {measurement['value']:.2f} {measurement['unit']}")

def draw_measurement_fast(draw: ImageDraw.Draw, measurement: Dict):
    """Dessine une mesure complète"""
    m_type = measurement.get('type')
    points = measurement.get('points', [])
    color = measurement.get('color', '#FF0000')
    
    if not points:
        return
    
    # Ajuster selon le zoom actuel
    current_zoom = st.session_state.pdf_fast_state.get('zoom_level', 1.0)
    measurement_zoom = measurement.get('zoom_level', 1.0)
    zoom_ratio = current_zoom / measurement_zoom
    
    adjusted_points = [(p[0] * zoom_ratio, p[1] * zoom_ratio) for p in points]
    
    color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    color_rgba = color_rgb + (200,)
    
    if m_type == 'distance' and len(adjusted_points) >= 2:
        draw.line([tuple(adjusted_points[0]), tuple(adjusted_points[1])], fill=color_rgba, width=4)
        
        for p in adjusted_points:
            x, y = p
            draw.ellipse([x-6, y-6, x+6, y+6], fill=color_rgba, outline='white', width=2)
        
        # Label
        if measurement.get('label'):
            mid_x = (adjusted_points[0][0] + adjusted_points[1][0]) / 2
            mid_y = (adjusted_points[0][1] + adjusted_points[1][1]) / 2
            label = f"{measurement['label']}: {measurement.get('value', 0):.2f} {measurement.get('unit', '')}"
            product = measurement.get('product', {})
            if product.get('name'):
                label += f" [{product['name']}]"
            draw_label_fast(draw, (mid_x, mid_y), label)
    
    elif m_type in ['area', 'perimeter'] and len(adjusted_points) >= 3:
        if m_type == 'area':
            draw.polygon([tuple(p) for p in adjusted_points], fill=color_rgba[:3] + (50,))
        
        for i in range(len(adjusted_points)):
            next_i = (i + 1) % len(adjusted_points)
            draw.line([tuple(adjusted_points[i]), tuple(adjusted_points[next_i])], 
                     fill=color_rgba, width=3)
        
        for p in adjusted_points:
            x, y = p
            draw.ellipse([x-5, y-5, x+5, y+5], fill=color_rgba, outline='white')
        
        # Label au centre
        if measurement.get('label'):
            center_x = sum(p[0] for p in adjusted_points) / len(adjusted_points)
            center_y = sum(p[1] for p in adjusted_points) / len(adjusted_points)
            label = f"{measurement['label']}: {measurement.get('value', 0):.2f} {measurement.get('unit', '')}"
            product = measurement.get('product', {})
            if product.get('name'):
                label += f"\n[{product['name']}]"
            draw_label_fast(draw, (center_x, center_y), label)
    
    elif m_type == 'angle' and len(adjusted_points) >= 3:
        draw.line([tuple(adjusted_points[0]), tuple(adjusted_points[1])], fill=color_rgba, width=3)
        draw.line([tuple(adjusted_points[1]), tuple(adjusted_points[2])], fill=color_rgba, width=3)
        
        # Arc d'angle
        draw_angle_arc_fast(draw, adjusted_points[0], adjusted_points[1], 
                           adjusted_points[2], color_rgba)
        
        for i, p in enumerate(adjusted_points):
            x, y = p
            size = 8 if i == 1 else 6
            draw.ellipse([x-size, y-size, x+size, y+size], fill=color_rgba, outline='white')
        
        # Label
        if measurement.get('value') is not None:
            label = f"{measurement.get('label', 'Angle')}: {measurement['value']:.1f}°"
            draw_label_fast(draw, adjusted_points[1], label, offset=(20, -20))

def draw_label_fast(draw: ImageDraw.Draw, position: Tuple[float, float], text: str, 
                   offset: Tuple[int, int] = (0, 0)):
    """Dessine un label avec fond"""
    x, y = position
    x += offset[0]
    y += offset[1]
    
    # Calculer la taille du texte
    bbox = draw.textbbox((0, 0), text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    padding = 4
    
    # Fond blanc avec bordure
    draw.rectangle(
        [x - text_width//2 - padding, y - padding,
         x + text_width//2 + padding, y + text_height + padding],
        fill=(255, 255, 255, 240),
        outline='black'
    )
    
    # Texte centré
    draw.text((x - text_width//2, y), text, fill='black')

def draw_angle_arc_fast(draw: ImageDraw.Draw, p1: Tuple, p2: Tuple, p3: Tuple, color: Tuple):
    """Dessine un arc pour l'angle"""
    angle1 = math.degrees(math.atan2(p1[1] - p2[1], p1[0] - p2[0]))
    angle2 = math.degrees(math.atan2(p3[1] - p2[1], p3[0] - p2[0]))
    
    radius = 35
    bbox = [p2[0] - radius, p2[1] - radius, p2[0] + radius, p2[1] + radius]
    
    start = min(angle1, angle2)
    end = max(angle1, angle2)
    
    if end - start > 180:
        start, end = end, start + 360
    
    draw.arc(bbox, start, end, fill=color, width=2)

def calculate_polygon_area(points: List[Tuple]) -> float:
    """Calcule l'aire d'un polygone"""
    n = len(points)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    return abs(area) / 2.0

def calculate_perimeter(points: List[Tuple]) -> float:
    """Calcule le périmètre"""
    perim = 0.0
    for i in range(len(points)):
        j = (i + 1) % len(points)
        perim += math.sqrt((points[j][0] - points[i][0])**2 + 
                          (points[j][1] - points[i][1])**2)
    return perim

def calculate_angle(p1: Tuple, p2: Tuple, p3: Tuple) -> float:
    """Calcule l'angle entre trois points"""
    v1 = (p1[0] - p2[0], p1[1] - p2[1])
    v2 = (p3[0] - p2[0], p3[1] - p2[1])
    
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    det = v1[0] * v2[1] - v1[1] * v2[0]
    
    angle = math.degrees(math.atan2(det, dot))
    return abs(angle)