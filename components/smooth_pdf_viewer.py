import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import math
from typing import List, Dict, Optional, Tuple
import json

def SmoothPDFViewer(pdf_processor, current_page: int, measurements: List[Dict],
                    selected_tool: str, calibration: Dict, detected_lines: Optional[List[Dict]] = None):
    """Visualiseur PDF optimisé sans rechargements intempestifs"""
    
    # Initialiser l'état
    if 'pending_points' not in st.session_state:
        st.session_state.pending_points = []
    if 'last_click_count' not in st.session_state:
        st.session_state.last_click_count = 0
    if 'last_click_pos' not in st.session_state:
        st.session_state.last_click_pos = None
    
    # Contrôle du zoom
    zoom_level = st.slider(
        "🔍 Zoom",
        min_value=0.5,
        max_value=3.0,
        value=st.session_state.get('zoom_level', 1.5),
        step=0.1,
        key='zoom_pdf'
    )
    st.session_state.zoom_level = zoom_level
    
    # Obtenir l'image
    page_image = pdf_processor.get_page_image(current_page, zoom=zoom_level)
    
    if not page_image:
        st.error("Impossible de charger la page PDF")
        return
    
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
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    
    with col1:
        st.markdown(f"### {config.get('name', selected_tool)}")
    
    with col2:
        points_count = len(st.session_state.pending_points)
        st.metric("Points", points_count)
    
    with col3:
        # Bouton valider pour les outils qui le nécessitent
        can_validate = False
        if selected_tool in ['area', 'perimeter'] and points_count >= 3:
            can_validate = True
        elif selected_tool in ['distance', 'angle', 'calibration'] and points_count >= config.get('points', 0):
            can_validate = True
        
        if can_validate:
            if st.button("✅ Valider", type="primary", use_container_width=True):
                create_measurement(selected_tool, st.session_state.pending_points, 
                                 measurements, current_page, calibration)
                st.session_state.pending_points = []
                st.rerun()
    
    with col4:
        if st.button("🔄 Effacer", use_container_width=True):
            st.session_state.pending_points = []
            st.rerun()
    
    # Instructions avec raccourcis clavier
    instructions = {
        'distance': "Cliquez 2 points pour mesurer une distance",
        'angle': "Cliquez 3 points (sommet au milieu) pour mesurer un angle",
        'area': "Cliquez au moins 3 points puis appuyez sur le bouton Valider ou double-cliquez pour fermer la surface",
        'perimeter': "Cliquez au moins 3 points puis appuyez sur le bouton Valider ou double-cliquez pour fermer le périmètre",
        'calibration': "Cliquez 2 points d'une distance connue"
    }
    
    # Afficher les instructions avec info sur Enter
    instruction_text = instructions.get(selected_tool, "")
    if selected_tool in ['area', 'perimeter']:
        instruction_text += " | 💡 Astuce: Double-cliquez sur le dernier point pour fermer automatiquement"
    
    st.info(instruction_text)
    
    # Préparer l'image d'affichage
    display_image = prepare_image(page_image, measurements, current_page, 
                                 st.session_state.pending_points, config.get('color', '#000000'),
                                 selected_tool, detected_lines)
    
    # Container pour l'image avec une clé unique basée sur le nombre de points
    # Cela évite de recharger l'image si les points n'ont pas changé
    image_key = f"pdf_{current_page}_{selected_tool}_{zoom_level}_{len(st.session_state.pending_points)}"
    
    # Créer un placeholder pour l'image
    image_placeholder = st.empty()
    
    # Afficher l'image cliquable
    with image_placeholder.container():
        value = streamlit_image_coordinates(
            display_image,
            key=image_key
        )
        
        # Traiter le clic seulement s'il y a un nouveau clic
        if value is not None:
            x, y = value["x"], value["y"]
            current_pos = (x, y)
            
            # Vérifier si c'est un double-clic (clic rapide au même endroit)
            is_double_click = False
            if st.session_state.last_click_pos:
                last_x, last_y = st.session_state.last_click_pos
                if abs(x - last_x) < 10 and abs(y - last_y) < 10:
                    is_double_click = True
            
            # Pour area/perimeter, double-clic ferme la forme
            if is_double_click and selected_tool in ['area', 'perimeter'] and len(st.session_state.pending_points) >= 3:
                create_measurement(selected_tool, st.session_state.pending_points, 
                                 measurements, current_page, calibration)
                st.session_state.pending_points = []
                st.session_state.last_click_pos = None
                st.rerun()
            else:
                # Éviter les doublons de points (sauf si c'est un vrai nouveau point)
                if not st.session_state.last_click_pos or \
                   abs(x - st.session_state.last_click_pos[0]) > 5 or \
                   abs(y - st.session_state.last_click_pos[1]) > 5:
                    
                    # Appliquer l'accrochage
                    if st.session_state.snap_enabled and detected_lines:
                        snap_point = find_snap_point((x, y), detected_lines, st.session_state.snap_threshold)
                        if snap_point:
                            x, y = snap_point
                    
                    # Ajouter le point
                    st.session_state.pending_points.append((x, y))
                    st.session_state.last_click_pos = current_pos
                    
                    # Auto-complétion pour certains outils
                    if config.get('auto_complete') and len(st.session_state.pending_points) >= config.get('points', 0):
                        create_measurement(selected_tool, st.session_state.pending_points, 
                                         measurements, current_page, calibration)
                        st.session_state.pending_points = []
                        st.session_state.last_click_pos = None
                        st.rerun()
    
    # Afficher les points en cours
    if st.session_state.pending_points:
        with st.expander("📍 Points placés", expanded=False):
            for i, point in enumerate(st.session_state.pending_points):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"Point {i+1}: X={point[0]:.0f}, Y={point[1]:.0f}")
                with col2:
                    if st.button("❌", key=f"del_{i}"):
                        st.session_state.pending_points.pop(i)
                        st.rerun()
    
    # Ajouter un script JavaScript pour capturer la touche Enter
    if selected_tool in ['area', 'perimeter'] and len(st.session_state.pending_points) >= 3:
        st.markdown("""
        <script>
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                const buttons = document.querySelectorAll('button');
                buttons.forEach(button => {
                    if (button.textContent.includes('Valider')) {
                        button.click();
                    }
                });
            }
        });
        </script>
        """, unsafe_allow_html=True)

