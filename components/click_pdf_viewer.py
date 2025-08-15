import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import math
from typing import List, Dict, Optional, Tuple

def ClickablePDFViewer(pdf_processor, current_page: int, measurements: List[Dict],
                      selected_tool: str, calibration: Dict, detected_lines: Optional[List[Dict]] = None):
    """Visualiseur PDF avec support des clics"""
    
    # Contrôle du zoom
    zoom_level = st.slider(
        "🔍 Zoom",
        min_value=0.5,
        max_value=3.0,
        value=st.session_state.get('zoom_level', 1.5),
        step=0.1,
        key='zoom_slider_click'
    )
    st.session_state.zoom_level = zoom_level
    
    # Obtenir l'image
    page_image = pdf_processor.get_page_image(current_page, zoom=zoom_level)
    
    if not page_image:
        st.error("Impossible de charger la page PDF")
        return
    
    # Préparer l'image avec les mesures existantes
    display_image = prepare_display_image(page_image, measurements, current_page, detected_lines)
    
    # Initialiser les points cliqués si nécessaire
    if 'clicked_points' not in st.session_state:
        st.session_state.clicked_points = []
    
    # Afficher l'outil actif et les instructions
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        tool_info = {
            'distance': ('📏 Distance', 'Cliquez 2 points', '#FF0000'),
            'angle': ('📐 Angle', 'Cliquez 3 points (sommet au milieu)', '#FF00FF'),
            'calibration': ('🎯 Calibration', 'Cliquez 2 points d\'une distance connue', '#FFA500'),
            'area': ('⬜ Surface', 'Utilisez plusieurs distances', '#00FF00'),
            'perimeter': ('🔲 Périmètre', 'Utilisez plusieurs distances', '#0000FF')
        }
        
        info = tool_info.get(selected_tool, ('', '', '#000000'))
        st.markdown(f"### {info[0]}")
        st.info(info[1])
    
    with col2:
        points_needed = {'distance': 2, 'angle': 3, 'calibration': 2}.get(selected_tool, 0)
        if points_needed > 0:
            st.metric("Points placés", f"{len(st.session_state.clicked_points)}/{points_needed}")
    
    with col3:
        if st.button("🔄 Réinitialiser", use_container_width=True):
            st.session_state.clicked_points = []
            st.rerun()
    
    # Zone cliquable avec solution de contournement
    st.markdown("### 📍 Cliquez sur l'image pour placer des points")
    
    # Diviser l'image en grille cliquable
    cols_per_row = 10  # Nombre de colonnes dans la grille
    img_width, img_height = display_image.size
    cell_width = img_width // cols_per_row
    cell_height = cell_width  # Cellules carrées
    rows = (img_height + cell_height - 1) // cell_height
    
    # Créer une grille de boutons invisibles sur l'image
    for row in range(min(rows, 10)):  # Limiter pour les performances
        cols = st.columns(cols_per_row)
        for col_idx, col in enumerate(cols):
            x = col_idx * cell_width + cell_width // 2
            y = row * cell_height + cell_height // 2
            
            if col.button(
                " ",
                key=f"cell_{row}_{col_idx}_{current_page}",
                help=f"X: {x}, Y: {y}",
                use_container_width=True
            ):
                add_clicked_point(x, y, selected_tool, measurements, current_page, calibration)
    
    # Afficher l'image en dessous
    st.image(display_image, use_container_width=True)
    
    # Afficher les points cliqués
    if st.session_state.clicked_points:
        st.write("**Points sélectionnés :**")
        for i, point in enumerate(st.session_state.clicked_points):
            st.write(f"Point {i+1}: X={point[0]:.0f}, Y={point[1]:.0f}")
        
        # Bouton pour valider la mesure
        if can_create_measurement(selected_tool, st.session_state.clicked_points):
            if st.button("✅ Valider la mesure", type="primary", use_container_width=True):
                create_measurement(selected_tool, st.session_state.clicked_points, 
                                 measurements, current_page, calibration)
    
    # Option de saisie manuelle
    with st.expander("⌨️ Saisie manuelle des coordonnées"):
        manual_input_form(selected_tool, measurements, current_page, calibration)

