import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import math
from typing import List, Dict, Optional, Tuple
import streamlit.components.v1 as components
import time
import base64
from io import BytesIO

def UltraFastPDFViewer(pdf_processor, current_page: int, measurements: List[Dict],
                       selected_tool: str, calibration: Dict, detected_lines: Optional[List[Dict]] = None):
    """Visualiseur PDF ultra-rapide sans aucun rechargement"""
    
    # Initialiser l'état persistant
    if 'pdf_ultra_state' not in st.session_state:
        st.session_state.pdf_ultra_state = {
            'pending_points': [],
            'last_tool': selected_tool,
            'last_page': current_page,
            'click_count': 0,
            'base_image': None,
            'base_image_key': None,
            'zoom_level': 1.5,
            'calibration_zoom': 1.0,
            'last_click_time': 0,
            'image_cache': {}
        }
    
    state = st.session_state.pdf_ultra_state
    
    # Réinitialiser si changement d'outil ou de page
    if state['last_tool'] != selected_tool or state['last_page'] != current_page:
        state['pending_points'] = []
        state['last_tool'] = selected_tool
        state['last_page'] = current_page
        state['click_count'] = 0
    
    # Configuration de l'outil
    tool_configs = {
        'distance': {'points': 2, 'auto_complete': True, 'color': '#FF0000', 'name': '📏 Distance'},
        'angle': {'points': 3, 'auto_complete': True, 'color': '#FF00FF', 'name': '📐 Angle'},
        'area': {'points': 3, 'auto_complete': False, 'color': '#00FF00', 'name': '⬜ Surface'},
        'perimeter': {'points': 3, 'auto_complete': False, 'color': '#0000FF', 'name': '🔲 Périmètre'},
        'calibration': {'points': 2, 'auto_complete': True, 'color': '#FFA500', 'name': '🎯 Calibration'}
    }
    
    config = tool_configs.get(selected_tool, {})
    
    # Interface ultra-compacte
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 1rem; padding: 0.5rem; background: #f0f0f0; border-radius: 8px;">
        <span style="font-weight: bold;">{config.get('name', selected_tool)}</span>
        <span style="color: #666;">Points: {len(state['pending_points'])}</span>
        <span style="color: #999; font-size: 0.9em;">
            {'Cliquez pour fermer le polygone • Enter pour valider' if selected_tool in ['area', 'perimeter'] else f'Cliquez {config.get("points", 0)} fois'}
        </span>
    </div>
    """, unsafe_allow_html=True)
    
    # Conteneur pour l'image avec ID fixe
    img_container = st.container()
    
    # Zone pour les contrôles (sans boutons qui causent des reloads)
    ctrl_container = st.container()
    
    with ctrl_container:
        # Zoom slider seulement (pas de boutons)
        zoom_level = st.slider(
            "🔍 Zoom",
            min_value=0.5,
            max_value=3.0,
            value=state['zoom_level'],
            step=0.1,
            key='zoom_ultra_fast',
            help="Alt+/- pour zoomer rapidement"
        )
        
        if zoom_level != state['zoom_level']:
            state['zoom_level'] = zoom_level
            state['base_image'] = None  # Force le recalcul de l'image
    
    # Générer une clé unique pour l'image de base
    image_key = f"{current_page}_{zoom_level}_{len(measurements)}"
    
    # Obtenir ou créer l'image de base
    if state['base_image_key'] != image_key or state['base_image'] is None:
        page_image = pdf_processor.get_page_image(current_page, zoom=zoom_level)
        if page_image:
            # Dessiner toutes les mesures existantes
            state['base_image'] = draw_base_image(page_image, measurements, current_page, detected_lines)
            state['base_image_key'] = image_key
    
    if state['base_image'] is None:
        st.error("Impossible de charger la page PDF")
        return
    
    # Créer l'image d'affichage avec les points en cours
    display_image = state['base_image'].copy()
    if state['pending_points']:
        draw_pending_points(display_image, state['pending_points'], config.get('color', '#000000'), selected_tool)
    
    # Convertir l'image en base64 pour éviter les rechargements
    buffered = BytesIO()
    display_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # HTML/JS personnalisé pour la gestion des clics sans rechargement
    with img_container:
        components.html(f"""
        <div id="pdf-viewer-container" style="position: relative; cursor: crosshair;">
            <img id="pdf-image" 
                 src="data:image/png;base64,{img_str}" 
                 style="max-width: 100%; height: auto; display: block;"
                 onclick="handleClick(event)">
            <canvas id="overlay-canvas" 
                    style="position: absolute; top: 0; left: 0; pointer-events: none;">
            </canvas>
        </div>
        
        <script>
        // État global
        window.pdfViewerState = window.pdfViewerState || {{
            points: {state['pending_points']},
            tool: '{selected_tool}',
            config: {str(config).replace("'", '"')},
            clickCount: {state['click_count']}
        }};
        
        const state = window.pdfViewerState;
        
        function handleClick(event) {{
            const img = event.target;
            const rect = img.getBoundingClientRect();
            const x = (event.clientX - rect.left) * (img.naturalWidth / rect.width);
            const y = (event.clientY - rect.top) * (img.naturalHeight / rect.height);
            
            // Éviter les doubles clics
            const now = Date.now();
            if (window.lastClickTime && now - window.lastClickTime < 300) return;
            window.lastClickTime = now;
            
            // Ajouter le point
            state.points.push([x, y]);
            state.clickCount++;
            
            // Redessiner
            updateCanvas();
            
            // Vérifier l'auto-complétion
            if (state.config.auto_complete && state.points.length >= state.config.points) {{
                completeAndSend();
            }}
            
            // Envoyer l'état à Streamlit
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                key: 'pdf_points_state',
                value: {{
                    points: state.points,
                    clickCount: state.clickCount,
                    complete: false
                }}
            }}, '*');
        }}
        
        function updateCanvas() {{
            const img = document.getElementById('pdf-image');
            const canvas = document.getElementById('overlay-canvas');
            const ctx = canvas.getContext('2d');
            
            // Ajuster la taille du canvas
            canvas.width = img.naturalWidth;
            canvas.height = img.naturalHeight;
            canvas.style.width = img.width + 'px';
            canvas.style.height = img.height + 'px';
            
            // Effacer
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            if (state.points.length === 0) return;
            
            // Couleur de l'outil
            const color = state.config.color || '#FF0000';
            ctx.strokeStyle = color;
            ctx.fillStyle = color + '88';
            ctx.lineWidth = 3;
            
            // Dessiner les lignes
            if (state.points.length > 1) {{
                ctx.beginPath();
                ctx.moveTo(state.points[0][0], state.points[0][1]);
                for (let i = 1; i < state.points.length; i++) {{
                    ctx.lineTo(state.points[i][0], state.points[i][1]);
                }}
                
                // Fermer pour area/perimeter
                if ((state.tool === 'area' || state.tool === 'perimeter') && 
                    state.points.length >= 3) {{
                    ctx.closePath();
                    if (state.tool === 'area') {{
                        ctx.fill();
                    }}
                }}
                ctx.stroke();
            }}
            
            // Dessiner les points
            state.points.forEach((point, i) => {{
                ctx.beginPath();
                ctx.arc(point[0], point[1], 8, 0, 2 * Math.PI);
                ctx.fillStyle = color;
                ctx.fill();
                ctx.strokeStyle = 'white';
                ctx.lineWidth = 2;
                ctx.stroke();
                
                // Numéro
                ctx.fillStyle = 'black';
                ctx.font = '14px Arial';
                ctx.fillText(i + 1, point[0] + 10, point[1] - 10);
            }});
        }}
        
        function completeAndSend() {{
            window.parent.postMessage({{
                type: 'streamlit:setComponentValue',
                key: 'pdf_points_state',
                value: {{
                    points: state.points,
                    clickCount: state.clickCount,
                    complete: true
                }}
            }}, '*');
            
            // Réinitialiser
            state.points = [];
            state.clickCount = 0;
            updateCanvas();
        }}
        
        // Raccourcis clavier
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Enter' && !event.shiftKey) {{
                if ((state.tool === 'area' || state.tool === 'perimeter') && 
                    state.points.length >= 3) {{
                    event.preventDefault();
                    completeAndSend();
                }}
            }} else if (event.key === 'Escape') {{
                event.preventDefault();
                state.points = [];
                state.clickCount = 0;
                updateCanvas();
            }} else if (event.altKey && event.key === '+') {{
                event.preventDefault();
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    key: 'zoom_change',
                    value: 'increase'
                }}, '*');
            }} else if (event.altKey && event.key === '-') {{
                event.preventDefault();
                window.parent.postMessage({{
                    type: 'streamlit:setComponentValue',
                    key: 'zoom_change',
                    value: 'decrease'
                }}, '*');
            }}
        }});
        
        // Initialiser le canvas
        setTimeout(updateCanvas, 100);
        </script>
        """, height=display_image.height + 50, scrolling=False)
    
    # Gérer les messages depuis JavaScript
    if 'pdf_points_state' in st.session_state:
        points_data = st.session_state.pdf_points_state
        if points_data and isinstance(points_data, dict):
            state['pending_points'] = points_data.get('points', [])
            state['click_count'] = points_data.get('clickCount', 0)
            
            if points_data.get('complete', False):
                process_measurement_fast(
                    selected_tool,
                    state['pending_points'],
                    measurements,
                    current_page,
                    calibration,
                    zoom_level
                )
                state['pending_points'] = []
                state['click_count'] = 0
                st.session_state.pdf_points_state = None
                st.rerun()
    
    # Gérer les changements de zoom
    if 'zoom_change' in st.session_state:
        if st.session_state.zoom_change == 'increase':
            state['zoom_level'] = min(3.0, state['zoom_level'] + 0.2)
        elif st.session_state.zoom_change == 'decrease':
            state['zoom_level'] = max(0.5, state['zoom_level'] - 0.2)
        st.session_state.zoom_change = None
        st.rerun()

def draw_base_image(base_image: Image.Image, measurements: List[Dict], current_page: int,
                   detected_lines: Optional[List[Dict]]) -> Image.Image:
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
            draw_measurement(draw, measurement)
    
    return img

def draw_pending_points(img: Image.Image, points: List[Tuple], color: str, tool: str):
    """Dessine les points en cours sur l'image"""
    draw = ImageDraw.Draw(img, 'RGBA')
    
    if not points:
        return
    
    color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    color_rgba = color_rgb + (180,)
    
    # Lignes
    if len(points) > 1:
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=color_rgba, width=3)
        
        # Ligne de fermeture
        if tool in ['area', 'perimeter'] and len(points) >= 3:
            draw.line([points[-1], points[0]], fill=color_rgba + (100,), width=2)
    
    # Points
    for i, point in enumerate(points):
        x, y = point
        size = 8
        draw.ellipse([x-size, y-size, x+size, y+size], 
                    fill=color_rgba, outline='white', width=2)
        draw.text((x+size+5, y-size), str(i+1), fill='black')

