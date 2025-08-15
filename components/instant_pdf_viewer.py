import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import math
from typing import List, Dict, Optional, Tuple
import json

def InstantPDFViewer(pdf_processor, current_page: int, measurements: List[Dict],
                     selected_tool: str, calibration: Dict, detected_lines: Optional[List[Dict]] = None):
    """Visualiseur PDF instantané sans rechargement"""
    
    # Initialiser l'état
    if 'pdf_instant_state' not in st.session_state:
        st.session_state.pdf_instant_state = {
            'pending_points': [],
            'last_tool': selected_tool,
            'last_page': current_page,
            'zoom_level': 1.5,
            'calibration_zoom': 1.0,
            'display_image': None,
            'base_image': None,
            'last_measurement_count': 0,
            'refresh_count': 0
        }
    
    state = st.session_state.pdf_instant_state
    
    # Réinitialiser si changement
    if state['last_tool'] != selected_tool or state['last_page'] != current_page:
        state['pending_points'] = []
        state['last_tool'] = selected_tool
        state['last_page'] = current_page
        state['base_image'] = None  # Force le rechargement de l'image
        state['display_image'] = None
        state['refresh_count'] += 1  # Incrémenter pour forcer la mise à jour
    
    # Configuration de l'outil
    tool_configs = {
        'distance': {'points': 2, 'auto_complete': True, 'color': '#FF0000', 'name': '📏 Distance'},
        'angle': {'points': 3, 'auto_complete': True, 'color': '#FF00FF', 'name': '📐 Angle'},
        'area': {'points': 3, 'auto_complete': False, 'color': '#00FF00', 'name': '⬜ Surface'},
        'perimeter': {'points': 3, 'auto_complete': False, 'color': '#0000FF', 'name': '🔲 Périmètre'},
        'calibration': {'points': 2, 'auto_complete': True, 'color': '#FFA500', 'name': '🎯 Calibration'}
    }
    
    config = tool_configs.get(selected_tool, {})
    
    # UI minimale
    st.markdown(f"""
    <style>
    .pdf-container {{
        position: relative;
        display: inline-block;
        cursor: crosshair;
    }}
    .point-marker {{
        position: absolute;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        border: 2px solid white;
        transform: translate(-50%, -50%);
        pointer-events: none;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Info tool
    col1, col2 = st.columns([10, 2])
    with col1:
        st.info(f"{config.get('name')} - {len(state['pending_points'])} points - Page {current_page + 1}")
    
    with col2:
        if st.button("🔄 Effacer", key="clear_instant"):
            state['pending_points'] = []
            state['display_image'] = None
            state['refresh_count'] += 1  # Forcer la mise à jour
    
    # Zoom
    zoom = st.slider("🔍", 0.5, 3.0, state['zoom_level'], 0.1, key="zoom_instant", label_visibility="collapsed")
    if zoom != state['zoom_level']:
        # Calculer le ratio de zoom pour ajuster les points en cours
        old_zoom = state['zoom_level']
        zoom_ratio = zoom / old_zoom
        
        # Ajuster les points en cours selon le nouveau zoom
        if state['pending_points']:
            state['pending_points'] = [(p[0] * zoom_ratio, p[1] * zoom_ratio) for p in state['pending_points']]
        
        state['zoom_level'] = zoom
        state['base_image'] = None
        state['display_image'] = None
        state['refresh_count'] += 1  # Forcer la mise à jour lors du zoom
    
    # Générer une clé unique pour forcer le rechargement quand la page change
    image_cache_key = f"page_{current_page}_zoom_{zoom}_measurements_{len(measurements)}"
    
    # Créer/Récupérer l'image de base
    if (state['base_image'] is None or 
        len(measurements) != state['last_measurement_count'] or
        state.get('last_image_key') != image_cache_key):
        
        page_image = pdf_processor.get_page_image(current_page, zoom=zoom)
        if page_image:
            state['base_image'] = create_base_image(page_image, measurements, current_page, detected_lines)
            state['last_measurement_count'] = len(measurements)
            state['last_image_key'] = image_cache_key
            state['display_image'] = None
    
    # Container principal avec deux colonnes
    main_col, data_col = st.columns([8, 2])
    
    with main_col:
        # Container pour l'image
        image_container = st.container()
        
        with image_container:
            # Forcer la création de l'image d'affichage si elle n'existe pas
            if state['base_image'] is not None:
                if state['display_image'] is None:
                    state['display_image'] = state['base_image'].copy()
                    # Redessiner les points en cours s'il y en a
                    if state['pending_points']:
                        draw = ImageDraw.Draw(state['display_image'], 'RGBA')
                        draw_pending_on_image(draw, state['pending_points'], config.get('color'), selected_tool)
            
            if state['display_image'] is not None:
                # Utiliser une clé qui inclut le compteur de rafraîchissement
                coords = streamlit_image_coordinates(
                    state['display_image'],
                    key=f"pdf_instant_{current_page}_{selected_tool}_{state['refresh_count']}"
                )
                
                # Gérer le clic SANS st.rerun()
                if coords:
                    point = (coords["x"], coords["y"])
                    
                    # Vérifier si c'est un nouveau point
                    is_new = True
                    for p in state['pending_points']:
                        if abs(p[0] - point[0]) < 10 and abs(p[1] - point[1]) < 10:
                            is_new = False
                            break
                    
                    if is_new:
                        # Ajouter le point
                        state['pending_points'].append(point)
                        
                        # Redessiner l'image immédiatement
                        state['display_image'] = state['base_image'].copy()
                        draw = ImageDraw.Draw(state['display_image'], 'RGBA')
                        draw_pending_on_image(draw, state['pending_points'], config.get('color'), selected_tool)
                        
                        # Vérifier l'auto-complétion
                        if (config.get('auto_complete') and 
                            len(state['pending_points']) >= config.get('points', 0)):
                            
                            # Traiter la mesure
                            process_instant_measurement(
                                selected_tool, state['pending_points'], 
                                measurements, current_page, calibration, zoom
                            )
                            
                            # Reset
                            state['pending_points'] = []
                            state['base_image'] = None
                            state['display_image'] = None
                            st.rerun()
    
    with data_col:
        # Afficher les points en cours
        if state['pending_points']:
            st.markdown("**Points:**")
            for i, p in enumerate(state['pending_points']):
                st.caption(f"{i+1}: ({p[0]:.0f}, {p[1]:.0f})")
            
            # Bouton de validation pour area/perimeter
            if selected_tool in ['area', 'perimeter'] and len(state['pending_points']) >= 3:
                if st.button("✅ Valider", key="validate_instant"):
                    process_instant_measurement(
                        selected_tool, state['pending_points'],
                        measurements, current_page, calibration, zoom
                    )
                    state['pending_points'] = []
                    state['base_image'] = None
                    state['display_image'] = None
                    st.rerun()
    
    # JavaScript pour gérer les événements sans rechargement
    js_code = f"""
    <script>
    (function() {{
        let points = {json.dumps(state['pending_points'])};
        const tool = '{selected_tool}';
        const config = {json.dumps(config)};
        
        // Gestionnaire de touches
        document.addEventListener('keydown', function(e) {{
            if (e.key === 'Escape') {{
                // Effacer les points
                const clearBtn = document.querySelector('button[key="clear_instant"]');
                if (clearBtn) clearBtn.click();
            }} else if (e.key === 'Enter' && (tool === 'area' || tool === 'perimeter')) {{
                // Valider
                const validateBtn = document.querySelector('button[key="validate_instant"]');
                if (validateBtn) validateBtn.click();
            }}
        }});
    }})();
    </script>
    """
    st.components.v1.html(js_code, height=0)

def create_base_image(page_image: Image.Image, measurements: List[Dict], 
                     current_page: int, detected_lines: Optional[List[Dict]]) -> Image.Image:
    """Crée l'image de base avec les mesures existantes"""
    img = page_image.copy()
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
            draw_measurement_instant(draw, measurement)
    
    return img

def draw_pending_on_image(draw: ImageDraw.Draw, points: List[Tuple], color: str, tool: str):
    """Dessine les points en cours directement sur le draw"""
    if not points:
        return
    
    color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    color_rgba = color_rgb + (180,)
    
    # Lignes
    if len(points) > 1:
        for i in range(len(points) - 1):
            draw.line([points[i], points[i+1]], fill=color_rgba, width=3)
        
        # Fermeture pour area/perimeter
        if tool in ['area', 'perimeter'] and len(points) >= 3:
            # Ligne pointillée
            x1, y1 = points[-1]
            x2, y2 = points[0]
            length = math.sqrt((x2-x1)**2 + (y2-y1)**2)
            steps = int(length / 10)
            for i in range(0, steps, 2):
                t1 = i / steps
                t2 = min((i+1) / steps, 1)
                p1 = (x1 + t1*(x2-x1), y1 + t1*(y2-y1))
                p2 = (x1 + t2*(x2-x1), y1 + t2*(y2-y1))
                draw.line([p1, p2], fill=color_rgba, width=2)
    
    # Points
    for i, point in enumerate(points):
        x, y = point
        # Cercle blanc
        draw.ellipse([x-10, y-10, x+10, y+10], fill='white', outline='white')
        # Point coloré
        draw.ellipse([x-8, y-8, x+8, y+8], fill=color_rgba, outline='black', width=2)
        # Numéro
        draw.text((x+12, y-8), str(i+1), fill='black')

def draw_measurement_instant(draw: ImageDraw.Draw, measurement: Dict):
    """Dessine une mesure"""
    m_type = measurement.get('type')
    points = measurement.get('points', [])
    color = measurement.get('color', '#FF0000')
    
    if not points:
        return
    
    # Ajuster selon zoom
    current_zoom = st.session_state.pdf_instant_state.get('zoom_level', 1.0)
    measurement_zoom = measurement.get('zoom_level', 1.0)
    zoom_ratio = current_zoom / measurement_zoom
    
    adjusted_points = [(p[0] * zoom_ratio, p[1] * zoom_ratio) for p in points]
    
    color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    color_rgba = color_rgb + (200,)
    
    if m_type == 'distance' and len(adjusted_points) >= 2:
        draw.line([adjusted_points[0], adjusted_points[1]], fill=color_rgba, width=4)
        
        for p in adjusted_points:
            draw.ellipse([p[0]-6, p[1]-6, p[0]+6, p[1]+6], 
                        fill=color_rgba, outline='white', width=2)
        
        # Label
        mid_x = (adjusted_points[0][0] + adjusted_points[1][0]) / 2
        mid_y = (adjusted_points[0][1] + adjusted_points[1][1]) / 2
        label = f"{measurement.get('label', '')}: {measurement.get('value', 0):.2f} {measurement.get('unit', '')}"
        draw_label_instant(draw, (mid_x, mid_y), label)
    
    elif m_type in ['area', 'perimeter'] and len(adjusted_points) >= 3:
        if m_type == 'area':
            draw.polygon(adjusted_points, fill=color_rgba[:3] + (50,))
        
        # Contour
        for i in range(len(adjusted_points)):
            j = (i + 1) % len(adjusted_points)
            draw.line([adjusted_points[i], adjusted_points[j]], fill=color_rgba, width=3)
        
        # Points
        for p in adjusted_points:
            draw.ellipse([p[0]-5, p[1]-5, p[0]+5, p[1]+5], 
                        fill=color_rgba, outline='white')
        
        # Label
        center_x = sum(p[0] for p in adjusted_points) / len(adjusted_points)
        center_y = sum(p[1] for p in adjusted_points) / len(adjusted_points)
        label = f"{measurement.get('label', '')}: {measurement.get('value', 0):.2f} {measurement.get('unit', '')}"
        draw_label_instant(draw, (center_x, center_y), label)
    
    elif m_type == 'angle' and len(adjusted_points) >= 3:
        draw.line([adjusted_points[0], adjusted_points[1]], fill=color_rgba, width=3)
        draw.line([adjusted_points[1], adjusted_points[2]], fill=color_rgba, width=3)
        
        # Arc
        angle1 = math.degrees(math.atan2(adjusted_points[0][1] - adjusted_points[1][1], 
                                        adjusted_points[0][0] - adjusted_points[1][0]))
        angle2 = math.degrees(math.atan2(adjusted_points[2][1] - adjusted_points[1][1], 
                                        adjusted_points[2][0] - adjusted_points[1][0]))
        
        radius = 35
        bbox = [adjusted_points[1][0] - radius, adjusted_points[1][1] - radius,
                adjusted_points[1][0] + radius, adjusted_points[1][1] + radius]
        
        start = min(angle1, angle2)
        end = max(angle1, angle2)
        if end - start > 180:
            start, end = end, start + 360
        
        draw.arc(bbox, start, end, fill=color_rgba, width=2)
        
        # Points
        for i, p in enumerate(adjusted_points):
            size = 8 if i == 1 else 6
            draw.ellipse([p[0]-size, p[1]-size, p[0]+size, p[1]+size], 
                        fill=color_rgba, outline='white')
        
        # Label
        label = f"{measurement.get('label', 'Angle')}: {measurement.get('value', 0):.1f}°"
        draw_label_instant(draw, adjusted_points[1], label, offset=(20, -20))

def draw_label_instant(draw: ImageDraw.Draw, position: Tuple[float, float], 
                      text: str, offset: Tuple[int, int] = (0, 0)):
    """Dessine un label"""
    x, y = position
    x += offset[0]
    y += offset[1]
    
    # Taille du texte
    bbox = draw.textbbox((0, 0), text)
    w = bbox[2] - bbox[0] + 8
    h = bbox[3] - bbox[1] + 4
    
    # Fond
    draw.rectangle([x-w//2, y-2, x+w//2, y+h], 
                  fill=(255, 255, 255, 240), outline='black')
    
    # Texte
    draw.text((x-w//2+4, y), text, fill='black')

def process_instant_measurement(tool: str, points: List[Tuple], measurements: List[Dict],
                               current_page: int, calibration: Dict, zoom_level: float):
    """Traite la mesure"""
    if not points:
        return
    
    # Calibration ajustée
    calibration_zoom = st.session_state.pdf_instant_state.get('calibration_zoom', 1.0)
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
        # Calcul aire
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
        # Calcul périmètre
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
        # Calcul angle
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
        st.session_state.pdf_instant_state['calibration_zoom'] = zoom_level
        return
    
    if measurement:
        measurements.append(measurement)
        st.session_state.temp_measurement = measurement
        st.session_state.temp_measurement_index = len(measurements) - 1
        st.success(f"✅ {measurement['label']}: {measurement['value']:.2f} {measurement['unit']}")