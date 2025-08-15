import streamlit as st
from PIL import Image, ImageDraw
import io
from typing import List, Dict, Optional, Tuple
import base64

def SimplePDFViewer(pdf_processor, current_page: int, measurements: List[Dict],
                   selected_tool: str, calibration: Dict, detected_lines: Optional[List[Dict]] = None):
    """Visualiseur PDF simple mais fonctionnel pour Streamlit"""
    
    # Contrôles de zoom
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        zoom_level = st.slider(
            "🔍 Zoom",
            min_value=0.5,
            max_value=5.0,
            value=st.session_state.get('zoom_level', 2.0),
            step=0.1,
            key='zoom_slider'
        )
        st.session_state.zoom_level = zoom_level
    
    # Obtenir l'image de la page avec le zoom
    page_image = pdf_processor.get_page_image(current_page, zoom=zoom_level)
    
    if not page_image:
        st.error("Impossible de charger la page PDF")
        return
    
    # Créer une copie pour dessiner
    display_image = page_image.copy()
    draw = ImageDraw.Draw(display_image, 'RGBA')
    
    # Dessiner les lignes détectées si disponibles
    if detected_lines and st.session_state.get('show_detected_lines', False):
        for line in detected_lines:
            start = tuple(map(int, line['start']))
            end = tuple(map(int, line['end']))
            draw.line([start, end], fill=(200, 200, 200, 100), width=1)
    
    # Dessiner les mesures existantes
    for measurement in measurements:
        if measurement.get('page') != current_page:
            continue
        
        _draw_measurement(draw, measurement)
    
    # Créer un conteneur scrollable pour les grandes images
    with st.container():
        # Afficher l'image avec les mesures
        st.image(display_image, use_container_width=True)
    
    # Interface de contrôle simple
    with st.expander("🎯 Ajouter des mesures", expanded=True):
        # Afficher l'outil actif avec un style
        tool_colors = {
            'distance': '🔴',
            'area': '🟢',
            'perimeter': '🔵',
            'angle': '🟣',
            'calibration': '🟠'
        }
        
        st.markdown(f"### {tool_colors.get(selected_tool, '⚪')} Outil actif : {selected_tool.capitalize()}")
        
        # Instructions détaillées
        instructions = {
            'distance': "📏 **Mesure de distance** : Cliquez sur l'image pour identifier les coordonnées X,Y de 2 points, puis entrez-les ci-dessous",
            'area': "⬜ **Mesure de surface** : Pour mesurer une surface, utilisez plusieurs mesures de distance pour créer un périmètre",
            'perimeter': "🔲 **Mesure de périmètre** : Pour mesurer un périmètre, additionnez plusieurs mesures de distance",
            'angle': "📐 **Mesure d'angle** : Identifiez 3 points sur l'image (le 2ème point est le sommet de l'angle)",
            'calibration': "🎯 **Calibration** : Mesurez une distance connue sur le plan pour définir l'échelle"
        }
        
        st.info(instructions.get(selected_tool, "Sélectionnez un outil"))
        
        # Aide pour trouver les coordonnées
        st.caption("💡 **Astuce** : Survolez l'image avec votre souris pour voir les coordonnées en bas de votre navigateur, ou faites un clic droit > Inspecter l'élément")
        
        # Solution alternative : utiliser un système de points cliquables
        st.markdown("### 🖱️ Méthode simple pour mesurer :")
        st.markdown("""
        1. **Regardez l'image** et identifiez visuellement les points à mesurer
        2. **Estimez les coordonnées** en utilisant les dimensions de l'image ci-dessous
        3. **Entrez les valeurs** dans les champs
        """)
        
        # Afficher une grille de référence optionnelle
        if st.checkbox("Afficher la grille de référence", key=f"grid_{current_page}"):
            # Redessiner l'image avec une grille
            grid_image = display_image.copy()
            grid_draw = ImageDraw.Draw(grid_image, 'RGBA')
            
            # Grille tous les 100 pixels
            grid_spacing = 100
            width, height = grid_image.size
            
            # Lignes verticales
            for x in range(0, width, grid_spacing):
                grid_draw.line([(x, 0), (x, height)], fill=(200, 200, 200, 100), width=1)
                grid_draw.text((x + 5, 5), str(x), fill=(100, 100, 100))
            
            # Lignes horizontales
            for y in range(0, height, grid_spacing):
                grid_draw.line([(0, y), (width, y)], fill=(200, 200, 200, 100), width=1)
                grid_draw.text((5, y + 5), str(y), fill=(100, 100, 100))
            
            st.image(grid_image, use_container_width=True)
        
        # Entrée manuelle pour distance et calibration
        if selected_tool in ['distance', 'calibration']:
            st.markdown("#### 📍 Entrez les coordonnées des 2 points")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                x1 = st.number_input("X1", value=0, step=10, key=f"x1_{current_page}")
            with col2:
                y1 = st.number_input("Y1", value=0, step=10, key=f"y1_{current_page}")
            with col3:
                x2 = st.number_input("X2", value=100, step=10, key=f"x2_{current_page}")
            with col4:
                y2 = st.number_input("Y2", value=100, step=10, key=f"y2_{current_page}")
            
            # Prévisualisation de la mesure
            if x1 != x2 or y1 != y2:
                col1, col2 = st.columns(2)
                with col1:
                    import math
                    pixel_distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                    real_distance = pixel_distance * calibration.get('value', 1.0)
                    st.info(f"📏 Distance : {real_distance:.2f} {calibration.get('unit', 'cm')}")
                
                with col2:
                    # Afficher un aperçu
                    preview_image = display_image.copy()
                    preview_draw = ImageDraw.Draw(preview_image, 'RGBA')
                    
                    # Dessiner la ligne de prévisualisation
                    preview_draw.line([(x1, y1), (x2, y2)], fill=(255, 165, 0, 200), width=5)
                    preview_draw.ellipse([x1-8, y1-8, x1+8, y1+8], fill=(255, 165, 0), outline='white', width=2)
                    preview_draw.ellipse([x2-8, y2-8, x2+8, y2+8], fill=(255, 165, 0), outline='white', width=2)
                    
                    # Montrer un crop de la zone
                    crop_margin = 50
                    crop_box = (
                        max(0, min(x1, x2) - crop_margin),
                        max(0, min(y1, y2) - crop_margin),
                        min(preview_image.width, max(x1, x2) + crop_margin),
                        min(preview_image.height, max(y1, y2) + crop_margin)
                    )
                    
                    if crop_box[2] > crop_box[0] and crop_box[3] > crop_box[1]:
                        cropped = preview_image.crop(crop_box)
                        st.image(cropped, caption="Aperçu de la mesure", use_container_width=True)
            
            if st.button("➕ Ajouter la mesure", type="primary", key=f"add_{current_page}"):
                points = [(x1, y1), (x2, y2)]
                pixel_distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                
                if selected_tool == 'distance':
                    # Créer une mesure de distance
                    measurement = {
                        'type': 'distance',
                        'points': points,
                        'page': current_page,
                        'value': pixel_distance * calibration.get('value', 1.0),
                        'unit': calibration.get('unit', 'cm'),
                        'label': f"Distance_{len(measurements) + 1}",
                        'color': '#FF0000'
                    }
                    
                    # Ajouter le produit sélectionné si applicable
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
                    
                    st.session_state.current_project['measurements'].append(measurement)
                    st.success(f"Mesure ajoutée : {measurement['value']:.2f} {measurement['unit']}")
                    st.rerun()
                
                elif selected_tool == 'calibration':
                    # Calibration
                    with st.form("calibration_form"):
                        st.write("Calibration")
                        real_value = st.number_input(
                            "Distance réelle",
                            min_value=0.01,
                            value=1.0,
                            step=0.01
                        )
                        unit = st.selectbox(
                            "Unité",
                            options=['mm', 'cm', 'm', 'in', 'ft']
                        )
                        
                        if st.form_submit_button("Appliquer"):
                            cal_factor = real_value / pixel_distance
                            st.session_state.current_project['calibration'] = {
                                'value': cal_factor,
                                'unit': unit
                            }
                            st.success(f"Calibration : 1 pixel = {cal_factor:.4f} {unit}")
                            st.rerun()
        
        elif selected_tool == 'angle':
            # Angle avec 3 points
            col1, col2 = st.columns(2)
            
            with col1:
                x1 = st.number_input("X1", value=0, key=f"ax1_{current_page}")
                y1 = st.number_input("Y1", value=0, key=f"ay1_{current_page}")
                x2 = st.number_input("X2 (sommet)", value=50, key=f"ax2_{current_page}")
                y2 = st.number_input("Y2 (sommet)", value=50, key=f"ay2_{current_page}")
            
            with col2:
                x3 = st.number_input("X3", value=100, key=f"ax3_{current_page}")
                y3 = st.number_input("Y3", value=0, key=f"ay3_{current_page}")
            
            if st.button("➕ Mesurer l'angle", key=f"angle_{current_page}"):
                points = [(x1, y1), (x2, y2), (x3, y3)]
                
                # Calculer l'angle
                import math
                v1 = (x1 - x2, y1 - y2)
                v2 = (x3 - x2, y3 - y2)
                
                dot_product = v1[0] * v2[0] + v1[1] * v2[1]
                norm1 = math.sqrt(v1[0]**2 + v1[1]**2)
                norm2 = math.sqrt(v2[0]**2 + v2[1]**2)
                
                if norm1 > 0 and norm2 > 0:
                    cos_angle = dot_product / (norm1 * norm2)
                    cos_angle = max(-1, min(1, cos_angle))
                    angle_deg = math.degrees(math.acos(cos_angle))
                    
                    measurement = {
                        'type': 'angle',
                        'points': points,
                        'page': current_page,
                        'value': angle_deg,
                        'unit': '°',
                        'label': f"Angle_{len(measurements) + 1}",
                        'color': '#FF00FF'
                    }
                    
                    st.session_state.current_project['measurements'].append(measurement)
                    st.success(f"Angle mesuré : {angle_deg:.1f}°")
                    st.rerun()
                else:
                    st.error("Points invalides pour mesurer un angle")
    
    # Afficher les dimensions de l'image pour référence
    with st.expander("ℹ️ Informations de la page"):
        st.text(f"Dimensions : {page_image.width} x {page_image.height} pixels")
        cal = st.session_state.current_project['calibration']
        st.text(f"Calibration : 1 pixel = {cal['value']:.4f} {cal['unit']}")
        st.text(f"Page {current_page + 1} sur {st.session_state.current_project['total_pages']}")

