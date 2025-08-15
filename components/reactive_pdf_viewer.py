import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import math
from typing import List, Dict, Optional, Tuple
import time
import streamlit.components.v1 as components

def ReactivePDFViewer(pdf_processor, current_page: int, measurements: List[Dict],
                      selected_tool: str, calibration: Dict, detected_lines: Optional[List[Dict]] = None):
    """Visualiseur PDF réactif sans rechargements"""
    
    # Initialiser l'état
    if 'pending_points' not in st.session_state:
        st.session_state.pending_points = []
    if 'force_refresh' not in st.session_state:
        st.session_state.force_refresh = 0
    if 'last_click' not in st.session_state:
        st.session_state.last_click = None
    if 'process_measurement' not in st.session_state:
        st.session_state.process_measurement = False
    
    # Configuration de l'outil
    tool_configs = {
        'distance': {'points': 2, 'auto_complete': True, 'color': '#FF0000', 'name': '📏 Distance'},
        'angle': {'points': 3, 'auto_complete': True, 'color': '#FF00FF', 'name': '📐 Angle'},
        'area': {'points': 3, 'auto_complete': False, 'color': '#00FF00', 'name': '⬜ Surface'},
        'perimeter': {'points': 3, 'auto_complete': False, 'color': '#0000FF', 'name': '🔲 Périmètre'},
        'calibration': {'points': 2, 'auto_complete': True, 'color': '#FFA500', 'name': '🎯 Calibration'}
    }
    
    config = tool_configs.get(selected_tool, {})
    
    # Contrôle du zoom en dehors du conteneur principal
    zoom_level = st.slider(
        "🔍 Zoom",
        min_value=0.5,
        max_value=3.0,
        value=st.session_state.get('zoom_level', 1.5),
        step=0.1,
        key='zoom_reactive',
        label_visibility="collapsed"
    )
    st.session_state.zoom_level = zoom_level
    
    # Interface utilisateur minimale
    st.markdown(f"### {config.get('name', selected_tool)} - {len(st.session_state.pending_points)} points")
    
    # Instructions selon l'outil
    if selected_tool in ['area', 'perimeter']:
        st.caption("💡 Cliquez pour placer des points • **Enter** pour fermer la forme")
    else:
        points_needed = config.get('points', 0)
        st.caption(f"💡 Cliquez pour placer {points_needed} points")
    
    # Conteneur principal avec cache
    @st.cache_data
    def get_base_image(page: int, zoom: float, measurements_count: int):
        """Cache l'image de base avec les mesures"""
        img = pdf_processor.get_page_image(page, zoom=zoom)
        if img:
            return draw_base_image(img, measurements, page, detected_lines)
        return None
    
    # Obtenir l'image de base
    base_image = get_base_image(current_page, zoom_level, len(measurements))
    
    if not base_image:
        st.error("Impossible de charger la page PDF")
        return
    
    # Ajouter les points en cours
    display_image = base_image.copy()
    if st.session_state.pending_points:
        draw_pending_points(display_image, st.session_state.pending_points, 
                           config.get('color', '#000000'), selected_tool)
    
    # Container pour l'image
    image_container = st.container()
    
    with image_container:
        # Image cliquable avec gestion optimisée
        click_value = streamlit_image_coordinates(
            display_image,
            key=f"pdf_{current_page}_{selected_tool}_{st.session_state.force_refresh}"
        )
        
        # Traiter le clic uniquement si c'est nouveau
        if click_value and click_value != st.session_state.last_click:
            st.session_state.last_click = click_value
            x, y = click_value["x"], click_value["y"]
            
            # Vérifier que ce n'est pas trop proche d'un point existant
            is_new = True
            for p in st.session_state.pending_points:
                if abs(p[0] - x) < 15 and abs(p[1] - y) < 15:
                    is_new = False
                    break
            
            if is_new:
                # Accrochage aux lignes
                if st.session_state.snap_enabled and detected_lines:
                    snap_point = find_snap_point((x, y), detected_lines, st.session_state.snap_threshold)
                    if snap_point:
                        x, y = snap_point
                
                # Ajouter le point
                st.session_state.pending_points.append((x, y))
                st.session_state.force_refresh += 1
                
                # Vérifier l'auto-complétion
                if config.get('auto_complete') and len(st.session_state.pending_points) >= config.get('points', 0):
                    st.session_state.process_measurement = True
                
                st.rerun()
    
    # Boutons d'action dans une ligne séparée
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        can_validate = (
            (selected_tool in ['area', 'perimeter'] and len(st.session_state.pending_points) >= 3) or
            (config.get('auto_complete') and len(st.session_state.pending_points) >= config.get('points', 0))
        )
        
        if can_validate:
            if st.button("✅ Valider", type="primary", key=f"validate_btn"):
                st.session_state.process_measurement = True
                st.rerun()
    
    with col3:
        if st.button("🔄 Effacer", key=f"clear_btn"):
            st.session_state.pending_points = []
            st.session_state.force_refresh += 1
            st.session_state.last_click = None
            st.rerun()
    
    # Gestion spéciale pour Enter sur area/perimeter
    if selected_tool in ['area', 'perimeter'] and len(st.session_state.pending_points) >= 3:
        # JavaScript pour capturer Enter sans formulaire
        enter_script = f"""
        <script>
        (function() {{
            let enterHandler = function(e) {{
                if (e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.altKey) {{
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Chercher et cliquer le bouton Valider
                    const buttons = window.parent.document.querySelectorAll('button');
                    for (let btn of buttons) {{
                        if (btn.textContent.includes('✅ Valider')) {{
                            btn.click();
                            return;
                        }}
                    }}
                }}
            }};
            
            // Nettoyer les anciens handlers
            window.parent.document.removeEventListener('keydown', window.enterHandler);
            window.enterHandler = enterHandler;
            window.parent.document.addEventListener('keydown', enterHandler);
        }})();
        </script>
        """
        
        components.html(enter_script, height=0)
    
    # Traiter la mesure si nécessaire
    if st.session_state.process_measurement and st.session_state.pending_points:
        create_and_store_measurement(
            selected_tool, 
            st.session_state.pending_points,
            measurements,
            current_page,
            calibration
        )
        st.session_state.pending_points = []
        st.session_state.force_refresh += 1
        st.session_state.process_measurement = False
        st.session_state.last_click = None
        st.rerun()