def prepare_display_image(base_image: Image.Image, measurements: List[Dict], 
                         current_page: int, detected_lines: Optional[List[Dict]]) -> Image.Image:
    """Prépare l'image avec les mesures et les points cliqués"""
    img = base_image.copy()
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Dessiner les lignes détectées
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
    
    # Dessiner les points cliqués en cours
    if 'clicked_points' in st.session_state:
        for i, point in enumerate(st.session_state.clicked_points):
            x, y = point
            # Point
            draw.ellipse([x-10, y-10, x+10, y+10], fill=(255, 0, 0, 200), outline='white', width=3)
            # Numéro
            draw.text((x+15, y-15), str(i+1), fill='red')
        
        # Lignes entre les points
        if len(st.session_state.clicked_points) > 1:
            for i in range(len(st.session_state.clicked_points) - 1):
                p1 = st.session_state.clicked_points[i]
                p2 = st.session_state.clicked_points[i + 1]
                draw.line([p1, p2], fill=(255, 0, 0, 150), width=3)
    
    return img

def draw_measurement(draw: ImageDraw.Draw, measurement: Dict):
    """Dessine une mesure sur l'image"""
    m_type = measurement.get('type')
    points = measurement.get('points', [])
    color = measurement.get('color', '#FF0000')
    
    if not points:
        return
    
    # Convertir la couleur
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
        if measurement.get('label') and measurement.get('value'):
            mid_x = (points[0][0] + points[1][0]) / 2
            mid_y = (points[0][1] + points[1][1]) / 2
            label = f"{measurement['label']}: {measurement['value']:.2f} {measurement.get('unit', '')}"
            
            # Fond du texte
            bbox = draw.textbbox((mid_x, mid_y), label)
            draw.rectangle([bbox[0]-5, bbox[1]-5, bbox[2]+5, bbox[3]+5], 
                          fill=(255, 255, 255, 230), outline='black')
            draw.text((mid_x, mid_y), label, fill='black')
    
    elif m_type == 'angle' and len(points) >= 3:
        # Lignes
        draw.line([tuple(points[0]), tuple(points[1])], fill=color_rgba, width=4)
        draw.line([tuple(points[1]), tuple(points[2])], fill=color_rgba, width=4)
        
        # Points
        for i, p in enumerate(points[:3]):
            x, y = p
            size = 10 if i == 1 else 8  # Sommet plus gros
            draw.ellipse([x-size, y-size, x+size, y+size], fill=color_rgba, outline='white', width=2)
        
        # Label à côté du sommet
        if measurement.get('value'):
            label = f"{measurement.get('label', 'Angle')}: {measurement['value']:.1f}°"
            x, y = points[1]
            bbox = draw.textbbox((x+20, y), label)
            draw.rectangle([bbox[0]-5, bbox[1]-5, bbox[2]+5, bbox[3]+5], 
                          fill=(255, 255, 255, 230), outline='black')
            draw.text((x+20, y), label, fill='black')

def add_clicked_point(x: int, y: int, tool: str, measurements: List[Dict], 
                     current_page: int, calibration: Dict):
    """Ajoute un point cliqué et crée une mesure si nécessaire"""
    points_needed = {'distance': 2, 'angle': 3, 'calibration': 2}.get(tool, 0)
    
    if points_needed > 0:
        st.session_state.clicked_points.append((x, y))
        
        if len(st.session_state.clicked_points) >= points_needed:
            create_measurement(tool, st.session_state.clicked_points[:points_needed],
                             measurements, current_page, calibration)

def can_create_measurement(tool: str, points: List[Tuple]) -> bool:
    """Vérifie si on peut créer une mesure avec les points actuels"""
    points_needed = {'distance': 2, 'angle': 3, 'calibration': 2}.get(tool, 0)
    return len(points) >= points_needed

