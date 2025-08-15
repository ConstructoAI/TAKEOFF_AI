import streamlit as st
from PIL import Image
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Optional, Tuple
import numpy as np

def create_interactive_pdf_plot(image: Image.Image, measurements: List[Dict], 
                               selected_tool: str, zoom_level: float = 1.0):
    """Crée un graphique Plotly interactif avec l'image PDF"""
    
    # Convertir l'image PIL en array numpy
    img_array = np.array(image)
    
    # Créer la figure Plotly
    fig = go.Figure()
    
    # Ajouter l'image comme fond
    fig.add_layout_image(
        dict(
            source=image,
            xref="x",
            yref="y",
            x=0,
            y=img_array.shape[0],
            sizex=img_array.shape[1],
            sizey=img_array.shape[0],
            sizing="stretch",
            opacity=1,
            layer="below"
        )
    )
    
    # Configurer les axes
    fig.update_xaxes(
        showgrid=False,
        zeroline=False,
        range=[0, img_array.shape[1]],
        constrain='domain'
    )
    
    fig.update_yaxes(
        showgrid=False,
        zeroline=False,
        range=[img_array.shape[0], 0],  # Inverser Y pour que 0 soit en haut
        scaleanchor="x",
        constrain='domain'
    )
    
    # Ajouter les mesures existantes
    for measurement in measurements:
        if measurement.get('type') == 'distance' and len(measurement.get('points', [])) >= 2:
            points = measurement['points']
            color = measurement.get('color', '#FF0000')
            
            # Ligne
            fig.add_trace(go.Scatter(
                x=[points[0][0], points[1][0]],
                y=[points[0][1], points[1][1]],
                mode='lines+markers+text',
                line=dict(color=color, width=3),
                marker=dict(size=10, color=color),
                text=['', f"{measurement.get('label', '')}: {measurement.get('value', 0):.2f} {measurement.get('unit', '')}"],
                textposition="top center",
                showlegend=False,
                hovertemplate='X: %{x}<br>Y: %{y}<extra></extra>'
            ))
    
    # Configurer la mise en page
    fig.update_layout(
        title=f"Mode : {selected_tool.capitalize()} - Cliquez sur l'image pour placer des points",
        showlegend=False,
        hovermode='closest',
        dragmode='pan',
        height=int(600 * zoom_level),
        margin=dict(l=0, r=0, t=30, b=0),
        plot_bgcolor='white'
    )
    
    return fig

def InteractiveMeasurePanel(pdf_processor, current_page: int, measurements: List[Dict],
                           selected_tool: str, calibration: Dict):
    """Panneau de mesure interactif utilisant Plotly"""
    
    # Contrôle du zoom
    zoom = st.slider("🔍 Zoom", 0.5, 3.0, 1.0, 0.1)
    
    # Obtenir l'image
    page_image = pdf_processor.get_page_image(current_page, zoom=zoom)
    
    if not page_image:
        st.error("Impossible de charger la page PDF")
        return
    
    # Créer le graphique interactif
    fig = create_interactive_pdf_plot(page_image, measurements, selected_tool, zoom)
    
    # Configuration Plotly
    config = {
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['select2d', 'lasso2d'],
        'toImageButtonOptions': {
            'format': 'png',
            'filename': f'page_{current_page}_mesures',
            'height': None,
            'width': None,
            'scale': 1
        }
    }
    
    # Afficher le graphique
    click_data = st.plotly_chart(fig, use_container_width=True, config=config, key=f"plot_{current_page}")
    
    # Gérer les clics
    if 'clicked_points' not in st.session_state:
        st.session_state.clicked_points = []
    
    # Instructions
    with st.expander("📝 Instructions", expanded=True):
        if selected_tool == 'distance':
            st.info("Cliquez sur 2 points pour mesurer une distance")
            
            # Afficher les points cliqués
            if st.session_state.clicked_points:
                st.write("Points sélectionnés :")
                for i, point in enumerate(st.session_state.clicked_points):
                    st.write(f"Point {i+1}: X={point[0]:.0f}, Y={point[1]:.0f}")
                
                if len(st.session_state.clicked_points) >= 2:
                    # Calculer et ajouter la mesure
                    if st.button("✅ Valider la mesure"):
                        import math
                        p1, p2 = st.session_state.clicked_points[:2]
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
                        
                        measurements.append(measurement)
                        st.session_state.clicked_points = []
                        st.success(f"Mesure ajoutée : {measurement['value']:.2f} {measurement['unit']}")
                        st.rerun()
            
            if st.button("🔄 Réinitialiser"):
                st.session_state.clicked_points = []
                st.rerun()
    
    # Zone de saisie manuelle alternative
    with st.expander("⌨️ Saisie manuelle des coordonnées"):
        col1, col2 = st.columns(2)
        
        with col1:
            x1 = st.number_input("X1", value=0)
            y1 = st.number_input("Y1", value=0)
        
        with col2:
            x2 = st.number_input("X2", value=100)
            y2 = st.number_input("Y2", value=100)
        
        if st.button("Ajouter avec coordonnées manuelles"):
            import math
            pixel_distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            
            measurement = {
                'type': 'distance',
                'points': [(x1, y1), (x2, y2)],
                'page': current_page,
                'value': pixel_distance * calibration.get('value', 1.0),
                'unit': calibration.get('unit', 'cm'),
                'label': f"Distance_{len(measurements) + 1}",
                'color': '#FF0000'
            }
            
            measurements.append(measurement)
            st.success(f"Mesure ajoutée : {measurement['value']:.2f} {measurement['unit']}")
            st.rerun()