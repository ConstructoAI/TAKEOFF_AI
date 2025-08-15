import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import math
from typing import List, Dict, Optional, Tuple
import io
import base64

def ClickablePDFViewer(pdf_processor, current_page: int, measurements: List[Dict],
                      selected_tool: str, calibration: Dict, detected_lines: Optional[List[Dict]] = None):
    """Visualiseur PDF avec clics directs sur l'image"""
    
    # Contrôle du zoom
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        zoom_level = st.slider(
            "🔍 Zoom",
            min_value=0.5,
            max_value=3.0,
            value=st.session_state.get('zoom_level', 1.5),
            step=0.1
        )
        st.session_state.zoom_level = zoom_level
    
    # Obtenir l'image
    page_image = pdf_processor.get_page_image(current_page, zoom=zoom_level)
    
    if not page_image:
        st.error("Impossible de charger la page PDF")
        return
    
    # Préparer l'image avec les mesures existantes
    display_image = prepare_display_image(page_image, measurements, current_page, detected_lines)
    
    # Initialiser les points cliqués
    if 'measurement_points' not in st.session_state:
        st.session_state.measurement_points = []
    
    # Afficher les instructions selon l'outil
    tool_info = {
        'distance': {
            'name': '📏 Mesure de distance',
            'instruction': 'Cliquez sur 2 points pour mesurer une distance',
            'points_needed': 2,
            'color': '#FF0000'
        },
        'area': {
            'name': '⬜ Mesure de surface',
            'instruction': 'Cliquez sur au moins 3 points pour définir une surface (double-clic pour fermer)',
            'points_needed': 3,
            'color': '#00FF00'
        },
        'perimeter': {
            'name': '🔲 Mesure de périmètre',
            'instruction': 'Cliquez sur au moins 3 points pour définir un périmètre (double-clic pour fermer)',
            'points_needed': 3,
            'color': '#0000FF'
        },
        'angle': {
            'name': '📐 Mesure d\'angle',
            'instruction': 'Cliquez sur 3 points (le 2ème est le sommet de l\'angle)',
            'points_needed': 3,
            'color': '#FF00FF'
        },
        'calibration': {
            'name': '🎯 Calibration',
            'instruction': 'Cliquez sur 2 points d\'une distance connue',
            'points_needed': 2,
            'color': '#FFA500'
        }
    }
    
    info = tool_info.get(selected_tool, {})
    
    # Afficher les informations de l'outil
    col1, col2, col3 = st.columns([3, 1, 1])
    
    with col1:
        st.markdown(f"### {info.get('name', selected_tool)}")
        st.info(info.get('instruction', ''))
    
    with col2:
        points_needed = info.get('points_needed', 0)
        current_points = len(st.session_state.measurement_points)
        st.metric("Points", f"{current_points}/{points_needed}")
    
    with col3:
        if st.button("🔄 Réinitialiser"):
            st.session_state.measurement_points = []
            st.rerun()
    
    # Dessiner les points en cours sur l'image
    if st.session_state.measurement_points:
        display_image = draw_current_measurement(
            display_image, 
            st.session_state.measurement_points,
            info.get('color', '#000000'),
            selected_tool
        )
    
    # Image cliquable
    value = streamlit_image_coordinates(
        display_image,
        key=f"canvas_{current_page}_{selected_tool}_{zoom_level}"
    )
    
    # Gérer le clic
    if value is not None:
        x = value["x"]
        y = value["y"]
        
        # Vérifier si c'est un nouveau clic (pas le même point)
        if not st.session_state.measurement_points or \
           (x, y) != st.session_state.measurement_points[-1]:
            
            # Appliquer l'accrochage si activé
            if st.session_state.snap_enabled and detected_lines:
                snap_point = find_snap_point((x, y), detected_lines, st.session_state.snap_threshold)
                if snap_point:
                    x, y = snap_point
            
            # Ajouter le point
            st.session_state.measurement_points.append((x, y))
            
            # Vérifier si on peut créer la mesure automatiquement
            if should_create_measurement(selected_tool, st.session_state.measurement_points):
                create_measurement_from_points(
                    selected_tool,
                    st.session_state.measurement_points,
                    measurements,
                    current_page,
                    calibration
                )
                st.rerun()
            else:
                # Pour éviter le rechargement, on met à jour l'affichage différemment
                # On stocke temporairement les points dans une clé unique
                st.session_state[f'temp_points_{current_page}'] = st.session_state.measurement_points.copy()
    
    # Afficher les points sélectionnés
    if st.session_state.measurement_points:
        with st.expander("📍 Points sélectionnés", expanded=True):
            for i, point in enumerate(st.session_state.measurement_points):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(f"Point {i+1}")
                with col2:
                    st.text(f"X: {point[0]:.0f}, Y: {point[1]:.0f}")
                with col3:
                    if st.button("❌", key=f"del_point_{i}"):
                        st.session_state.measurement_points.pop(i)
                        st.rerun()
            
            # Bouton pour forcer la création de la mesure
            if selected_tool in ['area', 'perimeter'] and len(st.session_state.measurement_points) >= 3:
                if st.button("✅ Fermer et valider la forme", type="primary"):
                    create_measurement_from_points(
                        selected_tool,
                        st.session_state.measurement_points,
                        measurements,
                        current_page,
                        calibration
                    )
                    st.rerun()

