import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw, ImageFont
import math
from typing import List, Dict, Optional, Tuple

def SimpleReactiveViewer(pdf_processor, current_page: int, measurements: List[Dict],
                        selected_tool: str, calibration: Dict, detected_lines: Optional[List[Dict]] = None):
    """Version avec support du mode orthogonal (ORTHO)"""
    
    # État minimal
    if 'viewer_state' not in st.session_state:
        st.session_state.viewer_state = {
            'points': [],
            'zoom': 1.5,
            'ortho_active': False,
            'preview_point': None
        }
    
    # Reset si changement de page/outil
    if 'last_page' not in st.session_state or st.session_state.last_page != current_page:
        st.session_state.viewer_state['points'] = []
        st.session_state.last_page = current_page
    
    if 'last_tool' not in st.session_state or st.session_state.last_tool != selected_tool:
        st.session_state.viewer_state['points'] = []
        st.session_state.last_tool = selected_tool
    
    state = st.session_state.viewer_state
    
    # Config outil
    configs = {
        'distance': {'max': 2, 'color': '#FF0000'},
        'angle': {'max': 3, 'color': '#FF00FF'},
        'area': {'max': 99, 'color': '#00FF00'},
        'perimeter': {'max': 99, 'color': '#0000FF'},
        'calibration': {'max': 2, 'color': '#FFA500'}
    }
    
    config = configs.get(selected_tool, {'max': 2, 'color': '#000000'})
    
    # UI simple avec indicateur ORTHO
    info_text = f"{selected_tool.capitalize()} - {len(state['points'])} points"
    if state.get('ortho_active', False):
        info_text += " - **ORTHO**"
    st.info(info_text)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Effacer", type="primary"):
            state['points'] = []
    with col2:
        if st.button("Valider", type="primary") and len(state['points']) >= 2:
            # Traiter la mesure
            save_measurement(selected_tool, state['points'], measurements, current_page, calibration, state['zoom'])
            state['points'] = []
            st.rerun()
    
    # Zoom et options
    col1, col2 = st.columns([3, 1])
    with col1:
        state['zoom'] = st.slider("Zoom", 0.5, 3.0, state['zoom'], 0.1)
    with col2:
        # Checkbox pour activer/désactiver le mode ortho manuellement
        ortho_manual = st.checkbox("Mode Ortho (Shift)", value=state.get('ortho_active', False), help="Maintenez Shift pour activer temporairement")
        if ortho_manual != state.get('ortho_active', False):
            state['ortho_active'] = ortho_manual
    
    # Obtenir l'image
    base_img = pdf_processor.get_page_image(current_page, zoom=state['zoom'])
    if not base_img:
        st.error("Erreur chargement PDF")
        return
    
    # Dessiner avec support RGBA pour la transparence
    img = base_img.copy()
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Afficher l'indicateur ORTHO si actif
    if state.get('ortho_active', False):
        # Rectangle pour l'indicateur ORTHO
        ortho_box = (10, 10, 80, 35)
        draw.rectangle(ortho_box, fill=(255, 165, 0, 200), outline=(255, 165, 0, 255), width=2)
        try:
            # Essayer d'utiliser une police par défaut
            draw.text((20, 15), "ORTHO", fill=(255, 255, 255, 255))
        except:
            draw.text((20, 15), "ORTHO", fill=(255, 255, 255, 255))
    
    # Mesures existantes triées par ordre de dessin (du plus bas au plus haut)
    page_measurements = [m for m in measurements if m.get('page') == current_page]
    
    # S'assurer que toutes les mesures ont un draw_order
    for i, m in enumerate(page_measurements):
        if 'draw_order' not in m:
            m['draw_order'] = i
    
    sorted_measurements = sorted(page_measurements, key=lambda m: m.get('draw_order', 0))
    
    for m in sorted_measurements:
        draw_saved_measurement(draw, m, state['zoom'])
    
    # Points en cours avec transparence
    if state['points']:
        color = config['color']
        rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        # Transparence pour les points en cours (semi-transparent)
        rgba = rgb + (150,)
        
        # Lignes avec transparence
        for i in range(len(state['points']) - 1):
            draw.line([state['points'][i], state['points'][i+1]], fill=rgba, width=3)
        
        # Mode ortho : afficher les lignes guides si actif
        if state.get('ortho_active', False) and len(state['points']) > 0:
            last_point = state['points'][-1]
            # Dessiner les lignes guides orthogonales
            guide_color = (128, 128, 128, 80)  # Gris semi-transparent
            highlight_color = (255, 165, 0, 120)  # Orange pour la direction active
            guide_length = 150  # Longueur des guides
            
            # Lignes guides pour les 8 directions
            for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
                angle_rad = math.radians(angle)
                end_x = last_point[0] + guide_length * math.cos(angle_rad)
                end_y = last_point[1] + guide_length * math.sin(angle_rad)
                
                # Ligne guide
                draw_dashed_line(draw, last_point, (end_x, end_y), guide_color)
                
                # Afficher l'angle
                text_x = last_point[0] + (guide_length/2) * math.cos(angle_rad)
                text_y = last_point[1] + (guide_length/2) * math.sin(angle_rad)
                draw.text((text_x-10, text_y-10), f"{angle}°", fill=(128, 128, 128, 200))
        
        # Ligne pointillée pour fermer les polygones (seulement pour les surfaces)
        if selected_tool == 'area' and len(state['points']) >= 3:
            draw_dashed_line(draw, state['points'][-1], state['points'][0], rgba)
        
        # Points avec transparence
        for i, p in enumerate(state['points']):
            # Cercle blanc semi-transparent en fond
            draw.ellipse([p[0]-8, p[1]-8, p[0]+8, p[1]+8], fill=(255, 255, 255, 180), outline=(255, 255, 255, 220), width=2)
            # Point coloré transparent
            draw.ellipse([p[0]-6, p[1]-6, p[0]+6, p[1]+6], fill=rgba, outline='black', width=1)
            # Numéro avec fond blanc
            bbox = draw.textbbox((p[0]+10, p[1]-10), str(i+1))
            draw.rectangle([bbox[0]-2, bbox[1]-2, bbox[2]+2, bbox[3]+2], fill=(255, 255, 255, 200))
            draw.text((p[0]+10, p[1]-10), str(i+1), fill='black')
    
    # Instructions pour le mode ortho
    with st.expander("Mode Orthogonal", expanded=False):
        st.info("""
        **Mode Orthogonal (ORTHO)**:
        - Activez le mode ortho avec le checkbox ou maintenez la touche **Shift**
        - Les lignes seront contraintes aux angles : 0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°
        - Des guides visuels apparaissent pour montrer les directions possibles
        """)
    
    # Afficher avec coordonnées
    clicked = streamlit_image_coordinates(img, key=f"img_{current_page}_{selected_tool}_{len(state['points'])}")
    
    # L'état ortho est géré par le checkbox
    
    # Traiter le clic
    if clicked:
        x, y = clicked["x"], clicked["y"]
        
        # Éviter les doublons
        is_new = True
        for p in state['points']:
            if abs(p[0] - x) < 10 and abs(p[1] - y) < 10:
                is_new = False
                break
        
        if is_new:
            # Appliquer le mode ortho si actif et qu'il y a déjà un point
            if state.get('ortho_active', False) and len(state['points']) > 0:
                x, y = calculate_ortho_point(state['points'][-1], (x, y))
            
            state['points'].append((x, y))
            
            # Auto-complétion pour distance/angle/calibration
            if selected_tool in ['distance', 'angle', 'calibration'] and len(state['points']) >= config['max']:
                save_measurement(selected_tool, state['points'], measurements, current_page, calibration, state['zoom'])
                state['points'] = []
                st.rerun()
            else:
                # Forcer la mise à jour
                st.rerun()

