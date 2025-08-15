import streamlit as st
from streamlit_image_coordinates import streamlit_image_coordinates
from PIL import Image, ImageDraw
import math
from typing import List, Dict, Optional, Tuple
import json

def FinalPDFViewer(pdf_processor, current_page: int, measurements: List[Dict],
                   selected_tool: str, calibration: Dict, detected_lines: Optional[List[Dict]] = None):
    """Visualiseur PDF final avec fermeture automatique par Enter"""
    
    # Initialiser l'état
    if 'pending_points' not in st.session_state:
        st.session_state.pending_points = []
    if 'viewer_key' not in st.session_state:
        st.session_state.viewer_key = 0
    
    # Contrôle du zoom
    zoom_level = st.slider(
        "🔍 Zoom",
        min_value=0.5,
        max_value=3.0,
        value=st.session_state.get('zoom_level', 1.5),
        step=0.1,
        key='zoom_final'
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
    col1, col2, col3 = st.columns([4, 1, 1])
    
    with col1:
        st.markdown(f"### {config.get('name', selected_tool)}")
    
    with col2:
        points_count = len(st.session_state.pending_points)
        st.metric("Points", points_count)
    
    with col3:
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            # Bouton valider
            can_validate = False
            if selected_tool in ['area', 'perimeter'] and points_count >= 3:
                can_validate = True
            elif config.get('auto_complete') and points_count >= config.get('points', 0):
                can_validate = True
            
            if can_validate:
                if st.button("✅", help="Valider", key=f"val_{st.session_state.viewer_key}"):
                    create_measurement(selected_tool, st.session_state.pending_points, 
                                     measurements, current_page, calibration)
                    st.session_state.pending_points = []
                    st.session_state.viewer_key += 1
                    st.rerun()
        
        with col_btn2:
            if st.button("🔄", help="Effacer", key=f"clr_{st.session_state.viewer_key}"):
                st.session_state.pending_points = []
                st.session_state.viewer_key += 1
                st.rerun()
    
    # Instructions avec raccourci
    instructions = {
        'distance': "Cliquez 2 points pour mesurer une distance",
        'angle': "Cliquez 3 points (sommet au milieu) pour mesurer un angle",
        'area': "Cliquez au moins 3 points • Appuyez sur **Enter** pour fermer automatiquement",
        'perimeter': "Cliquez au moins 3 points • Appuyez sur **Enter** pour fermer automatiquement",
        'calibration': "Cliquez 2 points d'une distance connue"
    }
    
    st.info(instructions.get(selected_tool, ""))
    
    # Préparer l'image
    display_image = prepare_image(page_image, measurements, current_page, 
                                 st.session_state.pending_points, config.get('color', '#000000'),
                                 selected_tool, detected_lines)
    
    # Container pour le PDF
    pdf_container = st.container()
    
    with pdf_container:
        # Image cliquable
        coords = streamlit_image_coordinates(
            display_image,
            key=f"img_{current_page}_{selected_tool}_{st.session_state.viewer_key}"
        )
        
        if coords is not None:
            x, y = coords["x"], coords["y"]
            
            # Appliquer l'accrochage
            if st.session_state.snap_enabled and detected_lines:
                snap_point = find_snap_point((x, y), detected_lines, st.session_state.snap_threshold)
                if snap_point:
                    x, y = snap_point
            
            # Vérifier que ce n'est pas un point existant
            is_new_point = True
            for p in st.session_state.pending_points:
                if abs(p[0] - x) < 5 and abs(p[1] - y) < 5:
                    is_new_point = False
                    break
            
            if is_new_point:
                st.session_state.pending_points.append((x, y))
                st.session_state.viewer_key += 1
                
                # Auto-complétion
                if config.get('auto_complete') and len(st.session_state.pending_points) >= config.get('points', 0):
                    create_measurement(selected_tool, st.session_state.pending_points, 
                                     measurements, current_page, calibration)
                    st.session_state.pending_points = []
                
                st.rerun()
    
    # Gestionnaire de touche Enter pour area/perimeter
    if selected_tool in ['area', 'perimeter'] and len(st.session_state.pending_points) >= 3:
        # Utiliser un formulaire invisible pour capturer Enter
        with st.form(key=f"enter_form_{st.session_state.viewer_key}", clear_on_submit=True):
            # Champ invisible qui capture Enter
            submit = st.form_submit_button("", help="Appuyez sur Enter pour fermer la forme")
            
            if submit:
                create_measurement(selected_tool, st.session_state.pending_points, 
                                 measurements, current_page, calibration)
                st.session_state.pending_points = []
                st.session_state.viewer_key += 1
                st.rerun()
        
        # CSS pour cacher le bouton mais garder la fonctionnalité Enter
        st.markdown("""
        <style>
        div[data-testid="stForm"] {
            border: none;
            padding: 0;
            margin: 0;
        }
        div[data-testid="stForm"] button[type="submit"] {
            position: absolute;
            left: -9999px;
            width: 1px;
            height: 1px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Liste des points
    if st.session_state.pending_points:
        with st.expander("📍 Points placés", expanded=True):
            for i, point in enumerate(st.session_state.pending_points):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    st.text(f"Point {i+1}")
                with col2:
                    st.text(f"X: {point[0]:.0f}, Y: {point[1]:.0f}")
                with col3:
                    if st.button("❌", key=f"del_{i}_{st.session_state.viewer_key}"):
                        st.session_state.pending_points.pop(i)
                        st.session_state.viewer_key += 1
                        st.rerun()

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
        
        # Ajouter à la liste temporairement
        measurements.append(measurement)
        
        # Demander l'association de produit
        show_product_association_dialog(measurement, len(measurements) - 1)
        
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
        
        # Ajouter à la liste temporairement
        measurements.append(measurement)
        
        # Demander l'association de produit
        show_product_association_dialog(measurement, len(measurements) - 1)
        
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
        
        # Ajouter à la liste temporairement
        measurements.append(measurement)
        
        # Demander l'association de produit
        show_product_association_dialog(measurement, len(measurements) - 1)
        
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

def show_product_association_dialog(measurement: Dict, measurement_index: int):
    """Affiche un dialogue pour associer un produit à la mesure"""
    @st.dialog(f"🏷️ Associer un produit à {measurement['label']}")
    def product_dialog():
        # Afficher les infos de la mesure
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Valeur", f"{measurement['value']:.2f} {measurement['unit']}")
        with col2:
            st.metric("Type", measurement['type'].capitalize())
        
        st.divider()
        
        # Sélection de catégorie
        categories = st.session_state.product_catalog.get_categories()
        
        # Utiliser la catégorie sélectionnée ou la première disponible
        default_category = st.session_state.selected_category if st.session_state.selected_category in categories else (categories[0] if categories else None)
        
        if categories:
            selected_category = st.selectbox(
                "📂 Catégorie",
                options=categories,
                index=categories.index(default_category) if default_category else 0,
                key=f"cat_select_{measurement_index}"
            )
            
            # Produits de la catégorie
            products = st.session_state.product_catalog.get_products_by_category(selected_category)
            
            if products:
                # Afficher les produits avec leurs infos
                st.subheader("📦 Produits disponibles")
                
                selected_product_name = None
                
                # Créer une grille de produits
                for i, (product_name, product_data) in enumerate(products.items()):
                    # Container pour chaque produit
                    with st.container():
                        color = product_data.get('color', '#CCCCCC')
                        
                        # Créer un style CSS pour le bouton avec la couleur du produit
                        st.markdown(f"""
                        <style>
                        div[data-testid="stButton"] > button[key="prod_{measurement_index}_{product_name}"] {{
                            border-left: 5px solid {color};
                        }}
                        </style>
                        """, unsafe_allow_html=True)
                        
                        col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 1])
                        
                        with col1:
                            # Pastille de couleur
                            st.markdown(
                                f'<div style="width: 30px; height: 30px; background-color: {color}; border-radius: 50%; border: 2px solid #333; margin-top: 5px;"></div>',
                                unsafe_allow_html=True
                            )
                        
                        with col2:
                            # Bouton avec le nom du produit
                            if st.button(
                                f"{product_name}",
                                key=f"prod_{measurement_index}_{product_name}",
                                use_container_width=True
                            ):
                                selected_product_name = product_name
                        
                        with col3:
                            # Prix
                            price_text = f"{product_data.get('price', 0):.2f} $"
                            unit_text = product_data.get('price_unit', '')
                            st.markdown(f"**{price_text}**<br><small>{unit_text}</small>", unsafe_allow_html=True)
                        
                        with col4:
                            # Dimensions
                            dimensions = product_data.get('dimensions', {})
                            if dimensions:
                                dims_text = f"{dimensions.get('length', 0)}x{dimensions.get('width', 0)}"
                                if dimensions.get('thickness'):
                                    dims_text += f"x{dimensions.get('thickness')}"
                                st.caption(f"📐 {dims_text}")
                        
                        with col5:
                            # Coût estimé pour cette mesure
                            cost = calculate_measurement_cost(measurement, product_data)
                            if cost > 0:
                                st.caption(f"≈ {cost:.0f}$")
                
                # Si un produit est sélectionné
                if selected_product_name:
                    product_data = products[selected_product_name]
                    
                    # Mettre à jour la mesure
                    measurement['product'] = {
                        'name': selected_product_name,
                        'category': selected_category,
                        'price': product_data.get('price', 0),
                        'price_unit': product_data.get('price_unit', ''),
                        'color': product_data.get('color', '#CCCCCC')
                    }
                    measurement['color'] = product_data.get('color', measurement['color'])
                    
                    # Mettre à jour la sélection globale
                    st.session_state.selected_category = selected_category
                    st.session_state.selected_product = selected_product_name
                    
                    # Mettre à jour dans la liste des mesures
                    st.session_state.current_project['measurements'][measurement_index] = measurement
                    
                    st.success(f"✅ Produit '{selected_product_name}' associé")
                    time.sleep(0.5)
                    st.rerun()
                
                st.divider()
                
                # Options supplémentaires
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🚫 Sans produit", type="secondary", use_container_width=True):
                        st.rerun()
                
                with col2:
                    # Calculer le coût si un produit par défaut est sélectionné
                    if st.session_state.selected_product in products:
                        product_data = products[st.session_state.selected_product]
                        cost = calculate_measurement_cost(measurement, product_data)
                        if cost > 0:
                            st.metric("Coût estimé", f"{cost:.2f} $")
            else:
                st.warning("Aucun produit dans cette catégorie")
                if st.button("Continuer sans produit"):
                    st.rerun()
        else:
            st.error("Aucune catégorie de produits disponible")
            if st.button("Continuer"):
                st.rerun()
    
    # Afficher le dialogue
    product_dialog()

def calculate_measurement_cost(measurement: Dict, product_data: Dict) -> float:
    """Calcule le coût d'une mesure selon le produit"""
    value = measurement.get('value', 0)
    price = product_data.get('price', 0)
    price_unit = product_data.get('price_unit', '')
    
    # Conversion selon l'unité de prix
    if measurement['type'] == 'distance':
        if 'lin' in price_unit.lower() or 'ml' in price_unit.lower():
            return value * price
        elif 'm²' in price_unit or 'pi²' in price_unit:
            # Pour une distance, on pourrait considérer une largeur standard
            width = product_data.get('dimensions', {}).get('width', 1)
            return value * width * price
    
    elif measurement['type'] == 'area':
        if 'm²' in price_unit or 'pi²' in price_unit:
            return value * price
        elif 'unit' in price_unit.lower():
            # Calculer le nombre d'unités nécessaires
            dims = product_data.get('dimensions', {})
            if dims.get('length') and dims.get('width'):
                unit_area = dims['length'] * dims['width']
                units_needed = math.ceil(value / unit_area)
                return units_needed * price
    
    elif measurement['type'] == 'perimeter':
        if 'lin' in price_unit.lower() or 'ml' in price_unit.lower():
            return value * price
    
    return 0

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