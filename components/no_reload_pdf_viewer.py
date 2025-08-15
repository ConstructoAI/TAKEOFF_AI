import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import math
from typing import List, Dict, Optional, Tuple
import streamlit.components.v1 as components
import hashlib
import json

def NoReloadPDFViewer(pdf_processor, current_page: int, measurements: List[Dict],
                      selected_tool: str, calibration: Dict, detected_lines: Optional[List[Dict]] = None):
    """Visualiseur PDF sans rechargement pendant le dessin"""
    
    # Initialiser l'état persistant
    if 'pdf_state' not in st.session_state:
        st.session_state.pdf_state = {
            'pending_points': [],
            'last_tool': selected_tool,
            'last_page': current_page,
            'click_count': 0,
            'image_hash': None,
            'base_zoom': 1.0,
            'calibration_zoom': 1.0,
            'last_coordinates': None,
            'force_redraw': False
        }
    
    # Réinitialiser si changement d'outil ou de page
    if (st.session_state.pdf_state['last_tool'] != selected_tool or 
        st.session_state.pdf_state['last_page'] != current_page):
        st.session_state.pdf_state['pending_points'] = []
        st.session_state.pdf_state['last_tool'] = selected_tool
        st.session_state.pdf_state['last_page'] = current_page
        st.session_state.pdf_state['click_count'] = 0
        st.session_state.pdf_state['last_coordinates'] = None
    
    # Configuration de l'outil
    tool_configs = {
        'distance': {'points': 2, 'auto_complete': True, 'color': '#FF0000', 'name': '📏 Distance'},
        'angle': {'points': 3, 'auto_complete': True, 'color': '#FF00FF', 'name': '📐 Angle'},
        'area': {'points': 3, 'auto_complete': False, 'color': '#00FF00', 'name': '⬜ Surface'},
        'perimeter': {'points': 3, 'auto_complete': False, 'color': '#0000FF', 'name': '🔲 Périmètre'},
        'calibration': {'points': 2, 'auto_complete': True, 'color': '#FFA500', 'name': '🎯 Calibration'}
    }
    
    config = tool_configs.get(selected_tool, {})
    
    # Interface compacte
    col1, col2, col3 = st.columns([6, 1, 1])
    
    with col1:
        st.markdown(f"**{config.get('name', selected_tool)}** - {len(st.session_state.pdf_state['pending_points'])} points")
        if selected_tool in ['area', 'perimeter']:
            st.caption("💡 Cliquez pour placer des points • **Enter** pour fermer")
        else:
            st.caption(f"💡 Cliquez pour placer {config.get('points', 0)} points")
    
    with col2:
        # Bouton Valider
        can_validate = (
            (selected_tool in ['area', 'perimeter'] and len(st.session_state.pdf_state['pending_points']) >= 3) or
            (config.get('auto_complete') and len(st.session_state.pdf_state['pending_points']) >= config.get('points', 0))
        )
        
        if can_validate:
            if st.button("✅", key="validate_measurement", help="Valider la mesure"):
                process_measurement(
                    selected_tool,
                    st.session_state.pdf_state['pending_points'],
                    measurements,
                    current_page,
                    calibration
                )
                st.session_state.pdf_state['pending_points'] = []
                st.session_state.pdf_state['click_count'] = 0
                st.session_state.pdf_state['last_coordinates'] = None
                st.rerun()
    
    with col3:
        # Bouton Effacer
        if st.button("🔄", key="clear_measurement", help="Effacer les points"):
            st.session_state.pdf_state['pending_points'] = []
            st.session_state.pdf_state['click_count'] = 0
            st.session_state.pdf_state['last_coordinates'] = None
            st.rerun()
    
    # Zoom avec raccourcis
    zoom_col1, zoom_col2, zoom_col3, zoom_col4 = st.columns([1, 1, 4, 1])
    
    with zoom_col1:
        if st.button("➖", key="zoom_out", help="Dézoomer (Alt+-)"):
            current_zoom = st.session_state.get('zoom_level', 1.5)
            st.session_state.zoom_level = max(0.5, current_zoom - 0.2)
            st.rerun()
    
    with zoom_col2:
        if st.button("🎯", key="zoom_reset", help="Réinitialiser (Alt+0)"):
            st.session_state.zoom_level = 1.0
            st.rerun()
    
    with zoom_col3:
        zoom_level = st.slider(
            "🔍 Zoom",
            min_value=0.5,
            max_value=3.0,
            value=st.session_state.get('zoom_level', 1.5),
            step=0.1,
            key='zoom_optimized',
            label_visibility="collapsed"
        )
        st.session_state.zoom_level = zoom_level
    
    with zoom_col4:
        if st.button("➕", key="zoom_in", help="Zoomer (Alt++)"): 
            current_zoom = st.session_state.get('zoom_level', 1.5)
            st.session_state.zoom_level = min(3.0, current_zoom + 0.2)
            st.rerun()
    
    # Afficher le niveau de zoom et l'échelle réelle
    zoom_info = st.columns([1, 1, 1])
    with zoom_info[0]:
        st.caption(f"🔍 Zoom: {zoom_level:.0%}")
    with zoom_info[1]:
        # Calculer l'échelle réelle avec le zoom
        adjusted_cal = calibration.get('value', 1.0)
        if 'calibration_zoom' in st.session_state.pdf_state:
            # Ajuster la calibration en fonction du changement de zoom
            zoom_ratio = zoom_level / st.session_state.pdf_state['calibration_zoom']
            adjusted_cal = calibration.get('value', 1.0) / zoom_ratio
        st.caption(f"📏 Échelle: 1px = {adjusted_cal:.3f} {calibration.get('unit', 'cm')}")
    with zoom_info[2]:
        st.caption(f"⌨️ Alt+/- pour zoomer")
    
    # Obtenir l'image de base
    page_image = pdf_processor.get_page_image(current_page, zoom=zoom_level)
    
    if not page_image:
        st.error("Impossible de charger la page PDF")
        return
    
    # Dessiner l'image complète
    display_image = draw_complete_image(
        page_image, measurements, current_page,
        st.session_state.pdf_state['pending_points'],
        config.get('color', '#000000'),
        selected_tool, detected_lines
    )
    
    # Container principal avec placeholder pour mise à jour dynamique
    main_container = st.container()
    
    with main_container:
        # Créer une clé unique stable
        unique_key = f"pdf_{current_page}_{selected_tool}"
        
        # Placeholder pour l'image
        img_placeholder = st.empty()
        
        with img_placeholder.container():
            # Image cliquable
            coordinates = streamlit_image_coordinates(
                display_image,
                key=unique_key
            )
            
            # Traiter le clic sans rerun
            if coordinates is not None and coordinates != st.session_state.pdf_state['last_coordinates']:
                st.session_state.pdf_state['last_coordinates'] = coordinates
                x, y = coordinates["x"], coordinates["y"]
                
                # Vérifier si c'est un nouveau clic
                is_new_click = True
                for p in st.session_state.pdf_state['pending_points']:
                    if abs(p[0] - x) < 10 and abs(p[1] - y) < 10:
                        is_new_click = False
                        break
                
                if is_new_click:
                    # Accrochage
                    if st.session_state.snap_enabled and detected_lines:
                        snap_point = find_snap_point((x, y), detected_lines, st.session_state.snap_threshold)
                        if snap_point:
                            x, y = snap_point
                    
                    # Ajouter le point sans rerun
                    st.session_state.pdf_state['pending_points'].append((x, y))
                    st.session_state.pdf_state['click_count'] += 1
                    
                    # Auto-complétion
                    if config.get('auto_complete') and len(st.session_state.pdf_state['pending_points']) >= config.get('points', 0):
                        process_measurement(
                            selected_tool,
                            st.session_state.pdf_state['pending_points'],
                            measurements,
                            current_page,
                            calibration
                        )
                        st.session_state.pdf_state['pending_points'] = []
                        st.session_state.pdf_state['click_count'] = 0
                        st.session_state.pdf_state['last_coordinates'] = None
                        st.rerun()
                    else:
                        # Redessiner l'image avec le nouveau point
                        new_display_image = draw_complete_image(
                            page_image, measurements, current_page,
                            st.session_state.pdf_state['pending_points'],
                            config.get('color', '#000000'),
                            selected_tool, detected_lines
                        )
                        # Mettre à jour l'image sans rerun
                        img_placeholder.empty()
                        with img_placeholder.container():
                            streamlit_image_coordinates(
                                new_display_image,
                                key=f"{unique_key}_update_{st.session_state.pdf_state['click_count']}"
                            )
    
    # JavaScript pour capturer Enter et mettre à jour dynamiquement
    if selected_tool in ['area', 'perimeter'] and len(st.session_state.pdf_state['pending_points']) >= 3:
        enter_js = """
        <script>
        (function() {
            // Fonction pour gérer Enter
            const handleEnter = function(event) {
                if (event.key === 'Enter' && !event.shiftKey && !event.ctrlKey && !event.altKey) {
                    event.preventDefault();
                    event.stopPropagation();
                    
                    // Trouver et cliquer le bouton de validation
                    const validateButton = window.parent.document.querySelector('button[aria-label="Valider la mesure"]');
                    if (!validateButton) {
                        // Fallback: chercher par texte
                        const buttons = window.parent.document.querySelectorAll('button');
                        for (let btn of buttons) {
                            if (btn.textContent.trim() === '✅') {
                                btn.click();
                                return;
                            }
                        }
                    } else {
                        validateButton.click();
                    }
                }
            };
            
            // Supprimer les anciens listeners
            if (window.enterHandler) {
                window.parent.document.removeEventListener('keydown', window.enterHandler);
            }
            
            // Ajouter le nouveau listener
            window.enterHandler = handleEnter;
            window.parent.document.addEventListener('keydown', handleEnter);
            
            // Ajouter aussi sur l'iframe
            document.addEventListener('keydown', handleEnter);
        })();
        </script>
        """
        
        components.html(enter_js, height=0)
    
    # JavaScript pour les raccourcis clavier de zoom
    zoom_shortcuts_js = """
    <script>
    (function() {
        const handleZoomShortcuts = function(event) {
            // Alt + Plus pour zoomer
            if (event.altKey && (event.key === '+' || event.key === '=')) {
                event.preventDefault();
                const zoomInBtn = window.parent.document.querySelector('button[key="zoom_in"]');
                if (!zoomInBtn) {
                    // Fallback: chercher par texte
                    const buttons = window.parent.document.querySelectorAll('button');
                    for (let btn of buttons) {
                        if (btn.textContent.trim() === '➕') {
                            btn.click();
                            return;
                        }
                    }
                } else {
                    zoomInBtn.click();
                }
            }
            // Alt + Minus pour dézoomer
            else if (event.altKey && event.key === '-') {
                event.preventDefault();
                const zoomOutBtn = window.parent.document.querySelector('button[key="zoom_out"]');
                if (!zoomOutBtn) {
                    // Fallback: chercher par texte
                    const buttons = window.parent.document.querySelectorAll('button');
                    for (let btn of buttons) {
                        if (btn.textContent.trim() === '➖') {
                            btn.click();
                            return;
                        }
                    }
                } else {
                    zoomOutBtn.click();
                }
            }
            // Alt + 0 pour réinitialiser le zoom
            else if (event.altKey && event.key === '0') {
                event.preventDefault();
                const zoomResetBtn = window.parent.document.querySelector('button[key="zoom_reset"]');
                if (!zoomResetBtn) {
                    // Fallback: chercher par texte
                    const buttons = window.parent.document.querySelectorAll('button');
                    for (let btn of buttons) {
                        if (btn.textContent.trim() === '🎯') {
                            btn.click();
                            return;
                        }
                    }
                } else {
                    zoomResetBtn.click();
                }
            }
        };
        
        // Ajouter les listeners
        if (window.zoomHandler) {
            window.parent.document.removeEventListener('keydown', window.zoomHandler);
        }
        window.zoomHandler = handleZoomShortcuts;
        window.parent.document.addEventListener('keydown', handleZoomShortcuts);
    })();
    </script>
    """
    
    components.html(zoom_shortcuts_js, height=0)