def prepare_image(base_image: Image.Image, measurements: List[Dict], current_page: int,
                 pending_points: List[Tuple], tool_color: str, tool: str,
                 detected_lines: Optional[List[Dict]]) -> Image.Image:
    """Prépare l'image avec toutes les annotations"""
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
            draw_measurement(draw, measurement)
    
    # Points en cours
    if pending_points:
        color_rgb = tuple(int(tool_color[i:i+2], 16) for i in (1, 3, 5))
        color_rgba = color_rgb + (180,)
        
        # Dessiner les lignes
        if len(pending_points) > 1:
            for i in range(len(pending_points) - 1):
                draw.line([pending_points[i], pending_points[i+1]], fill=color_rgba, width=3)
            
            # Ligne de fermeture pour polygones
            if tool in ['area', 'perimeter'] and len(pending_points) >= 3:
                # Ligne en pointillés
                draw_dashed_line(draw, pending_points[-1], pending_points[0], color_rgba)
        
        # Dessiner les points
        for i, point in enumerate(pending_points):
            x, y = point
            size = 10 if tool == 'angle' and i == 1 else 8
            
            # Cercle blanc de fond
            draw.ellipse([x-size-2, y-size-2, x+size+2, y+size+2], 
                        fill='white', outline='white')
            # Point coloré
            draw.ellipse([x-size, y-size, x+size, y+size], 
                        fill=color_rgba, outline='black')
            # Numéro
            draw.text((x+size+5, y-size), str(i+1), fill='black')
    
    return img

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
        draw.line([tuple(points[0]), tuple(points[1])], fill=color_rgba, width=4)
        
        # Points
        for p in points:
            x, y = p
            draw.ellipse([x-6, y-6, x+6, y+6], fill=color_rgba, outline='white', width=2)
        
        # Label
        if measurement.get('label') and measurement.get('value') is not None:
            mid_x = (points[0][0] + points[1][0]) / 2
            mid_y = (points[0][1] + points[1][1]) / 2
            label = f"{measurement['label']}: {measurement['value']:.2f} {measurement.get('unit', '')}"
            draw_label(draw, (mid_x, mid_y), label)
    
    elif m_type in ['area', 'perimeter'] and len(points) >= 3:
        # Polygone
        if m_type == 'area':
            draw.polygon([tuple(p) for p in points], fill=color_rgba[:3] + (50,))
        
        # Contour
        for i in range(len(points)):
            next_i = (i + 1) % len(points)
            draw.line([tuple(points[i]), tuple(points[next_i])], fill=color_rgba, width=3)
        
        # Points
        for p in points:
            x, y = p
            draw.ellipse([x-5, y-5, x+5, y+5], fill=color_rgba, outline='white')
        
        # Label au centre
        if measurement.get('label') and measurement.get('value') is not None:
            center_x = sum(p[0] for p in points) / len(points)
            center_y = sum(p[1] for p in points) / len(points)
            
            unit = measurement.get('unit', '')
            if m_type == 'area':
                label = f"{measurement['label']}: {measurement['value']:.2f} {unit}"
            else:
                label = f"{measurement['label']}: {measurement['value']:.2f} {unit}"
            
            draw_label(draw, (center_x, center_y), label)
    
    elif m_type == 'angle' and len(points) >= 3:
        # Lignes de l'angle
        draw.line([tuple(points[0]), tuple(points[1])], fill=color_rgba, width=3)
        draw.line([tuple(points[1]), tuple(points[2])], fill=color_rgba, width=3)
        
        # Arc
        draw_angle_arc(draw, points[0], points[1], points[2], color_rgba)
        
        # Points
        for i, p in enumerate(points):
            x, y = p
            size = 8 if i == 1 else 6
            draw.ellipse([x-size, y-size, x+size, y+size], fill=color_rgba, outline='white')
        
        # Label
        if measurement.get('value') is not None:
            label = f"{measurement.get('label', 'Angle')}: {measurement['value']:.1f}°"
            draw_label(draw, points[1], label, offset=(20, -20))

