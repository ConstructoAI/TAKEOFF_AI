import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import math
from typing import List, Dict, Optional, Tuple
import time

def FastPDFViewer(pdf_processor, current_page: int, measurements: List[Dict],
                  selected_tool: str, calibration: Dict, detected_lines: Optional[List[Dict]] = None):
    """Visualiseur PDF ultra-rapide sans rechargements"""
    
    # Initialiser l'état
    if 'pending_points' not in st.session_state:
        st.session_state.pending_points = []
    if 'viewer_id' not in st.session_state:
        st.session_state.viewer_id = 0
    if 'enter_pressed' not in st.session_state:
        st.session_state.enter_pressed = False
    
    # Contrôle du zoom
    zoom_level = st.slider(
        "🔍 Zoom",
        min_value=0.5,
        max_value=3.0,
        value=st.session_state.get('zoom_level', 1.5),
        step=0.1,
        key='zoom_fast'
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
    
    # Interface utilisateur compacte
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.markdown(f"### {config.get('name', selected_tool)} - {len(st.session_state.pending_points)} points")
    
    with col2:
        button_col = st.columns(2)
        with button_col[0]:
            # Validation
            can_validate = (
                (selected_tool in ['area', 'perimeter'] and len(st.session_state.pending_points) >= 3) or
                (config.get('auto_complete') and len(st.session_state.pending_points) >= config.get('points', 0))
            )
            
            if can_validate:
                if st.button("✅", key=f"val{st.session_state.viewer_id}"):
                    finalize_measurement(selected_tool, st.session_state.pending_points, 
                                       measurements, current_page, calibration)
        
        with button_col[1]:
            if st.button("🔄", key=f"clr{st.session_state.viewer_id}"):
                st.session_state.pending_points = []
                st.session_state.viewer_id += 1
                st.rerun()
    
    # Instructions courtes
    instructions = {
        'distance': "2 points",
        'angle': "3 points (sommet au milieu)",
        'area': "3+ points • Enter pour fermer",
        'perimeter': "3+ points • Enter pour fermer",
        'calibration': "2 points"
    }
    
    st.caption(f"💡 {instructions.get(selected_tool, '')}")
    
    # Container principal pour éviter les rechargements
    main_container = st.container()
    
    with main_container:
        # Préparer l'image complète
        display_image = draw_complete_image(
            page_image, measurements, current_page,
            st.session_state.pending_points, config.get('color', '#000000'),
            selected_tool, detected_lines
        )
        
        # Utiliser un placeholder pour l'image
        img_placeholder = st.empty()
        
        with img_placeholder.container():
            # Image cliquable avec clé stable
            value = streamlit_image_coordinates(
                display_image,
                key=f"img_{current_page}_{selected_tool}_{st.session_state.viewer_id}"
            )
            
            # Gérer le clic
            if value is not None:
                handle_click(value, config, measurements, current_page, calibration, 
                           selected_tool, detected_lines)
    
    # Gestion de la touche Enter pour area/perimeter
    if selected_tool in ['area', 'perimeter'] and len(st.session_state.pending_points) >= 3:
        # Créer un conteneur invisible avec JavaScript
        enter_js = """
        <script>
        var checkEnter = function(e) {
            if (e.keyCode === 13) {
                // Simuler un clic sur le bouton de validation
                var buttons = window.parent.document.querySelectorAll('button');
                for (var i = 0; i < buttons.length; i++) {
                    if (buttons[i].innerText === '✅') {
                        buttons[i].click();
                        break;
                    }
                }
            }
        };
        document.removeEventListener('keydown', checkEnter);
        document.addEventListener('keydown', checkEnter);
        window.parent.document.removeEventListener('keydown', checkEnter);
        window.parent.document.addEventListener('keydown', checkEnter);
        </script>
        """
        st.components.v1.html(enter_js, height=0)

def handle_click(value: Dict, config: Dict, measurements: List[Dict], 
                 current_page: int, calibration: Dict, selected_tool: str,
                 detected_lines: Optional[List[Dict]]):
    """Gère les clics sans rechargement"""
    x, y = value["x"], value["y"]
    
    # Vérifier que ce n'est pas un doublon
    for p in st.session_state.pending_points:
        if abs(p[0] - x) < 10 and abs(p[1] - y) < 10:
            return
    
    # Appliquer l'accrochage
    if st.session_state.snap_enabled and detected_lines:
        snap_point = find_snap_point((x, y), detected_lines, st.session_state.snap_threshold)
        if snap_point:
            x, y = snap_point
    
    # Ajouter le point
    st.session_state.pending_points.append((x, y))
    st.session_state.viewer_id += 1
    
    # Auto-complétion
    if config.get('auto_complete') and len(st.session_state.pending_points) >= config.get('points', 0):
        finalize_measurement(selected_tool, st.session_state.pending_points, 
                           measurements, current_page, calibration)
    else:
        st.rerun()

def finalize_measurement(tool: str, points: List[Tuple], measurements: List[Dict],
                        current_page: int, calibration: Dict):
    """Finalise la mesure et affiche le dialogue produit"""
    if not points:
        return
    
    # Créer la mesure
    measurement = create_measurement_object(tool, points, measurements, current_page, calibration)
    
    if measurement:
        measurements.append(measurement)
        st.session_state.pending_points = []
        st.session_state.viewer_id += 1
        
        # Stocker temporairement pour le dialogue
        st.session_state.temp_measurement = measurement
        st.session_state.temp_measurement_index = len(measurements) - 1
        
        st.success(f"✅ {measurement['label']}: {measurement['value']:.2f} {measurement['unit']}")
        st.rerun()

def create_measurement_object(tool: str, points: List[Tuple], measurements: List[Dict],
                             current_page: int, calibration: Dict) -> Optional[Dict]:
    """Crée l'objet mesure selon l'outil"""
    if tool == 'distance' and len(points) >= 2:
        pixel_dist = math.sqrt((points[1][0] - points[0][0])**2 + 
                              (points[1][1] - points[0][1])**2)
        return {
            'type': 'distance',
            'points': points[:2],
            'page': current_page,
            'value': pixel_dist * calibration.get('value', 1.0),
            'unit': calibration.get('unit', 'cm'),
            'label': f"Distance_{len([m for m in measurements if m['type'] == 'distance']) + 1}",
            'color': '#FF0000'
        }
    
    elif tool == 'area' and len(points) >= 3:
        area = calculate_polygon_area(points)
        cal_value = calibration.get('value', 1.0)
        return {
            'type': 'area',
            'points': points,
            'page': current_page,
            'value': area * cal_value * cal_value,
            'unit': f"{calibration.get('unit', 'cm')}²",
            'label': f"Surface_{len([m for m in measurements if m['type'] == 'area']) + 1}",
            'color': '#00FF00'
        }
    
    elif tool == 'perimeter' and len(points) >= 3:
        perim = calculate_perimeter(points)
        return {
            'type': 'perimeter',
            'points': points,
            'page': current_page,
            'value': perim * calibration.get('value', 1.0),
            'unit': calibration.get('unit', 'cm'),
            'label': f"Périmètre_{len([m for m in measurements if m['type'] == 'perimeter']) + 1}",
            'color': '#0000FF'
        }
    
    elif tool == 'angle' and len(points) >= 3:
        angle = calculate_angle(points[0], points[1], points[2])
        return {
            'type': 'angle',
            'points': points[:3],
            'page': current_page,
            'value': angle,
            'unit': '°',
            'label': f"Angle_{len([m for m in measurements if m['type'] == 'angle']) + 1}",
            'color': '#FF00FF'
        }
    
    elif tool == 'calibration' and len(points) >= 2:
        pixel_dist = math.sqrt((points[1][0] - points[0][0])**2 + 
                              (points[1][1] - points[0][1])**2)
        
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
                st.rerun()
        
        calibration_dialog()
        return None
    
    return None

def draw_complete_image(base_image: Image.Image, measurements: List[Dict], current_page: int,
                       pending_points: List[Tuple], tool_color: str, tool: str,
                       detected_lines: Optional[List[Dict]]) -> Image.Image:
    """Dessine l'image complète avec toutes les annotations"""
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
        
        # Lignes
        if len(pending_points) > 1:
            for i in range(len(pending_points) - 1):
                draw.line([pending_points[i], pending_points[i+1]], fill=color_rgba, width=3)
            
            # Ligne de fermeture
            if tool in ['area', 'perimeter'] and len(pending_points) >= 3:
                draw_dashed_line(draw, pending_points[-1], pending_points[0], color_rgba)
        
        # Points
        for i, point in enumerate(pending_points):
            x, y = point
            size = 10 if tool == 'angle' and i == 1 else 8
            
            draw.ellipse([x-size-2, y-size-2, x+size+2, y+size+2], 
                        fill='white', outline='white')
            draw.ellipse([x-size, y-size, x+size, y+size], 
                        fill=color_rgba, outline='black', width=2)
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
        draw.line([tuple(points[0]), tuple(points[1])], fill=color_rgba, width=4)
        
        for p in points:
            x, y = p
            draw.ellipse([x-6, y-6, x+6, y+6], fill=color_rgba, outline='white', width=2)
        
        if measurement.get('label') and measurement.get('value') is not None:
            mid_x = (points[0][0] + points[1][0]) / 2
            mid_y = (points[0][1] + points[1][1]) / 2
            label = f"{measurement['label']}: {measurement['value']:.2f} {measurement.get('unit', '')}"
            product = measurement.get('product', {})
            if product.get('name'):
                label += f" [{product['name']}]"
            draw_label(draw, (mid_x, mid_y), label)
    
    elif m_type in ['area', 'perimeter'] and len(points) >= 3:
        if m_type == 'area':
            draw.polygon([tuple(p) for p in points], fill=color_rgba[:3] + (50,))
        
        for i in range(len(points)):
            next_i = (i + 1) % len(points)
            draw.line([tuple(points[i]), tuple(points[next_i])], fill=color_rgba, width=3)
        
        for p in points:
            x, y = p
            draw.ellipse([x-5, y-5, x+5, y+5], fill=color_rgba, outline='white')
        
        if measurement.get('label') and measurement.get('value') is not None:
            center_x = sum(p[0] for p in points) / len(points)
            center_y = sum(p[1] for p in points) / len(points)
            
            unit = measurement.get('unit', '')
            label = f"{measurement['label']}: {measurement['value']:.2f} {unit}"
            product = measurement.get('product', {})
            if product.get('name'):
                label += f"\n[{product['name']}]"
            
            draw_label(draw, (center_x, center_y), label)
    
    elif m_type == 'angle' and len(points) >= 3:
        draw.line([tuple(points[0]), tuple(points[1])], fill=color_rgba, width=3)
        draw.line([tuple(points[1]), tuple(points[2])], fill=color_rgba, width=3)
        
        draw_angle_arc(draw, points[0], points[1], points[2], color_rgba)
        
        for i, p in enumerate(points):
            x, y = p
            size = 8 if i == 1 else 6
            draw.ellipse([x-size, y-size, x+size, y+size], fill=color_rgba, outline='white')
        
        if measurement.get('value') is not None:
            label = f"{measurement.get('label', 'Angle')}: {measurement['value']:.1f}°"
            draw_label(draw, points[1], label, offset=(20, -20))

def draw_label(draw: ImageDraw.Draw, position: Tuple[float, float], text: str, 
              offset: Tuple[int, int] = (0, 0)):
    """Dessine un label avec fond"""
    x, y = position
    x += offset[0]
    y += offset[1]
    
    lines = text.split('\n')
    line_height = 20
    
    max_width = 0
    total_height = len(lines) * line_height
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line)
        line_width = bbox[2] - bbox[0]
        max_width = max(max_width, line_width)
    
    padding = 6
    
    draw.rectangle(
        [x-max_width//2-padding-1, y-padding-1, 
         x+max_width//2+padding+1, y+total_height+padding+1],
        fill='black'
    )
    draw.rectangle(
        [x-max_width//2-padding, y-padding, 
         x+max_width//2+padding, y+total_height+padding],
        fill=(255, 255, 255, 240)
    )
    
    for i, line in enumerate(lines):
        line_y = y + i * line_height
        bbox = draw.textbbox((x, line_y), line)
        line_width = bbox[2] - bbox[0]
        draw.text((x - line_width//2, line_y), line, fill='black')

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
    angle1 = math.degrees(math.atan2(p1[1] - p2[1], p1[0] - p2[0]))
    angle2 = math.degrees(math.atan2(p3[1] - p2[1], p3[0] - p2[0]))
    
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
        for point in [line['start'], line['end']]:
            dist = math.sqrt((cursor[0] - point[0])**2 + (cursor[1] - point[1])**2)
            if dist < min_dist:
                min_dist = dist
                snap_point = tuple(point)
        
        mid = ((line['start'][0] + line['end'][0]) / 2,
               (line['start'][1] + line['end'][1]) / 2)
        dist = math.sqrt((cursor[0] - mid[0])**2 + (cursor[1] - mid[1])**2)
        if dist < min_dist:
            min_dist = dist
            snap_point = mid
    
    return snap_point

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