def prepare_display_image(base_image: Image.Image, measurements: List[Dict], 
                         current_page: int, detected_lines: Optional[List[Dict]]) -> Image.Image:
    """Prépare l'image avec les mesures existantes"""
    img = base_image.copy()
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Dessiner les lignes détectées si activées
    if detected_lines and st.session_state.get('show_detected_lines', False):
        for line in detected_lines:
            start = tuple(map(int, line['start']))
            end = tuple(map(int, line['end']))
            draw.line([start, end], fill=(200, 200, 200, 100), width=1)
    
    # Dessiner les mesures existantes
    for measurement in measurements:
        if measurement.get('page') != current_page:
            continue
        draw_measurement(draw, measurement)
    
    return img

def draw_current_measurement(image: Image.Image, points: List[Tuple], 
                           color: str, tool: str) -> Image.Image:
    """Dessine la mesure en cours de création"""
    img = image.copy()
    draw = ImageDraw.Draw(img, 'RGBA')
    
    color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    color_rgba = color_rgb + (150,)
    
    # Dessiner les lignes
    if len(points) > 1:
        if tool in ['area', 'perimeter']:
            # Polygone
            for i in range(len(points) - 1):
                draw.line([points[i], points[i+1]], fill=color_rgba, width=3)
            # Ligne de fermeture en pointillés
            if len(points) >= 3:
                draw_dashed_line(draw, points[-1], points[0], color_rgba, 3)
        else:
            # Lignes simples
            for i in range(len(points) - 1):
                draw.line([points[i], points[i+1]], fill=color_rgba, width=3)
    
    # Dessiner les points
    for i, point in enumerate(points):
        x, y = point
        # Point plus gros pour le sommet de l'angle
        size = 10 if tool == 'angle' and i == 1 else 8
        draw.ellipse([x-size, y-size, x+size, y+size], 
                    fill=color_rgba, outline='white', width=2)
        # Numéro du point
        draw.text((x+12, y-12), str(i+1), fill=color_rgb)
    
    return img

def draw_dashed_line(draw: ImageDraw.Draw, start: Tuple, end: Tuple, 
                    color: Tuple, width: int):
    """Dessine une ligne en pointillés"""
    x1, y1 = start
    x2, y2 = end
    
    # Calculer la longueur et le nombre de segments
    length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    segments = int(length / 10)  # Un segment tous les 10 pixels
    
    if segments > 0:
        dx = (x2 - x1) / segments
        dy = (y2 - y1) / segments
        
        for i in range(0, segments, 2):  # Dessiner un segment sur deux
            start_x = x1 + i * dx
            start_y = y1 + i * dy
            end_x = x1 + (i + 1) * dx
            end_y = y1 + (i + 1) * dy
            draw.line([(start_x, start_y), (end_x, end_y)], fill=color, width=width)