def create_measurement(tool: str, points: List[Tuple], measurements: List[Dict],
                      current_page: int, calibration: Dict):
    """Crée une mesure à partir des points"""
    if tool == 'distance':
        p1, p2 = points[:2]
        pixel_distance = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        
        measurement = {
            'type': 'distance',
            'points': [p1, p2],
            'page': current_page,
            'value': pixel_distance * calibration.get('value', 1.0),
            'unit': calibration.get('unit', 'cm'),
            'label': f"Distance_{len(measurements) + 1}",
            'color': '#FF0000'
        }
        
        # Ajouter le produit sélectionné
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
        
        measurements.append(measurement)
        st.session_state.clicked_points = []
        st.success(f"Distance ajoutée : {measurement['value']:.2f} {measurement['unit']}")
        st.rerun()
    
    elif tool == 'angle':
        p1, p2, p3 = points[:3]
        
        # Calculer l'angle
        v1 = (p1[0] - p2[0], p1[1] - p2[1])
        v2 = (p3[0] - p2[0], p3[1] - p2[1])
        
        dot_product = v1[0] * v2[0] + v1[1] * v2[1]
        norm1 = math.sqrt(v1[0]**2 + v1[1]**2)
        norm2 = math.sqrt(v2[0]**2 + v2[1]**2)
        
        if norm1 > 0 and norm2 > 0:
            cos_angle = dot_product / (norm1 * norm2)
            cos_angle = max(-1, min(1, cos_angle))
            angle_deg = math.degrees(math.acos(cos_angle))
            
            measurement = {
                'type': 'angle',
                'points': [p1, p2, p3],
                'page': current_page,
                'value': angle_deg,
                'unit': '°',
                'label': f"Angle_{len(measurements) + 1}",
                'color': '#FF00FF'
            }
            
            measurements.append(measurement)
            st.session_state.clicked_points = []
            st.success(f"Angle ajouté : {angle_deg:.1f}°")
            st.rerun()
    
    elif tool == 'calibration':
        p1, p2 = points[:2]
        pixel_distance = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        
        # Demander la distance réelle
        with st.form("calibration_form"):
            st.write("### Calibration")
            real_value = st.number_input("Distance réelle", min_value=0.01, value=1.0, step=0.01)
            unit = st.selectbox("Unité", options=['mm', 'cm', 'm', 'in', 'ft'])
            
            if st.form_submit_button("Appliquer"):
                cal_factor = real_value / pixel_distance
                st.session_state.current_project['calibration'] = {
                    'value': cal_factor,
                    'unit': unit
                }
                st.session_state.clicked_points = []
                st.success(f"Calibration : 1 pixel = {cal_factor:.4f} {unit}")
                st.rerun()

def manual_input_form(tool: str, measurements: List[Dict], current_page: int, calibration: Dict):
    """Formulaire de saisie manuelle des coordonnées"""
    if tool in ['distance', 'calibration']:
        col1, col2 = st.columns(2)
        
        with col1:
            x1 = st.number_input("X1", value=0, key="manual_x1")
            y1 = st.number_input("Y1", value=0, key="manual_y1")
        
        with col2:
            x2 = st.number_input("X2", value=100, key="manual_x2")
            y2 = st.number_input("Y2", value=100, key="manual_y2")
        
        if st.button("Ajouter avec coordonnées manuelles", key="manual_add"):
            create_measurement(tool, [(x1, y1), (x2, y2)], measurements, current_page, calibration)
    
    elif tool == 'angle':
        col1, col2, col3 = st.columns(3)
        
        with col1:
            x1 = st.number_input("X1", value=0, key="manual_ax1")
            y1 = st.number_input("Y1", value=0, key="manual_ay1")
        
        with col2:
            x2 = st.number_input("X2 (sommet)", value=50, key="manual_ax2")
            y2 = st.number_input("Y2 (sommet)", value=50, key="manual_ay2")
        
        with col3:
            x3 = st.number_input("X3", value=100, key="manual_ax3")
            y3 = st.number_input("Y3", value=0, key="manual_ay3")
        
        if st.button("Ajouter l'angle", key="manual_angle_add"):
            create_measurement(tool, [(x1, y1), (x2, y2), (x3, y3)], measurements, current_page, calibration)