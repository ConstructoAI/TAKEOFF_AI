import streamlit as st
from PIL import Image, ImageDraw
import io
from typing import List, Dict, Optional, Tuple

def PDFViewer(pdf_processor, current_page: int, measurements: List[Dict], 
              selected_tool: str, calibration: Dict):
    """Composant pour afficher et interagir avec les pages PDF"""
    
    # Obtenir l'image de la page
    page_image = pdf_processor.get_page_image(current_page)
    
    if not page_image:
        st.error("Impossible de charger la page PDF")
        return
    
    # Créer une copie pour dessiner
    display_image = page_image.copy()
    draw = ImageDraw.Draw(display_image, 'RGBA')
    
    # Dessiner les mesures existantes
    for measurement in measurements:
        if measurement.get('page') != current_page:
            continue
        
        m_type = measurement.get('type')
        points = measurement.get('points', [])
        color = measurement.get('color', '#FF0000')
        
        if not points:
            continue
        
        # Convertir la couleur hex en RGBA
        color_rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
        color_rgba = color_rgb + (200,)  # Transparence
        
        if m_type == 'distance' and len(points) >= 2:
            # Ligne
            draw.line([tuple(p) for p in points[:2]], fill=color_rgba, width=3)
            # Points
            for point in points[:2]:
                draw.ellipse([point[0]-5, point[1]-5, point[0]+5, point[1]+5], 
                           fill=color_rgba, outline='white')
        
        elif m_type in ['area', 'perimeter'] and len(points) >= 3:
            # Polygone
            if m_type == 'area':
                # Remplir avec transparence
                draw.polygon([tuple(p) for p in points], fill=color_rgba[:3] + (50,), 
                           outline=color_rgba, width=2)
            else:
                # Juste le contour
                for i in range(len(points)):
                    next_i = (i + 1) % len(points)
                    draw.line([tuple(points[i]), tuple(points[next_i])], 
                            fill=color_rgba, width=2)
            
            # Points
            for point in points:
                draw.ellipse([point[0]-4, point[1]-4, point[0]+4, point[1]+4], 
                           fill=color_rgba, outline='white')
        
        elif m_type == 'angle' and len(points) >= 3:
            # Lignes de l'angle
            draw.line([tuple(points[0]), tuple(points[1])], fill=color_rgba, width=2)
            draw.line([tuple(points[1]), tuple(points[2])], fill=color_rgba, width=2)
            
            # Arc pour visualiser l'angle
            # (Simplifié pour Streamlit)
            
            # Points
            for point in points[:3]:
                draw.ellipse([point[0]-4, point[1]-4, point[0]+4, point[1]+4], 
                           fill=color_rgba, outline='white')
        
        # Ajouter le label
        if measurement.get('label'):
            label_text = f"{measurement['label']}: {measurement.get('value', 0):.2f} {measurement.get('unit', '')}"
            # Position du label
            if points:
                label_pos = points[0]
                # Fond blanc semi-transparent pour le texte
                bbox = draw.textbbox(label_pos, label_text)
                draw.rectangle(bbox, fill=(255, 255, 255, 200))
                draw.text(label_pos, label_text, fill='black')
    
    # Afficher l'image
    st.image(display_image, use_container_width=True)
    
    # Zone d'information
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption(f"Outil: {selected_tool.capitalize()}")
    
    with col2:
        st.caption(f"Page: {current_page + 1}")
    
    with col3:
        cal_text = f"Cal: {calibration['value']:.2f} {calibration['unit']}"
        st.caption(cal_text)
    
    # Instructions selon l'outil
    instructions = {
        'distance': "Cliquez pour placer 2 points et mesurer une distance",
        'area': "Cliquez pour créer un polygone et mesurer une surface",
        'perimeter': "Cliquez pour créer une forme et mesurer son périmètre",
        'angle': "Cliquez pour placer 3 points et mesurer un angle",
        'calibration': "Mesurez une distance connue pour calibrer l'échelle"
    }
    
    if selected_tool in instructions:
        st.info(instructions[selected_tool])
    
    # Note: Dans une vraie implémentation Streamlit, l'interaction avec le canvas
    # nécessiterait des composants personnalisés ou streamlit-drawable-canvas