def draw_measurement(draw: ImageDraw.Draw, measurement: Dict):
    """Dessine une mesure complète"""
    m_type = measurement.get('type')
    points = measurement.get('points', [])
    color = measurement.get('color', '#FF0000')
    
    if not points:
        return
    
    color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    color_rgba = color_rgb + (200,)
    
    if m_type == 'distance' and len(points) >= 2:
        # Ligne
        draw.line([tuple(points[0]), tuple(points[1])], fill=color_rgba, width=5)
        
        # Points
        for p in points[:2]:
            x, y = p
            draw.ellipse([x-8, y-8, x+8, y+8], fill=color_rgba, outline='white', width=2)
        
        # Label
        draw_measurement_label(draw, points, measurement)
    
    elif m_type in ['area', 'perimeter'] and len(points) >= 3:
        # Polygone
        polygon_points = [tuple(p) for p in points]
        
        if m_type == 'area':
            # Remplir avec transparence
            draw.polygon(polygon_points, fill=color_rgba[:3] + (50,))
        
        # Contour
        for i in range(len(polygon_points)):
            next_i = (i + 1) % len(polygon_points)
            draw.line([polygon_points[i], polygon_points[next_i]], 
                    fill=color_rgba, width=4)
        
        # Points
        for p in points:
            x, y = p
            draw.ellipse([x-6, y-6, x+6, y+6], fill=color_rgba, outline='white', width=2)
        
        # Label au centre
        draw_measurement_label(draw, points, measurement)
    
    elif m_type == 'angle' and len(points) >= 3:
        # Lignes
        draw.line([tuple(points[0]), tuple(points[1])], fill=color_rgba, width=4)
        draw.line([tuple(points[1]), tuple(points[2])], fill=color_rgba, width=4)
        
        # Arc d'angle
        draw_angle_arc(draw, points[0], points[1], points[2], color_rgba)
        
        # Points
        for i, p in enumerate(points[:3]):
            x, y = p
            size = 10 if i == 1 else 8
            draw.ellipse([x-size, y-size, x+size, y+size], 
                        fill=color_rgba, outline='white', width=2)
        
        # Label
        draw_measurement_label(draw, [points[1]], measurement)

def draw_angle_arc(draw: ImageDraw.Draw, p1: Tuple, p2: Tuple, p3: Tuple, color: Tuple):
    """Dessine un arc pour visualiser l'angle"""
    # Calculer les angles des vecteurs
    v1_angle = math.degrees(math.atan2(p1[1] - p2[1], p1[0] - p2[0]))
    v2_angle = math.degrees(math.atan2(p3[1] - p2[1], p3[0] - p2[0]))
    
    # Rayon de l'arc
    radius = 40
    
    # Déterminer les angles de début et fin
    start_angle = min(v1_angle, v2_angle)
    end_angle = max(v1_angle, v2_angle)
    
    # S'assurer que l'arc prend le chemin le plus court
    if end_angle - start_angle > 180:
        start_angle, end_angle = end_angle, start_angle + 360
    
    # Dessiner l'arc
    bbox = [p2[0] - radius, p2[1] - radius, p2[0] + radius, p2[1] + radius]
    draw.arc(bbox, start_angle, end_angle, fill=color, width=2)