def _draw_measurement(draw: ImageDraw.Draw, measurement: Dict):
    """Dessine une mesure sur l'image"""
    m_type = measurement.get('type')
    points = measurement.get('points', [])
    color = measurement.get('color', '#FF0000')
    
    if not points:
        return
    
    # Convertir la couleur
    color_rgb = _hex_to_rgb(color)
    color_rgba = color_rgb + (200,)
    
    if m_type == 'distance' and len(points) >= 2:
        # Ligne
        p1, p2 = points[0], points[1]
        draw.line([tuple(p1), tuple(p2)], fill=color_rgba, width=5)  # Plus épais
        
        # Points
        for p in [p1, p2]:
            _draw_point(draw, p, color_rgba)
        
        # Label
        if measurement.get('label') and measurement.get('value'):
            mid_point = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
            label = f"{measurement['label']}: {measurement['value']:.2f} {measurement.get('unit', '')}"
            _draw_label(draw, mid_point, label)
    
    elif m_type in ['area', 'perimeter'] and len(points) >= 3:
        # Polygone
        polygon_points = [tuple(p) for p in points]
        
        if m_type == 'area':
            # Remplir avec transparence
            draw.polygon(polygon_points, fill=color_rgba[:3] + (50,), 
                       outline=color_rgba, width=2)
        else:
            # Juste le contour
            for i in range(len(polygon_points)):
                next_i = (i + 1) % len(polygon_points)
                draw.line([polygon_points[i], polygon_points[next_i]], 
                        fill=color_rgba, width=2)
        
        # Points
        for p in points:
            _draw_point(draw, p, color_rgba)
        
        # Label au centre
        if measurement.get('label') and measurement.get('value'):
            center_x = sum(p[0] for p in points) / len(points)
            center_y = sum(p[1] for p in points) / len(points)
            label = f"{measurement['label']}: {measurement['value']:.2f} {measurement.get('unit', '')}"
            _draw_label(draw, (center_x, center_y), label)
    
    elif m_type == 'angle' and len(points) >= 3:
        # Lignes de l'angle
        p1, p2, p3 = points[:3]
        draw.line([tuple(p1), tuple(p2)], fill=color_rgba, width=2)
        draw.line([tuple(p2), tuple(p3)], fill=color_rgba, width=2)
        
        # Points
        for p in [p1, p2, p3]:
            _draw_point(draw, p, color_rgba)
        
        # Label
        if measurement.get('value'):
            label = f"{measurement.get('label', 'Angle')}: {measurement['value']:.1f}°"
            _draw_label(draw, p2, label)