def draw_base_image(img: Image.Image, measurements: List[Dict], 
                    page: int, detected_lines: Optional[List[Dict]]) -> Image.Image:
    """Dessine l'image de base avec les mesures existantes"""
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Lignes détectées
    if detected_lines and st.session_state.get('show_detected_lines', False):
        for line in detected_lines:
            start = tuple(map(int, line['start']))
            end = tuple(map(int, line['end']))
            draw.line([start, end], fill=(200, 200, 200, 100), width=1)
    
    # Mesures existantes
    for measurement in measurements:
        if measurement.get('page') == page:
            draw_measurement(draw, measurement)
    
    return img

def draw_pending_points(img: Image.Image, points: List[Tuple], 
                       color: str, tool: str):
    """Dessine les points en cours sur l'image"""
    if not points:
        return
    
    draw = ImageDraw.Draw(img, 'RGBA')
    color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    color_rgba = color_rgb + (180,)
    
    # Lignes
    if len(points) > 1:
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=color_rgba, width=3)
        
        # Ligne de fermeture pour polygones
        if tool in ['area', 'perimeter'] and len(points) >= 3:
            draw_dashed_line(draw, points[-1], points[0], color_rgba)
    
    # Points
    for i, point in enumerate(points):
        x, y = point
        size = 10 if tool == 'angle' and i == 1 else 8
        
        # Fond blanc
        draw.ellipse([x-size-2, y-size-2, x+size+2, y+size+2], 
                    fill='white', outline='white')
        # Point coloré
        draw.ellipse([x-size, y-size, x+size, y+size], 
                    fill=color_rgba, outline='black', width=2)
        # Numéro
        draw.text((x+size+5, y-size), str(i+1), fill='black')

def create_and_store_measurement(tool: str, points: List[Tuple], measurements: List[Dict],
                                current_page: int, calibration: Dict):
    """Crée et stocke la mesure"""
    measurement = None
    
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
    
    elif tool == 'calibration' and len(points) >= 2:
        pixel_dist = math.sqrt((points[1][0] - points[0][0])**2 + 
                              (points[1][1] - points[0][1])**2)
        
        # Stocker pour le dialogue
        st.session_state.calibration_distance = pixel_dist
        st.session_state.show_calibration_dialog = True
        return
    
    if measurement:
        measurements.append(measurement)
        st.session_state.temp_measurement = measurement
        st.session_state.temp_measurement_index = len(measurements) - 1
        st.success(f"✅ {measurement['label']}: {measurement['value']:.2f} {measurement['unit']}")

# Fonctions utilitaires (identiques aux versions précédentes)
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