def draw_label(draw: ImageDraw.Draw, position: Tuple[float, float], text: str, 
              offset: Tuple[int, int] = (0, 0)):
    """Dessine un label avec fond"""
    x, y = position
    x += offset[0]
    y += offset[1]
    
    # Calculer la taille du texte
    bbox = draw.textbbox((x, y), text)
    padding = 4
    
    # Fond blanc avec bordure
    draw.rectangle(
        [bbox[0]-padding-1, bbox[1]-padding-1, bbox[2]+padding+1, bbox[3]+padding+1],
        fill='black'
    )
    draw.rectangle(
        [bbox[0]-padding, bbox[1]-padding, bbox[2]+padding, bbox[3]+padding],
        fill=(255, 255, 255, 240)
    )
    
    # Texte
    draw.text((x, y), text, fill='black')

def draw_dashed_line(draw: ImageDraw.Draw, start: Tuple, end: Tuple, color: Tuple):
    """Dessine une ligne en pointillés"""
    x1, y1 = start
    x2, y2 = end
    
    length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    if length == 0:
        return
    
    segments = int(length / 15)
    if segments == 0:
        segments = 1
    
    for i in range(0, segments, 2):
        t1 = i / segments
        t2 = min((i + 1) / segments, 1)
        
        sx = x1 + t1 * (x2 - x1)
        sy = y1 + t1 * (y2 - y1)
        ex = x1 + t2 * (x2 - x1)
        ey = y1 + t2 * (y2 - y1)
        
        draw.line([(sx, sy), (ex, ey)], fill=color, width=3)

def draw_angle_arc(draw: ImageDraw.Draw, p1: Tuple, p2: Tuple, p3: Tuple, color: Tuple):
    """Dessine un arc pour l'angle"""
    # Angles des vecteurs
    angle1 = math.degrees(math.atan2(p1[1] - p2[1], p1[0] - p2[0]))
    angle2 = math.degrees(math.atan2(p3[1] - p2[1], p3[0] - p2[0]))
    
    # Arc
    radius = 35
    bbox = [p2[0] - radius, p2[1] - radius, p2[0] + radius, p2[1] + radius]
    
    start = min(angle1, angle2)
    end = max(angle1, angle2)
    
    if end - start > 180:
        start, end = end, start + 360
    
    draw.arc(bbox, start, end, fill=color, width=2)