def _draw_point(draw: ImageDraw.Draw, point: Tuple[float, float], color):
    """Dessine un point"""
    x, y = point
    r = 8  # Plus gros pour être plus visible
    # Cercle extérieur blanc
    draw.ellipse([x-r-2, y-r-2, x+r+2, y+r+2], fill='white', outline='white')
    # Cercle intérieur coloré
    draw.ellipse([x-r, y-r, x+r, y+r], fill=color, outline='black')

def _draw_label(draw: ImageDraw.Draw, position: Tuple[float, float], text: str):
    """Dessine un label avec fond"""
    x, y = position
    
    # Utiliser une police par défaut plus grande si possible
    try:
        from PIL import ImageFont
        # Essayer de charger une police plus grande
        font = ImageFont.load_default()
    except:
        font = None
    
    # Obtenir la taille du texte
    bbox = draw.textbbox((x, y), text, font=font)
    padding = 6
    
    # Dessiner le fond avec bordure
    draw.rectangle(
        [bbox[0]-padding-1, bbox[1]-padding-1, bbox[2]+padding+1, bbox[3]+padding+1],
        fill='black'
    )
    draw.rectangle(
        [bbox[0]-padding, bbox[1]-padding, bbox[2]+padding, bbox[3]+padding],
        fill=(255, 255, 255, 230)
    )
    
    # Dessiner le texte
    draw.text((x, y), text, fill='black', font=font)

def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convertit une couleur hexadécimale en RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))