def calculate_ortho_point(last_point: Tuple[float, float], current_point: Tuple[float, float]) -> Tuple[float, float]:
    """Calcule le point orthogonal le plus proche (0°, 45°, 90°, etc.)"""
    dx = current_point[0] - last_point[0]
    dy = current_point[1] - last_point[1]
    
    # Calculer l'angle
    angle = math.atan2(dy, dx)
    angle_deg = math.degrees(angle)
    
    # Angles orthogonaux possibles (0°, 45°, 90°, 135°, 180°, 225°, 270°, 315°)
    ortho_angles = [0, 45, 90, 135, 180, 225, 270, 315]
    
    # Normaliser l'angle entre 0 et 360
    if angle_deg < 0:
        angle_deg += 360
    
    # Trouver l'angle orthogonal le plus proche
    closest_angle = min(ortho_angles, key=lambda a: min(abs(a - angle_deg), abs(a - angle_deg + 360), abs(a - angle_deg - 360)))
    
    # Calculer la distance
    distance = math.sqrt(dx**2 + dy**2)
    
    # Calculer le nouveau point selon l'angle orthogonal
    angle_rad = math.radians(closest_angle)
    new_x = last_point[0] + distance * math.cos(angle_rad)
    new_y = last_point[1] + distance * math.sin(angle_rad)
    
    return (new_x, new_y)