def draw_measurement_label(draw: ImageDraw.Draw, points: List[Tuple], measurement: Dict):
    """Dessine le label d'une mesure"""
    if not measurement.get('label') or measurement.get('value') is None:
        return
    
    # Calculer la position du label
    if len(points) == 1:
        x, y = points[0]
        y += 20  # Décaler vers le bas
    elif len(points) == 2:
        x = (points[0][0] + points[1][0]) / 2
        y = (points[0][1] + points[1][1]) / 2
    else:
        # Centre du polygone
        x = sum(p[0] for p in points) / len(points)
        y = sum(p[1] for p in points) / len(points)
    
    # Texte du label
    value = measurement['value']
    unit = measurement.get('unit', '')
    label = measurement.get('label', '')
    
    if measurement['type'] == 'angle':
        text = f"{label}: {value:.1f}{unit}"
    else:
        text = f"{label}: {value:.2f} {unit}"
    
    # Dessiner le fond
    bbox = draw.textbbox((x, y), text)
    padding = 5
    draw.rectangle(
        [bbox[0]-padding, bbox[1]-padding, bbox[2]+padding, bbox[3]+padding],
        fill=(255, 255, 255, 230),
        outline='black'
    )
    
    # Dessiner le texte
    draw.text((x, y), text, fill='black')

def find_snap_point(cursor: Tuple[float, float], lines: List[Dict], 
                   threshold: float) -> Optional[Tuple[float, float]]:
    """Trouve le point d'accrochage le plus proche"""
    min_distance = threshold
    snap_point = None
    
    for line in lines:
        # Vérifier les extrémités
        for point in [line['start'], line['end']]:
            dist = math.sqrt((cursor[0] - point[0])**2 + (cursor[1] - point[1])**2)
            if dist < min_distance:
                min_distance = dist
                snap_point = tuple(point)
        
        # Vérifier le milieu
        mid_x = (line['start'][0] + line['end'][0]) / 2
        mid_y = (line['start'][1] + line['end'][1]) / 2
        dist = math.sqrt((cursor[0] - mid_x)**2 + (cursor[1] - mid_y)**2)
        if dist < min_distance:
            min_distance = dist
            snap_point = (mid_x, mid_y)
    
    return snap_point

def should_create_measurement(tool: str, points: List[Tuple]) -> bool:
    """Détermine si on doit créer automatiquement la mesure"""
    if tool in ['distance', 'calibration'] and len(points) >= 2:
        return True
    elif tool == 'angle' and len(points) >= 3:
        return True
    # Pour area et perimeter, on attend le bouton de validation
    return False

