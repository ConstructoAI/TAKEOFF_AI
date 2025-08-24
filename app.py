import streamlit as st
import os
from datetime import datetime
import json
import pandas as pd
from typing import Dict
from models.profile_manager import ExpertProfileManager
from models.product_catalog import ProductCatalog
from models.ai_assistant import AIAssistant
from utils.pdf_processor import PDFProcessor
from utils.measurement_tools import MeasurementTools
from utils.project_manager import ProjectManager
from components.simple_reactive_viewer import SimpleReactiveViewer
from components.measurement_panel import MeasurementPanel
from components.catalog_panel import CatalogPanel
from components.ai_chat import AIChat

# Configuration de la page
st.set_page_config(
    page_title="TAKEOFF AI - Estimation de Construction",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Charger les styles CSS personnalisés
def load_css():
    """Charge le fichier CSS personnalisé"""
    css_file = "assets/takeoff_styles.css"
    try:
        with open(css_file) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        # CSS de secours si le fichier n'est pas trouvé
        st.markdown("""
        <style>
            :root {
                --primary-color: #3B82F6;
                --primary-light: #93C5FD;
                --primary-lighter: #DBEAFE;
                --primary-darker: #2563EB;
                --bg-primary: #FAFBFF;
                --bg-card: #F5F8FF;
                --text-primary: #1F2937;
                --border-blue: #DBEAFE;
            }
            
            .stApp {
                background-color: var(--bg-primary);
            }
            
            .stButton > button {
                background: linear-gradient(145deg, var(--primary-color) 0%, var(--primary-darker) 100%);
                color: white;
                border: none;
                border-radius: 0.5rem;
                padding: 0.5rem 1rem;
                font-weight: 600;
                transition: all 0.3s ease;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
            
            .stButton > button:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 12px rgba(0, 0, 0, 0.15);
            }
            
            .stTabs [data-baseweb="tab-list"] {
                gap: 2px;
                background: #F8FAFF;
                padding: 4px;
                border-radius: 0.5rem;
            }
            
            .stTabs [aria-selected="true"] {
                background: linear-gradient(145deg, var(--primary-color) 0%, var(--primary-darker) 100%);
                color: white;
            }
            
            section[data-testid="stSidebar"] {
                background: linear-gradient(135deg, #F5F8FF 0%, #FFFFFF 100%);
                border-right: 1px solid var(--border-blue);
            }
            
            [data-testid="metric-container"] {
                background: white;
                padding: 1rem;
                border-radius: 0.5rem;
                border: 1px solid var(--border-blue);
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            }
            
            .stAlert {
                border-radius: 0.5rem;
                animation: fadeIn 0.3s ease;
            }
            
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(10px); }
                to { opacity: 1; transform: translateY(0); }
            }
        </style>
        """, unsafe_allow_html=True)

# Charger les styles
load_css()

# Initialisation de l'état de session
def init_session_state():
    """Initialise les variables de session Streamlit"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.profile_manager = ExpertProfileManager()
        st.session_state.product_catalog = ProductCatalog()
        st.session_state.ai_assistant = None  # Initialisé avec la clé API
        st.session_state.pdf_processor = PDFProcessor()
        st.session_state.measurement_tools = MeasurementTools()
        st.session_state.project_manager = ProjectManager()
        
        # État du projet
        st.session_state.current_project = {
            'filename': None,
            'pdf_path': None,
            'measurements': [],
            'calibration': {'value': 1.0, 'unit': 'cm'},
            'current_page': 0,
            'total_pages': 0
        }
        
        # État de l'interface
        st.session_state.selected_tool = 'distance'
        st.session_state.selected_product = None
        st.session_state.selected_category = None
        st.session_state.show_calibration = False
        st.session_state.chat_history = []
        
        # Paramètres
        st.session_state.unit_system = 'metric'
        st.session_state.snap_enabled = True
        st.session_state.snap_threshold = 10
        st.session_state.show_grid = False

def main():
    """Fonction principale de l'application"""
    init_session_state()
    
    # Menu principal dans la barre latérale
    with st.sidebar:
        st.header("📁 Menu Fichier")
        
        # Nouveau projet
        if st.button("🆕 Nouveau projet", use_container_width=True):
            st.session_state.current_project = {
                'filename': None,
                'pdf_path': None,
                'measurements': [],
                'calibration': {'value': 1.0, 'unit': 'cm'},
                'current_page': 0,
                'total_pages': 0
            }
            st.success("Nouveau projet créé")
            st.rerun()
        
        # Ouvrir projet
        uploaded_project = st.file_uploader(
            "Ouvrir un projet (.tak)",
            type=['tak'],
            key='project_upload'
        )
        
        if uploaded_project:
            # Sauvegarder temporairement
            temp_path = os.path.join("temp", uploaded_project.name)
            os.makedirs("temp", exist_ok=True)
            
            with open(temp_path, "wb") as f:
                f.write(uploaded_project.getbuffer())
            
            # Charger le projet
            project_data = st.session_state.project_manager.load_project(temp_path)
            if project_data:
                st.session_state.current_project.update(project_data)
                st.success(f"Projet {uploaded_project.name} chargé")
                st.rerun()
        
        # Sauvegarder projet
        if st.button("💾 Sauvegarder projet", use_container_width=True):
            if st.session_state.current_project['filename']:
                # Préparer les données
                save_data = st.session_state.current_project.copy()
                
                # Nom de fichier
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"projet_{timestamp}.tak"
                
                # Convertir en JSON
                json_str = json.dumps(save_data, indent=2, ensure_ascii=False)
                
                # Bouton de téléchargement
                st.download_button(
                    label="📥 Télécharger le projet",
                    data=json_str,
                    file_name=filename,
                    mime="application/json"
                )
            else:
                st.warning("Aucun projet actif à sauvegarder")
        
        st.divider()
        
        # Projets récents
        st.subheader("📋 Projets récents")
        recent_projects = st.session_state.project_manager.get_recent_projects()
        
        if recent_projects:
            for project_path in recent_projects[:5]:
                project_name = os.path.basename(project_path)
                if st.button(f"📄 {project_name}", key=f"recent_{project_path}"):
                    project_data = st.session_state.project_manager.load_project(project_path)
                    if project_data:
                        st.session_state.current_project.update(project_data)
                        st.success(f"Projet {project_name} chargé")
                        st.rerun()
        else:
            st.info("Aucun projet récent")
        
        st.divider()
    
    # Header principal avec style moderne
    st.markdown("""
    <div class="main-header" style="
        background: linear-gradient(145deg, rgba(255, 255, 255, 0.3) 0%, #3B82F6 15%, #1F2937 85%, rgba(0, 0, 0, 0.4) 100%);
        padding: 25px 30px;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 8px 24px rgba(31, 41, 55, 0.35), inset 0 2px 0 rgba(255, 255, 255, 0.3), inset 0 -2px 0 rgba(0, 0, 0, 0.2);
        position: relative;
        overflow: hidden;
    ">
        <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.6);">
            🏗️ TAKEOFF AI
        </h1>
        <p style="margin-top: 12px; margin-bottom: 0; font-size: 1.1rem; color: rgba(255, 255, 255, 0.95); text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);">
            Système d'estimation de construction avec Intelligence Artificielle
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Barre latérale pour les paramètres et informations
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Clé API (sécurisée)
        api_key = st.text_input(
            "Clé API",
            type="password",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            help="Entrez votre clé API Anthropic"
        )
        
        if api_key and not st.session_state.ai_assistant:
            st.session_state.ai_assistant = AIAssistant(api_key)
            st.success("✅ Assistant IA connecté")
        
        st.divider()
        
        # Profil expert
        st.subheader("👤 Profil Expert")
        profiles = st.session_state.profile_manager.get_profiles()
        # Trier les profils par ordre alphabétique français des noms (avec support des accents)
        import locale
        import unicodedata
        
        def normalize_for_sorting(text):
            """Normalise le texte pour le tri alphabétique français"""
            # Convertir en majuscules et normaliser les accents pour le tri
            # NFD décompose les caractères accentués, puis on garde juste les caractères de base
            return ''.join(
                c for c in unicodedata.normalize('NFD', text.upper())
                if unicodedata.category(c) != 'Mn'  # Mn = Mark, Nonspacing (accents)
            )
        
        sorted_profile_keys = sorted(
            profiles.keys(), 
            key=lambda x: normalize_for_sorting(profiles[x]['name'])
        )
        selected_profile = st.selectbox(
            "Sélectionner un profil",
            options=sorted_profile_keys,
            format_func=lambda x: profiles[x]['name']
        )
        
        st.divider()
        
        # Paramètres d'unités
        st.subheader("📏 Unités")
        st.session_state.unit_system = st.radio(
            "Système d'unités",
            options=['metric', 'imperial'],
            format_func=lambda x: 'Métrique' if x == 'metric' else 'Impérial'
        )
        
        st.divider()
        
        # Options d'accrochage
        st.subheader("🎯 Accrochage")
        st.session_state.snap_enabled = st.checkbox(
            "Activer l'accrochage",
            value=st.session_state.snap_enabled
        )
        
        if st.session_state.snap_enabled:
            st.session_state.snap_threshold = st.slider(
                "Seuil d'accrochage (pixels)",
                min_value=5,
                max_value=50,
                value=st.session_state.snap_threshold
            )
        
        st.divider()
        
        # Informations du projet
        if st.session_state.current_project['filename']:
            st.subheader("📄 Projet actuel")
            st.text(f"Fichier: {st.session_state.current_project['filename']}")
            st.text(f"Page: {st.session_state.current_project['current_page'] + 1}/{st.session_state.current_project['total_pages']}")
            st.text(f"Mesures: {len(st.session_state.current_project['measurements'])}")
    
    # Section supérieure avec outils et assistant IA
    col_tools, col_ai = st.columns([5, 4])
    
    # Colonne des outils et mesures
    with col_tools:
        st.header("🛠️ Outils et Mesures")
        
        # Onglets
        tab_measures, tab_catalog, tab_totals, tab_options = st.tabs([
            "📐 Mesures", "📦 Catalogue", "📊 Totaux", "⚙️ Options"
        ])
        
        with tab_measures:
            MeasurementPanel(
                measurements=st.session_state.current_project['measurements'],
                selected_tool=st.session_state.selected_tool,
                selected_product=st.session_state.selected_product,
                calibration=st.session_state.current_project['calibration'],
                unit_system=st.session_state.unit_system
            )
        
        with tab_catalog:
            CatalogPanel(
                catalog=st.session_state.product_catalog,
                selected_category=st.session_state.selected_category,
                selected_product=st.session_state.selected_product
            )
        
        with tab_totals:
            st.subheader("📊 Totaux par Produit")
            if st.session_state.current_project['measurements']:
                # Calculer les totaux
                totals = st.session_state.measurement_tools.calculate_totals(
                    st.session_state.current_project['measurements'],
                    st.session_state.product_catalog
                )
                
                # Afficher le tableau
                if totals:
                    df = pd.DataFrame(totals)
                    st.dataframe(df, use_container_width=True)
                    
                    # Calculer et afficher le total général
                    grand_total = 0.0
                    for row in totals:
                        # Extraire le montant du prix total (format: "123.45$")
                        prix_total_str = row.get('Prix total', 'N/D')
                        if prix_total_str != 'N/D' and '$' in prix_total_str:
                            try:
                                montant = float(prix_total_str.replace('$', '').strip())
                                grand_total += montant
                            except:
                                pass
                    
                    # Afficher le total général avec style
                    st.divider()
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col3:
                        st.metric(
                            label="💰 Total Général",
                            value=f"{grand_total:.2f}$",
                            help="Somme de tous les prix totaux"
                        )
                    
                    st.divider()
                    
                    # Options d'export
                    col1, col2 = st.columns(2)
                    with col1:
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "📥 Télécharger CSV",
                            csv,
                            "totaux_produits.csv",
                            "text/csv"
                        )
                    with col2:
                        json_str = df.to_json(orient='records')
                        st.download_button(
                            "📥 Télécharger JSON",
                            json_str,
                            "totaux_produits.json",
                            "application/json"
                        )
                else:
                    st.info("Aucun produit associé aux mesures")
            else:
                st.info("Aucune mesure effectuée")
        
        with tab_options:
            st.subheader("⚙️ Options d'Affichage")
            
            # Options de visualisation
            col1, col2 = st.columns(2)
            
            with col1:
                st.session_state.show_grid = st.checkbox(
                    "Afficher la grille",
                    value=st.session_state.show_grid
                )
                
                st.session_state.show_detected_lines = st.checkbox(
                    "Afficher les lignes détectées",
                    value=st.session_state.get('show_detected_lines', False)
                )
            
            with col2:
                if st.button("🔍 Extraire les lignes du PDF"):
                    if st.session_state.current_project['pdf_path']:
                        with st.spinner("Extraction des lignes..."):
                            lines = st.session_state.pdf_processor.extract_lines(
                                st.session_state.current_project['current_page']
                            )
                            st.success(f"{len(lines)} lignes détectées")
                            st.session_state.show_detected_lines = True
                            st.rerun()
            
            st.divider()
            
            # Options d'export
            st.subheader("📤 Export")
            
            export_format = st.selectbox(
                "Format d'export",
                options=['CSV', 'TXT', 'JSON'],
                key='export_format'
            )
            
            if st.button("📥 Exporter les données", use_container_width=True):
                if st.session_state.current_project['measurements']:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    if export_format == 'CSV':
                        # Export CSV
                        csv_data = []
                        for m in st.session_state.current_project['measurements']:
                            product = m.get('product', {})
                            csv_data.append({
                                'Type': m.get('type', ''),
                                'Nom': m.get('label', ''),
                                'Valeur': f"{m.get('value', 0):.2f}",
                                'Unité': m.get('unit', ''),
                                'Page': m.get('page', 0) + 1,
                                'Produit': product.get('name', ''),
                                'Catégorie': product.get('category', ''),
                                'Prix unitaire': f"{product.get('price', 0):.2f}"
                            })
                        
                        df = pd.DataFrame(csv_data)
                        csv = df.to_csv(index=False)
                        
                        st.download_button(
                            "📥 Télécharger CSV",
                            csv,
                            f"mesures_{timestamp}.csv",
                            "text/csv"
                        )
                    
                    elif export_format == 'TXT':
                        # Export TXT
                        txt_content = "RAPPORT D'ESTIMATION - TAKEOFF AI\n"
                        txt_content += "=" * 60 + "\n\n"
                        txt_content += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
                        txt_content += f"Nombre de mesures: {len(st.session_state.current_project['measurements'])}\n\n"
                        
                        # Mesures par type
                        by_type = {}
                        for m in st.session_state.current_project['measurements']:
                            m_type = m.get('type', 'unknown')
                            if m_type not in by_type:
                                by_type[m_type] = []
                            by_type[m_type].append(m)
                        
                        for m_type, items in by_type.items():
                            txt_content += f"\n{m_type.upper()} ({len(items)} mesures)\n"
                            for m in items:
                                txt_content += f"- {m.get('label')}: {m.get('value', 0):.2f} {m.get('unit', '')}\n"
                        
                        st.download_button(
                            "📥 Télécharger TXT",
                            txt_content,
                            f"rapport_{timestamp}.txt",
                            "text/plain"
                        )
                    
                    elif export_format == 'JSON':
                        # Export JSON
                        json_data = {
                            'project': st.session_state.current_project,
                            'export_date': datetime.now().isoformat()
                        }
                        json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
                        
                        st.download_button(
                            "📥 Télécharger JSON",
                            json_str,
                            f"export_{timestamp}.json",
                            "application/json"
                        )
                else:
                    st.warning("Aucune mesure à exporter")
            
            st.divider()
            
            # Couleurs des mesures
            st.subheader("🎨 Couleurs des Mesures")
            
            # Information sur la transparence
            st.info("💡 Les mesures utilisent des niveaux de transparence optimisés :\n"
                   "• **Surfaces** : Très transparentes (80/255)\n"
                   "• **Périmètres** : Semi-transparents (120/255)\n"
                   "• **Distances & Angles** : Plus opaques (180/255)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.color_picker("Distance", value="#FF0000", key="color_distance")
                st.color_picker("Surface", value="#00FF00", key="color_area")
                st.color_picker("Périmètre", value="#0000FF", key="color_perimeter")
            
            with col2:
                st.color_picker("Angle", value="#FF00FF", key="color_angle")
                st.color_picker("Calibration", value="#FFA500", key="color_calibration")
                st.color_picker("Sélection", value="#FFFF00", key="color_selection")
            
            # Option pour ajuster la transparence globale
            st.divider()
            st.subheader("🔍 Transparence")
            transparency_adjustment = st.slider(
                "Ajustement global de transparence",
                min_value=-50,
                max_value=50,
                value=0,
                help="Ajuster la transparence de toutes les mesures"
            )
            st.session_state.transparency_adjustment = transparency_adjustment
    
    # Colonne de l'assistant IA
    with col_ai:
        st.header("🤖 Assistant IA")
        
        if st.session_state.ai_assistant:
            AIChat(
                ai_assistant=st.session_state.ai_assistant,
                profile_manager=st.session_state.profile_manager,
                selected_profile=selected_profile,
                current_project=st.session_state.current_project,
                chat_history=st.session_state.chat_history
            )
        else:
            st.warning("""🔑 **Clé API requise**

Veuillez saisir votre clé API dans la barre latérale pour commencer à utiliser EXPERTS IA.

Pour obtenir une clé API, contactez-nous :
📧 info@constructoai.ca
📱 (514) 820-1972""")
    
    # Séparateur avant le PDF
    st.divider()
    
    # Section PDF en bas sur toute la largeur
    st.header("📄 Document PDF")
    
    # Contrôles du PDF
    col1, col2, col3, col4 = st.columns([2, 3, 3, 2])
    
    with col1:
        # Upload de fichier
        uploaded_file = st.file_uploader(
            "Charger un PDF",
            type=['pdf'],
            help="Sélectionnez un fichier PDF à analyser"
        )
    
    with col2:
        # Navigation si PDF chargé
        if st.session_state.current_project['pdf_path']:
            col_prev, col_page, col_next = st.columns([1, 3, 1])
            
            with col_prev:
                if st.button("◀", disabled=st.session_state.current_project['current_page'] == 0):
                    st.session_state.current_project['current_page'] -= 1
                    st.rerun()
            
            with col_page:
                page_num = st.number_input(
                    "Page",
                    min_value=1,
                    max_value=st.session_state.current_project['total_pages'],
                    value=st.session_state.current_project['current_page'] + 1,
                    label_visibility="collapsed"
                ) - 1
                if page_num != st.session_state.current_project['current_page']:
                    st.session_state.current_project['current_page'] = page_num
                    st.rerun()
            
            with col_next:
                if st.button("▶", disabled=st.session_state.current_project['current_page'] >= st.session_state.current_project['total_pages'] - 1):
                    st.session_state.current_project['current_page'] += 1
                    st.rerun()
    
    with col3:
        # Statut du PDF
        if st.session_state.current_project['filename']:
            st.info(f"📄 {st.session_state.current_project['filename']} - Page {st.session_state.current_project['current_page'] + 1}/{st.session_state.current_project['total_pages']}")
    
    with col4:
        # Calibration actuelle
        cal = st.session_state.current_project['calibration']
        st.info(f"📏 Cal: {cal['value']:.3f} {cal['unit']}")
    
    # Traitement de l'upload
    if uploaded_file:
        # Sauvegarder temporairement le fichier
        temp_path = os.path.join("temp", uploaded_file.name)
        os.makedirs("temp", exist_ok=True)
        
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Charger le PDF si nouveau
        if st.session_state.current_project['pdf_path'] != temp_path:
            st.session_state.current_project['pdf_path'] = temp_path
            st.session_state.current_project['filename'] = uploaded_file.name
            st.session_state.pdf_processor.load_pdf(temp_path)
            st.session_state.current_project['total_pages'] = st.session_state.pdf_processor.get_page_count()
            st.session_state.current_project['current_page'] = 0
    
    # Afficher le PDF si chargé
    if st.session_state.current_project['pdf_path']:
        # Extraire les lignes si activé
        detected_lines = None
        if st.session_state.get('show_detected_lines', False):
            detected_lines = st.session_state.pdf_processor.extract_lines(
                st.session_state.current_project['current_page']
            )
        
        # Visualiseur PDF simplifié et réactif
        SimpleReactiveViewer(
            pdf_processor=st.session_state.pdf_processor,
            current_page=st.session_state.current_project['current_page'],
            measurements=st.session_state.current_project['measurements'],
            selected_tool=st.session_state.selected_tool,
            calibration=st.session_state.current_project['calibration'],
            detected_lines=detected_lines
        )
        
        # Gérer le dialogue produit après mesure
        if 'temp_measurement' in st.session_state and st.session_state.temp_measurement:
            show_product_association_dialog(
                st.session_state.temp_measurement,
                st.session_state.temp_measurement_index
            )
            # Réinitialiser après affichage
            st.session_state.temp_measurement = None
            st.session_state.temp_measurement_index = None
        
        # Gérer le dialogue de calibration
        if st.session_state.get('show_calibration_dialog', False):
            @st.dialog("🎯 Calibration")
            def calibration_dialog():
                pixel_dist = st.session_state.get('calibration_distance', 0)
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
                    st.session_state.show_calibration_dialog = False
                    st.rerun()
            
            calibration_dialog()
    else:
        st.info("👆 Chargez un fichier PDF pour commencer")
    
    # Barre de statut tout en bas
    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Outil actif", st.session_state.selected_tool.capitalize())
    
    with col2:
        if st.session_state.selected_product:
            st.metric("Produit", st.session_state.selected_product)
        else:
            st.metric("Produit", "Aucun")
    
    with col3:
        cal_value = st.session_state.current_project['calibration']['value']
        cal_unit = st.session_state.current_project['calibration']['unit']
        st.metric("Calibration", f"{cal_value:.2f} {cal_unit}")
    
    with col4:
        st.metric("Système", "Métrique" if st.session_state.unit_system == 'metric' else "Impérial")
    
    # Crédit du développeur
    st.markdown("""
    <div style="text-align: center; padding: 1rem; color: #6B7280; font-size: 0.875rem;">
        © 2025 Constructo AI - Développé par Sylvain Leduc</strong>
    </div>
    """, unsafe_allow_html=True)

def show_product_association_dialog(measurement: Dict, measurement_index: int):
    """Dialogue pour associer un produit à la mesure"""
    @st.dialog(f"🏷️ Produit pour {measurement['label']}")
    def product_dialog():
        # Infos de la mesure
        st.metric(f"{measurement['type'].capitalize()}", 
                  f"{measurement['value']:.2f} {measurement['unit']}")
        
        st.divider()
        
        # Si un produit est déjà sélectionné, proposer de l'utiliser
        if st.session_state.selected_product and st.session_state.selected_category:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"📦 Produit actif: **{st.session_state.selected_product}**")
            with col2:
                if st.button("Utiliser", type="primary"):
                    # Récupérer les infos du produit
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
                        st.session_state.current_project['measurements'][measurement_index] = measurement
                    st.rerun()
            
            st.caption("Ou choisir un autre produit ci-dessous")
        
        # Sélection de catégorie
        categories = st.session_state.product_catalog.get_categories()
        
        if categories:
            selected_category = st.selectbox(
                "Catégorie",
                options=categories,
                index=categories.index(st.session_state.selected_category) if st.session_state.selected_category in categories else 0,
                key=f"cat_dialog_{measurement_index}"
            )
            
            # Produits de la catégorie
            products = st.session_state.product_catalog.get_products_by_category(selected_category)
            
            if products:
                # Afficher les produits en grille
                cols = st.columns(2)
                for i, (product_name, product_data) in enumerate(products.items()):
                    with cols[i % 2]:
                        color = product_data.get('color', '#CCCCCC')
                        price = product_data.get('price', 0)
                        unit = product_data.get('price_unit', '')
                        
                        # Calculer le coût estimé
                        cost = calculate_measurement_cost(measurement, product_data)
                        cost_text = f" ≈ {cost:.0f}$" if cost > 0 else ""
                        
                        # Bouton avec toutes les infos
                        button_text = f"{product_name}\n{price:.2f}$/{unit}{cost_text}"
                        
                        if st.button(button_text, key=f"prod_{measurement_index}_{product_name}", 
                                   use_container_width=True):
                            measurement['product'] = {
                                'name': product_name,
                                'category': selected_category,
                                'price': price,
                                'price_unit': unit,
                                'color': color
                            }
                            measurement['color'] = color
                            st.session_state.selected_category = selected_category
                            st.session_state.selected_product = product_name
                            st.session_state.current_project['measurements'][measurement_index] = measurement
                            st.rerun()
        
        st.divider()
        
        if st.button("Sans produit", use_container_width=True):
            st.rerun()
    
    product_dialog()

def calculate_measurement_cost(measurement: Dict, product_data: Dict) -> float:
    """Calcule le coût estimé"""
    value = measurement.get('value', 0)
    price = product_data.get('price', 0)
    price_unit = product_data.get('price_unit', '')
    
    if measurement['type'] == 'distance':
        if 'lin' in price_unit.lower() or 'ml' in price_unit.lower():
            return value * price
    elif measurement['type'] == 'area':
        if 'm²' in price_unit or 'pi²' in price_unit:
            return value * price
    elif measurement['type'] == 'perimeter':
        if 'lin' in price_unit.lower() or 'ml' in price_unit.lower():
            return value * price
    
    return 0

if __name__ == "__main__":
    main()