def draw_dashed_line(draw, start, end, color):
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

def draw_saved_measurement(draw, measurement, current_zoom):
    """Dessine une mesure sauvegardée avec transparence"""
    points = measurement.get('points', [])
    if not points:
        return
    
    # Ajuster au zoom
    saved_zoom = measurement.get('zoom_level', 1.0)
    ratio = current_zoom / saved_zoom
    adjusted = [(p[0] * ratio, p[1] * ratio) for p in points]
    
    color = measurement.get('color', '#000000')
    rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
    
    # Niveaux de transparence selon le type
    transparency_levels = {
        'distance': 180,      # Plus opaque pour les lignes
        'angle': 180,         # Plus opaque pour les angles
        'area': 80,          # Très transparent pour les surfaces
        'perimeter': 120,    # Moyennement transparent
        'calibration': 200   # Presque opaque pour la calibration
    }
    
    m_type = measurement.get('type')
    base_alpha = transparency_levels.get(m_type, 150)
    
    # Appliquer l'ajustement de transparence si disponible
    adjustment = st.session_state.get('transparency_adjustment', 0)
    alpha = max(30, min(255, base_alpha + adjustment))  # Garder entre 30 et 255
    rgba = rgb + (alpha,)
    
    # Récupérer le nom de la mesure et du produit
    measurement_label = measurement.get('label', '')
    product = measurement.get('product', {})
    product_name = product.get('name', '')
    
    # Créer le texte à afficher (nom de mesure + produit)
    display_text = ""
    if measurement_label and product_name:
        display_text = f"{measurement_label} - {product_name}"
    elif measurement_label:
        display_text = measurement_label
    elif product_name:
        display_text = product_name
    
    if m_type == 'distance' and len(adjusted) >= 2:
        # Utiliser ImageDraw avec mode RGBA pour la transparence
        draw.line([adjusted[0], adjusted[1]], fill=rgba, width=3)
        for p in adjusted:
            draw.ellipse([p[0]-5, p[1]-5, p[0]+5, p[1]+5], fill=rgba, outline=(255, 255, 255, 200), width=1)
        
        # Afficher le nom de la mesure et du produit au milieu de la ligne
        if display_text:
            mid_x = (adjusted[0][0] + adjusted[1][0]) / 2
            mid_y = (adjusted[0][1] + adjusted[1][1]) / 2
            
            # Essayer de charger une police pour le texte en gras
            try:
                from PIL import ImageFont
                # Ajuster la taille selon la longueur du texte
                font_size = 14 if len(display_text) > 20 else 16
                
                # Essayer différentes polices système
                font = None
                font_paths = [
                    "C:/Windows/Fonts/arialbd.ttf",  # Windows Arial Bold
                    "C:/Windows/Fonts/arial.ttf",    # Windows Arial regular
                    "/System/Library/Fonts/Helvetica.ttc",  # macOS
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",  # Linux
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                ]
                for font_path in font_paths:
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        break
                    except:
                        continue
                if not font:
                    try:
                        font = ImageFont.load_default()
                    except:
                        font = None
            except:
                font = None
            
            # Texte du produit avec contour blanc pour la lisibilité
            text_x = mid_x
            text_y = mid_y - 25
            
            # Dessiner un contour blanc autour du texte pour la lisibilité
            outline_offsets = [(-2, -2), (-2, 0), (-2, 2), (0, -2), (0, 2), (2, -2), (2, 0), (2, 2)]
            for dx, dy in outline_offsets:
                try:
                    if font:
                        draw.text((text_x + dx, text_y + dy), display_text, fill=(255, 255, 255, 255), anchor="mm", font=font)
                    else:
                        draw.text((text_x + dx, text_y + dy), display_text, fill=(255, 255, 255, 255), anchor="mm")
                except:
                    pass
            
            # Texte principal en noir
            try:
                if font:
                    draw.text((text_x, text_y), display_text, fill=(0, 0, 0, 255), anchor="mm", font=font)
                else:
                    draw.text((text_x, text_y), display_text, fill=(0, 0, 0, 255), anchor="mm")
            except:
                # Fallback sans anchor
                try:
                    if font:
                        draw.text((text_x-len(display_text)*4, text_y), display_text, fill=(0, 0, 0, 255), font=font)
                    else:
                        draw.text((text_x-len(display_text)*4, text_y), display_text, fill=(0, 0, 0, 255))
                except:
                    pass
    
    elif m_type in ['area', 'perimeter'] and len(adjusted) >= 3:
        if m_type == 'area':
            # Remplissage très transparent pour les surfaces
            draw.polygon(adjusted, fill=rgba[:3] + (50,), outline=rgba)
        # Contour avec transparence appropriée
        for i in range(len(adjusted)):
            j = (i + 1) % len(adjusted)
            draw.line([adjusted[i], adjusted[j]], fill=rgba, width=3)
        # Points aux sommets avec transparence
        for p in adjusted:
            draw.ellipse([p[0]-4, p[1]-4, p[0]+4, p[1]+4], fill=rgba, outline=(255, 255, 255, 200), width=1)
        
        # Afficher le nom de la mesure et du produit au centre du polygone
        if display_text:
            # Calculer le centre du polygone
            center_x = sum(p[0] for p in adjusted) / len(adjusted)
            center_y = sum(p[1] for p in adjusted) / len(adjusted)
            
            # Essayer de charger une police pour le texte en gras
            try:
                from PIL import ImageFont
                # Ajuster la taille selon la longueur du texte
                font_size = 14 if len(display_text) > 20 else 16
                
                # Essayer différentes polices système
                font = None
                font_paths = [
                    "C:/Windows/Fonts/arialbd.ttf",  # Windows Arial Bold
                    "C:/Windows/Fonts/arial.ttf",    # Windows Arial regular
                    "/System/Library/Fonts/Helvetica.ttc",  # macOS
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",  # Linux
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                ]
                for font_path in font_paths:
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        break
                    except:
                        continue
                if not font:
                    try:
                        font = ImageFont.load_default()
                    except:
                        font = None
            except:
                font = None
            
            # Texte du produit avec contour blanc pour la lisibilité
            # Dessiner un contour blanc autour du texte pour la lisibilité
            outline_offsets = [(-2, -2), (-2, 0), (-2, 2), (0, -2), (0, 2), (2, -2), (2, 0), (2, 2)]
            for dx, dy in outline_offsets:
                try:
                    if font:
                        draw.text((center_x + dx, center_y + dy), display_text, fill=(255, 255, 255, 255), anchor="mm", font=font)
                    else:
                        draw.text((center_x + dx, center_y + dy), display_text, fill=(255, 255, 255, 255), anchor="mm")
                except:
                    pass
            
            # Texte principal en noir
            try:
                if font:
                    draw.text((center_x, center_y), display_text, fill=(0, 0, 0, 255), anchor="mm", font=font)
                else:
                    draw.text((center_x, center_y), display_text, fill=(0, 0, 0, 255), anchor="mm")
            except:
                # Fallback sans anchor
                try:
                    if font:
                        draw.text((center_x-len(display_text)*4, center_y), display_text, fill=(0, 0, 0, 255), font=font)
                    else:
                        draw.text((center_x-len(display_text)*4, center_y), display_text, fill=(0, 0, 0, 255))
                except:
                    pass
    
    elif m_type == 'angle' and len(adjusted) >= 3:
        draw.line([adjusted[0], adjusted[1]], fill=rgba, width=3)
        draw.line([adjusted[1], adjusted[2]], fill=rgba, width=3)
        # Points avec transparence
        for i, p in enumerate(adjusted):
            size = 6 if i == 1 else 5
            draw.ellipse([p[0]-size, p[1]-size, p[0]+size, p[1]+size], fill=rgba, outline=(255, 255, 255, 200), width=1)
        
        # Afficher le nom de la mesure et du produit près du sommet de l'angle
        if display_text:
            vertex_x = adjusted[1][0]
            vertex_y = adjusted[1][1]
            
            # Positionner le texte légèrement décalé du sommet
            text_x = vertex_x + 20
            text_y = vertex_y - 20
            
            # Essayer de charger une police pour le texte en gras
            try:
                from PIL import ImageFont
                # Ajuster la taille selon la longueur du texte
                font_size = 14 if len(display_text) > 20 else 16
                
                # Essayer différentes polices système
                font = None
                font_paths = [
                    "C:/Windows/Fonts/arialbd.ttf",  # Windows Arial Bold
                    "C:/Windows/Fonts/arial.ttf",    # Windows Arial regular
                    "/System/Library/Fonts/Helvetica.ttc",  # macOS
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",  # Linux
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                ]
                for font_path in font_paths:
                    try:
                        font = ImageFont.truetype(font_path, font_size)
                        break
                    except:
                        continue
                if not font:
                    try:
                        font = ImageFont.load_default()
                    except:
                        font = None
            except:
                font = None
            
            # Texte du produit avec contour blanc pour la lisibilité
            # Dessiner un contour blanc autour du texte pour la lisibilité
            outline_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            for dx, dy in outline_offsets:
                if font:
                    draw.text((text_x + dx, text_y + dy), display_text, fill=(255, 255, 255, 255), anchor="mm", font=font)
                else:
                    draw.text((text_x + dx, text_y + dy), display_text, fill=(255, 255, 255, 255), anchor="mm")
            
            # Texte principal en noir
            if font:
                draw.text((text_x, text_y), display_text, fill=(0, 0, 0, 255), anchor="mm", font=font)
            else:
                draw.text((text_x, text_y), display_text, fill=(0, 0, 0, 255), anchor="mm")