def process_measurement_fast(tool: str, points: List[Tuple], measurements: List[Dict],
                           current_page: int, calibration: Dict, zoom_level: float):
    """Traite rapidement la mesure"""
    if not points:
        return
    
    # Ajuster la calibration selon le zoom
    calibration_zoom = st.session_state.pdf_ultra_state.get('calibration_zoom', 1.0)
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
        st.session_state.pdf_ultra_state['calibration_zoom'] = zoom_level
        return
    
    if measurement:
        measurements.append(measurement)
        st.session_state.temp_measurement = measurement
        st.session_state.temp_measurement_index = len(measurements) - 1

def draw_measurement(draw: ImageDraw.Draw, measurement: Dict):
    """Dessine une mesure sur l'image"""
    m_type = measurement.get('type')
    points = measurement.get('points', [])
    color = measurement.get('color', '#FF0000')
    
    if not points:
        return
    
    # Ajuster selon le zoom
    current_zoom = st.session_state.pdf_ultra_state.get('zoom_level', 1.0)
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
        
        # Label
        if measurement.get('label'):
            center_x = sum(p[0] for p in adjusted_points) / len(adjusted_points)
            center_y = sum(p[1] for p in adjusted_points) / len(adjusted_points)
            label = f"{measurement['label']}: {measurement.get('value', 0):.2f} {measurement.get('unit', '')}"
            draw_label(draw, (center_x, center_y), label)
    
    elif m_type == 'angle' and len(adjusted_points) >= 3:
        draw.line([tuple(adjusted_points[0]), tuple(adjusted_points[1])], fill=color_rgba, width=3)
        draw.line([tuple(adjusted_points[1]), tuple(adjusted_points[2])], fill=color_rgba, width=3)
        
        # Arc d'angle
        draw_angle_arc(draw, adjusted_points[0], adjusted_points[1], adjusted_points[2], color_rgba)
        
        for i, p in enumerate(adjusted_points):
            x, y = p
            size = 8 if i == 1 else 6
            draw.ellipse([x-size, y-size, x+size, y+size], fill=color_rgba, outline='white')
        
        # Label
        if measurement.get('value') is not None:
            label = f"{measurement.get('label', 'Angle')}: {measurement['value']:.1f}°"
            draw_label(draw, adjusted_points[1], label, offset=(20, -20))

def draw_label(draw: ImageDraw.Draw, position: Tuple[float, float], text: str, 
              offset: Tuple[int, int] = (0, 0)):
    """Dessine un label avec fond"""
    x, y = position
    x += offset[0]
    y += offset[1]
    
    # Fond blanc
    bbox = draw.textbbox((x, y), text)
    padding = 4
    draw.rectangle([bbox[0]-padding, bbox[1]-padding, bbox[2]+padding, bbox[3]+padding],
                  fill=(255, 255, 255, 240), outline='black')
    
    # Texte
    draw.text((x, y), text, fill='black')

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