def process_measurement(tool: str, points: List[Tuple], measurements: List[Dict],
                       current_page: int, calibration: Dict):
    """Traite et stocke la mesure"""
    measurement = None
    
    # Ajuster la calibration selon le zoom actuel
    zoom_level = st.session_state.get('zoom_level', 1.0)
    calibration_zoom = st.session_state.pdf_state.get('calibration_zoom', 1.0)
    zoom_ratio = zoom_level / calibration_zoom if calibration_zoom != 0 else 1.0
    adjusted_calibration = calibration.get('value', 1.0) / zoom_ratio
    
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
            'zoom_level': st.session_state.get('zoom_level', 1.0)
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
            'zoom_level': st.session_state.get('zoom_level', 1.0)
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
            'zoom_level': st.session_state.get('zoom_level', 1.0)
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
            'zoom_level': st.session_state.get('zoom_level', 1.0)
        }
    
    elif tool == 'calibration' and len(points) >= 2:
        pixel_dist = math.sqrt((points[1][0] - points[0][0])**2 + 
                              (points[1][1] - points[0][1])**2)
        st.session_state.calibration_distance = pixel_dist
        st.session_state.show_calibration_dialog = True
        # Stocker le zoom actuel pour la calibration
        st.session_state.pdf_state['calibration_zoom'] = st.session_state.get('zoom_level', 1.0)
        return
    
    if measurement:
        measurements.append(measurement)
        st.session_state.temp_measurement = measurement
        st.session_state.temp_measurement_index = len(measurements) - 1
        st.success(f"✅ {measurement['label']}: {measurement['value']:.2f} {measurement['unit']}")

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
            
            # Fond blanc
            draw.ellipse([x-size-2, y-size-2, x+size+2, y+size+2], 
                        fill='white', outline='white')
            # Point coloré
            draw.ellipse([x-size, y-size, x+size, y+size], 
                        fill=color_rgba, outline='black', width=2)
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
    
    # Ajuster les points selon le zoom actuel
    current_zoom = st.session_state.get('zoom_level', 1.0)
    measurement_zoom = measurement.get('zoom_level', 1.0)
    zoom_ratio = current_zoom / measurement_zoom
    
    # Recalculer les points avec le nouveau zoom
    adjusted_points = []
    for p in points:
        adjusted_points.append((p[0] * zoom_ratio, p[1] * zoom_ratio))
    
    color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    color_rgba = color_rgb + (200,)
    
    if m_type == 'distance' and len(adjusted_points) >= 2:
        draw.line([tuple(adjusted_points[0]), tuple(adjusted_points[1])], fill=color_rgba, width=4)
        
        for p in adjusted_points:
            x, y = p
            draw.ellipse([x-6, y-6, x+6, y+6], fill=color_rgba, outline='white', width=2)
        
        if measurement.get('label') and measurement.get('value') is not None:
            mid_x = (adjusted_points[0][0] + adjusted_points[1][0]) / 2
            mid_y = (adjusted_points[0][1] + adjusted_points[1][1]) / 2
            label = f"{measurement['label']}: {measurement['value']:.2f} {measurement.get('unit', '')}"
            product = measurement.get('product', {})
            if product.get('name'):
                label += f" [{product['name']}]"
            draw_label(draw, (mid_x, mid_y), label)
    
    elif m_type in ['area', 'perimeter'] and len(adjusted_points) >= 3:
        if m_type == 'area':
            draw.polygon([tuple(p) for p in adjusted_points], fill=color_rgba[:3] + (50,))
        
        for i in range(len(adjusted_points)):
            next_i = (i + 1) % len(adjusted_points)
            draw.line([tuple(adjusted_points[i]), tuple(adjusted_points[next_i])], fill=color_rgba, width=3)
        
        for p in adjusted_points:
            x, y = p
            draw.ellipse([x-5, y-5, x+5, y+5], fill=color_rgba, outline='white')
        
        if measurement.get('label') and measurement.get('value') is not None:
            center_x = sum(p[0] for p in adjusted_points) / len(adjusted_points)
            center_y = sum(p[1] for p in adjusted_points) / len(adjusted_points)
            
            unit = measurement.get('unit', '')
            label = f"{measurement['label']}: {measurement['value']:.2f} {unit}"
            product = measurement.get('product', {})
            if product.get('name'):
                label += f"\n[{product['name']}]"
            
            draw_label(draw, (center_x, center_y), label)
    
    elif m_type == 'angle' and len(adjusted_points) >= 3:
        draw.line([tuple(adjusted_points[0]), tuple(adjusted_points[1])], fill=color_rgba, width=3)
        draw.line([tuple(adjusted_points[1]), tuple(adjusted_points[2])], fill=color_rgba, width=3)
        
        draw_angle_arc(draw, adjusted_points[0], adjusted_points[1], adjusted_points[2], color_rgba)
        
        for i, p in enumerate(adjusted_points):
            x, y = p
            size = 8 if i == 1 else 6
            draw.ellipse([x-size, y-size, x+size, y+size], fill=color_rgba, outline='white')
        
        if measurement.get('value') is not None:
            label = f"{measurement.get('label', 'Angle')}: {measurement['value']:.1f}°"
            draw_label(draw, adjusted_points[1], label, offset=(20, -20))

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
    
    # Fond noir
    draw.rectangle(
        [x-max_width//2-padding-1, y-padding-1, 
         x+max_width//2+padding+1, y+total_height+padding+1],
        fill='black'
    )
    # Fond blanc
    draw.rectangle(
        [x-max_width//2-padding, y-padding, 
         x+max_width//2+padding, y+total_height+padding],
        fill=(255, 255, 255, 240)
    )
    
    # Texte
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
        # Points de fin
        for point in [line['start'], line['end']]:
            dist = math.sqrt((cursor[0] - point[0])**2 + (cursor[1] - point[1])**2)
            if dist < min_dist:
                min_dist = dist
                snap_point = tuple(point)
        
        # Point milieu
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