def find_snap_point(cursor: Tuple, lines: List[Dict], threshold: float) -> Optional[Tuple]:
    """Trouve le point d'accrochage le plus proche"""
    min_dist = threshold
    snap_point = None
    
    for line in lines:
        # Extrémités
        for point in [line['start'], line['end']]:
            dist = math.sqrt((cursor[0] - point[0])**2 + (cursor[1] - point[1])**2)
            if dist < min_dist:
                min_dist = dist
                snap_point = tuple(point)
        
        # Milieu
        mid = ((line['start'][0] + line['end'][0]) / 2,
               (line['start'][1] + line['end'][1]) / 2)
        dist = math.sqrt((cursor[0] - mid[0])**2 + (cursor[1] - mid[1])**2)
        if dist < min_dist:
            min_dist = dist
            snap_point = mid
    
    return snap_point

def create_measurement(tool: str, points: List[Tuple], measurements: List[Dict],
                      current_page: int, calibration: Dict):
    """Crée une mesure à partir des points"""
    if tool == 'distance' and len(points) >= 2:
        pixel_dist = math.sqrt((points[1][0] - points[0][0])**2 + 
                              (points[1][1] - points[0][1])**2)
        
        measurement = {
            'type': 'distance',
            'points': points[:2],
            'page': current_page,
            'value': pixel_dist * calibration.get('value', 1.0),
            'unit': calibration.get('unit', 'cm'),
            'label': f"Distance_{len([m for m in measurements if m['type'] == 'distance']) + 1}",
            'color': '#FF0000'
        }
        
        add_product_info(measurement)
        measurements.append(measurement)
        st.success(f"✅ Distance: {measurement['value']:.2f} {measurement['unit']}")
    
    elif tool == 'area' and len(points) >= 3:
        area = calculate_polygon_area(points)
        cal_value = calibration.get('value', 1.0)
        
        measurement = {
            'type': 'area',
            'points': points,
            'page': current_page,
            'value': area * cal_value * cal_value,
            'unit': f"{calibration.get('unit', 'cm')}²",
            'label': f"Surface_{len([m for m in measurements if m['type'] == 'area']) + 1}",
            'color': '#00FF00'
        }
        
        add_product_info(measurement)
        measurements.append(measurement)
        st.success(f"✅ Surface: {measurement['value']:.2f} {measurement['unit']}")
    
    elif tool == 'perimeter' and len(points) >= 3:
        perim = calculate_perimeter(points)
        
        measurement = {
            'type': 'perimeter',
            'points': points,
            'page': current_page,
            'value': perim * calibration.get('value', 1.0),
            'unit': calibration.get('unit', 'cm'),
            'label': f"Périmètre_{len([m for m in measurements if m['type'] == 'perimeter']) + 1}",
            'color': '#0000FF'
        }
        
        add_product_info(measurement)
        measurements.append(measurement)
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
        st.success(f"✅ Angle: {angle:.1f}°")
    
    elif tool == 'calibration' and len(points) >= 2:
        pixel_dist = math.sqrt((points[1][0] - points[0][0])**2 + 
                              (points[1][1] - points[0][1])**2)
        
        # Formulaire de calibration dans un dialog
        @st.dialog("🎯 Calibration")
        def calibration_dialog():
            st.info(f"Distance mesurée: {pixel_dist:.2f} pixels")
            
            col1, col2 = st.columns(2)
            with col1:
                real_value = st.number_input("Distance réelle", min_value=0.01, value=1.0, step=0.01)
            with col2:
                unit = st.selectbox("Unité", ['mm', 'cm', 'm', 'in', 'ft'])
            
            if st.button("Appliquer", type="primary"):
                cal_factor = real_value / pixel_dist
                st.session_state.current_project['calibration'] = {
                    'value': cal_factor,
                    'unit': unit
                }
                st.success(f"✅ Calibration: 1 pixel = {cal_factor:.4f} {unit}")
                st.session_state.pending_points = []
                st.rerun()
        
        calibration_dialog()

def add_product_info(measurement: Dict):
    """Ajoute les informations du produit sélectionné"""
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
            measurement['color'] = product_data.get('color', measurement['color'])

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