def save_measurement(tool, points, measurements, page, calibration, zoom):
    """Sauvegarde une mesure"""
    if not points:
        return
    
    cal_value = calibration.get('value', 1.0)
    cal_unit = calibration.get('unit', 'cm')
    measurement = None
    
    # Déterminer l'ordre de dessin (le plus élevé s'affiche au-dessus)
    max_order = max([m.get('draw_order', 0) for m in measurements], default=0)
    new_draw_order = max_order + 1
    
    if tool == 'distance' and len(points) >= 2:
        dist = math.sqrt((points[1][0] - points[0][0])**2 + (points[1][1] - points[0][1])**2)
        measurement = {
            'type': 'distance',
            'points': points[:2],
            'page': page,
            'value': dist * cal_value,
            'unit': cal_unit,
            'label': f"Distance_{len([m for m in measurements if m['type'] == 'distance']) + 1}",
            'color': '#FF0000',
            'zoom_level': zoom,
            'draw_order': new_draw_order
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
            'page': page,
            'value': area * cal_value * cal_value,
            'unit': f"{cal_unit}²",
            'label': f"Surface_{len([m for m in measurements if m['type'] == 'area']) + 1}",
            'color': '#00FF00',
            'zoom_level': zoom,
            'draw_order': new_draw_order
        }
    
    elif tool == 'perimeter' and len(points) >= 3:
        perim = 0.0
        # Calculer seulement les segments entre points consécutifs (sans fermer)
        for i in range(len(points) - 1):
            j = i + 1
            perim += math.sqrt((points[j][0] - points[i][0])**2 + (points[j][1] - points[i][1])**2)
        
        measurement = {
            'type': 'perimeter',
            'points': points[:],
            'page': page,
            'value': perim * cal_value,
            'unit': cal_unit,
            'label': f"Périmètre_{len([m for m in measurements if m['type'] == 'perimeter']) + 1}",
            'color': '#0000FF',
            'zoom_level': zoom,
            'draw_order': new_draw_order
        }
    
    elif tool == 'angle' and len(points) >= 3:
        v1 = (points[0][0] - points[1][0], points[0][1] - points[1][1])
        v2 = (points[2][0] - points[1][0], points[2][1] - points[1][1])
        dot = v1[0] * v2[0] + v1[1] * v2[1]
        det = v1[0] * v2[1] - v1[1] * v2[0]
        angle = abs(math.degrees(math.atan2(det, dot)))
        
        measurement = {
            'type': 'angle',
            'points': points[:3],
            'page': page,
            'value': angle,
            'unit': '°',
            'label': f"Angle_{len([m for m in measurements if m['type'] == 'angle']) + 1}",
            'color': '#FF00FF',
            'zoom_level': zoom,
            'draw_order': new_draw_order
        }
    
    elif tool == 'calibration' and len(points) >= 2:
        dist = math.sqrt((points[1][0] - points[0][0])**2 + (points[1][1] - points[0][1])**2)
        st.session_state.calibration_distance = dist
        st.session_state.show_calibration_dialog = True
        return
    
    # Ajouter la mesure et déclencher le dialogue produit
    if measurement:
        measurements.append(measurement)
        # Déclencher le dialogue d'association de produit
        st.session_state.temp_measurement = measurement
        st.session_state.temp_measurement_index = len(measurements) - 1
        st.success(f"✅ {measurement['label']}: {measurement['value']:.2f} {measurement['unit']}")