def create_measurement_from_points(tool: str, points: List[Tuple], measurements: List[Dict],
                                 current_page: int, calibration: Dict):
    """Crée une mesure à partir des points cliqués"""
    if tool == 'distance':
        pixel_distance = math.sqrt((points[1][0] - points[0][0])**2 + 
                                 (points[1][1] - points[0][1])**2)
        
        measurement = {
            'type': 'distance',
            'points': points[:2],
            'page': current_page,
            'value': pixel_distance * calibration.get('value', 1.0),
            'unit': calibration.get('unit', 'cm'),
            'label': f"Distance_{len([m for m in measurements if m['type'] == 'distance']) + 1}",
            'color': '#FF0000'
        }
        
        add_product_to_measurement(measurement)
        measurements.append(measurement)
        st.session_state.measurement_points = []
        st.success(f"✅ Distance: {measurement['value']:.2f} {measurement['unit']}")
    
    elif tool == 'area' and len(points) >= 3:
        pixel_area = calculate_polygon_area(points)
        cal_factor = calibration.get('value', 1.0)
        
        measurement = {
            'type': 'area',
            'points': points,
            'page': current_page,
            'value': pixel_area * cal_factor * cal_factor,
            'unit': f"{calibration.get('unit', 'cm')}²",
            'label': f"Surface_{len([m for m in measurements if m['type'] == 'area']) + 1}",
            'color': '#00FF00'
        }
        
        add_product_to_measurement(measurement)
        measurements.append(measurement)
        st.session_state.measurement_points = []
        st.success(f"✅ Surface: {measurement['value']:.2f} {measurement['unit']}")
    
    elif tool == 'perimeter' and len(points) >= 3:
        pixel_perimeter = calculate_perimeter(points, closed=True)
        
        measurement = {
            'type': 'perimeter',
            'points': points,
            'page': current_page,
            'value': pixel_perimeter * calibration.get('value', 1.0),
            'unit': calibration.get('unit', 'cm'),
            'label': f"Périmètre_{len([m for m in measurements if m['type'] == 'perimeter']) + 1}",
            'color': '#0000FF'
        }
        
        add_product_to_measurement(measurement)
        measurements.append(measurement)
        st.session_state.measurement_points = []
        st.success(f"✅ Périmètre: {measurement['value']:.2f} {measurement['unit']}")
    
    elif tool == 'angle' and len(points) >= 3:
        angle = calculate_angle(points[0], points[1], points[2])
        
        measurement = {
            'type': 'angle',
            'points': points[:3],
            'page': current_page,
            'value': angle,
            'unit': '°',
            'label': f"Angle_{len([m for m in measurements if m['type'] == 'angle']) + 1}",
            'color': '#FF00FF'
        }
        
        measurements.append(measurement)
        st.session_state.measurement_points = []
        st.success(f"✅ Angle: {angle:.1f}°")
    
    elif tool == 'calibration' and len(points) >= 2:
        pixel_distance = math.sqrt((points[1][0] - points[0][0])**2 + 
                                 (points[1][1] - points[0][1])**2)
        
        # Interface de calibration
        with st.form("calibration_form", clear_on_submit=True):
            st.write("### 🎯 Calibration")
            st.info(f"Distance mesurée: {pixel_distance:.2f} pixels")
            
            col1, col2 = st.columns(2)
            with col1:
                real_value = st.number_input(
                    "Distance réelle",
                    min_value=0.01,
                    value=1.0,
                    step=0.01
                )
            with col2:
                unit = st.selectbox(
                    "Unité",
                    options=['mm', 'cm', 'm', 'in', 'ft']
                )
            
            if st.form_submit_button("✅ Appliquer la calibration", type="primary"):
                cal_factor = real_value / pixel_distance
                st.session_state.current_project['calibration'] = {
                    'value': cal_factor,
                    'unit': unit
                }
                st.session_state.measurement_points = []
                st.success(f"✅ Calibration appliquée: 1 pixel = {cal_factor:.4f} {unit}")
                st.rerun()

def add_product_to_measurement(measurement: Dict):
    """Ajoute le produit sélectionné à la mesure"""
    if st.session_state.selected_product and st.session_state.selected_category:
        product_data = st.session_state.product_catalog.get_product(
            st.session_state.selected_category,
            st.session_state.selected_product
        )
        if product_data:
            measurement['product'] = {
                'name': st.session_state.selected_product,
                'category': st.session_state.selected_category,
                'price': product_data.get('price', 0),
                'price_unit': product_data.get('price_unit', ''),
                'color': product_data.get('color', '#CCCCCC')
            }
            # Utiliser la couleur du produit
            measurement['color'] = product_data.get('color', measurement['color'])

def calculate_polygon_area(points: List[Tuple]) -> float:
    """Calcule l'aire d'un polygone avec la formule du lacet"""
    n = len(points)
    area = 0.0
    
    for i in range(n):
        j = (i + 1) % n
        area += points[i][0] * points[j][1]
        area -= points[j][0] * points[i][1]
    
    return abs(area) / 2.0

def calculate_perimeter(points: List[Tuple], closed: bool = True) -> float:
    """Calcule le périmètre d'une forme"""
    perimeter = 0.0
    
    for i in range(len(points) - 1):
        perimeter += math.sqrt((points[i+1][0] - points[i][0])**2 + 
                             (points[i+1][1] - points[i][1])**2)
    
    if closed and len(points) > 2:
        perimeter += math.sqrt((points[0][0] - points[-1][0])**2 + 
                             (points[0][1] - points[-1][1])**2)
    
    return perimeter

def calculate_angle(p1: Tuple, p2: Tuple, p3: Tuple) -> float:
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