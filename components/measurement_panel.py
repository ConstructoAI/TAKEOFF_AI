import streamlit as st
from typing import List, Dict, Optional

def MeasurementPanel(measurements: List[Dict], selected_tool: str, 
                    selected_product: Optional[str], calibration: Dict,
                    unit_system: str):
    """Panneau pour gérer les mesures"""
    
    # Barre d'outils
    st.subheader("🛠️ Outils de mesure")
    
    # Sélection de l'outil
    tools = {
        'distance': '📏 Distance',
        'area': '⬜ Surface',
        'perimeter': '🔲 Périmètre',
        'angle': '📐 Angle',
        'calibration': '🎯 Calibration'
    }
    
    selected = st.radio(
        "Sélectionner un outil",
        options=list(tools.keys()),
        format_func=lambda x: tools[x],
        horizontal=True,
        key='tool_selector'
    )
    
    if selected != selected_tool:
        st.session_state.selected_tool = selected
        st.rerun()
    
    st.divider()
    
    # Produit sélectionné
    if selected_product:
        st.info(f"📦 Produit actif: {selected_product}")
    else:
        st.warning("⚠️ Aucun produit sélectionné")
    
    st.divider()
    
    # Liste des mesures
    st.subheader("📊 Mesures effectuées")
    
    if not measurements:
        st.info("Aucune mesure effectuée pour le moment")
    else:
        # Grouper par type
        by_type = {}
        for m in measurements:
            m_type = m.get('type', 'unknown')
            if m_type not in by_type:
                by_type[m_type] = []
            by_type[m_type].append(m)
        
        # Options globales d'ordre de dessin
        with st.expander("🎨 Ordre de dessin (DrawOrder)", expanded=False):
            st.info("Utilisez les boutons ↑↓ pour modifier l'ordre d'affichage des mesures. Les mesures avec un ordre plus élevé s'affichent au-dessus.")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Réinitialiser l'ordre", use_container_width=True):
                    # Réinitialiser l'ordre selon l'ordre de création
                    for i, m in enumerate(measurements):
                        m['draw_order'] = i
                    st.success("Ordre réinitialisé")
                    st.rerun()
            
            with col2:
                if st.button("🔃 Inverser l'ordre", use_container_width=True):
                    # Inverser l'ordre actuel
                    orders = [m.get('draw_order', i) for i, m in enumerate(measurements)]
                    orders.reverse()
                    for i, m in enumerate(measurements):
                        m['draw_order'] = orders[i]
                    st.success("Ordre inversé")
                    st.rerun()
            
            with col3:
                if st.button("🧹 Optimiser", use_container_width=True):
                    # Nettoyer et optimiser les ordres (éliminer les trous)
                    sorted_measurements = sorted(measurements, key=lambda m: m.get('draw_order', 0))
                    for i, m in enumerate(sorted_measurements):
                        m['draw_order'] = i
                    st.success("Ordre optimisé")
                    st.rerun()
        
        # Afficher par type
        for m_type, items in by_type.items():
            # Trier les items par draw_order pour affichage cohérent
            items_sorted = sorted(items, key=lambda m: m.get('draw_order', 0))
            with st.expander(f"{m_type.capitalize()} ({len(items_sorted)} mesures)", expanded=True):
                for i, measurement in enumerate(items_sorted):
                    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 1, 1])
                    
                    with col1:
                        # Nom éditable
                        new_label = st.text_input(
                            "Nom",
                            value=measurement.get('label', f"{m_type}_{i+1}"),
                            key=f"label_{m_type}_{i}",
                            label_visibility="collapsed"
                        )
                        if new_label != measurement.get('label'):
                            measurement['label'] = new_label
                    
                    with col2:
                        # Valeur et unité
                        value = measurement.get('value', 0)
                        unit = measurement.get('unit', '')
                        st.text(f"{value:.2f} {unit}")
                    
                    with col3:
                        # Produit associé et ordre de dessin
                        product = measurement.get('product', {})
                        product_name = product.get('name', 'Aucun')
                        draw_order = measurement.get('draw_order', 0)
                        
                        # Bouton pour changer le produit
                        if st.button(f"📦 {product_name}", key=f"change_product_{m_type}_{i}", 
                                   help="Cliquer pour changer le produit"):
                            st.session_state[f'editing_product_{m_type}_{i}'] = True
                        st.caption(f"Ordre: {draw_order}")
                        
                        # Dialogue de sélection de produit
                        if st.session_state.get(f'editing_product_{m_type}_{i}'):
                            show_product_selection_dialog(measurement, i, m_type)
                    
                    with col4:
                        # Contrôles d'ordre de dessin
                        draw_order = measurement.get('draw_order', 0)
                        col4a, col4b, col4c = st.columns(3)
                        
                        with col4a:
                            # Bouton monter (augmenter l'ordre = dessiner plus tard = au-dessus)
                            current_order = measurement.get('draw_order', 0)
                            # Vérifier s'il peut monter
                            higher_orders = [m.get('draw_order', 0) for m in measurements 
                                           if m.get('draw_order', 0) > current_order]
                            can_move_up = len(higher_orders) > 0 or True  # Peut toujours créer un nouveau niveau
                            
                            if st.button("↑", key=f"up_{m_type}_{i}", 
                                       help="Afficher au-dessus",
                                       disabled=not can_move_up):
                                # Augmenter l'ordre de dessin
                                if higher_orders:
                                    next_order = min(higher_orders)
                                    # Échanger avec la mesure suivante
                                    for m in measurements:
                                        if m.get('draw_order', 0) == next_order:
                                            m['draw_order'] = current_order
                                            measurement['draw_order'] = next_order
                                            break
                                else:
                                    # Créer un nouveau niveau au-dessus
                                    max_order = max([m.get('draw_order', 0) for m in measurements], default=0)
                                    measurement['draw_order'] = max_order + 1
                                st.rerun()
                        
                        with col4b:
                            # Bouton descendre (diminuer l'ordre = dessiner plus tôt = en-dessous)
                            current_order = measurement.get('draw_order', 0)
                            # Vérifier s'il peut descendre
                            lower_orders = [m.get('draw_order', 0) for m in measurements 
                                          if m.get('draw_order', 0) < current_order]
                            can_move_down = len(lower_orders) > 0 or current_order > 0
                            
                            if st.button("↓", key=f"down_{m_type}_{i}", 
                                       help="Afficher en-dessous",
                                       disabled=not can_move_down):
                                # Diminuer l'ordre de dessin
                                if lower_orders:
                                    prev_order = max(lower_orders)
                                    # Échanger avec la mesure précédente
                                    for m in measurements:
                                        if m.get('draw_order', 0) == prev_order:
                                            m['draw_order'] = current_order
                                            measurement['draw_order'] = prev_order
                                            break
                                else:
                                    # Créer un nouveau niveau en-dessous
                                    min_order = min([m.get('draw_order', 0) for m in measurements], default=0)
                                    measurement['draw_order'] = min_order - 1
                                st.rerun()
                        
                        with col4c:
                            # Menu pour premier/dernier plan
                            action = st.selectbox(
                                "Plan",
                                options=["", "⬆️ Premier", "⬇️ Dernier"],
                                key=f"plan_{m_type}_{i}",
                                label_visibility="collapsed"
                            )
                            if action == "⬆️ Premier":
                                # Envoyer au premier plan
                                max_order = max([m.get('draw_order', 0) for m in measurements], default=0)
                                measurement['draw_order'] = max_order + 1
                                st.rerun()
                            elif action == "⬇️ Dernier":
                                # Envoyer au dernier plan
                                min_order = min([m.get('draw_order', 0) for m in measurements], default=0)
                                measurement['draw_order'] = min_order - 1
                                st.rerun()
                    
                    with col5:
                        # Bouton supprimer
                        if st.button("🗑️", key=f"del_{m_type}_{i}"):
                            measurements.remove(measurement)
                            st.rerun()
    
    st.divider()
    
    # Statistiques
    st.subheader("📈 Statistiques")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_measurements = len(measurements)
        st.metric("Total mesures", total_measurements)
    
    with col2:
        # Compter les mesures avec produits
        with_product = sum(1 for m in measurements if m.get('product', {}).get('name'))
        st.metric("Avec produit", with_product)
    
    with col3:
        # Pages utilisées
        pages = set(m.get('page', 0) for m in measurements)
        st.metric("Pages", len(pages))
    
    # Actions globales
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Effacer tout", type="secondary", use_container_width=True):
            if st.session_state.get('confirm_clear'):
                measurements.clear()
                st.session_state.confirm_clear = False
                st.success("Toutes les mesures ont été effacées")
                st.rerun()
            else:
                st.session_state.confirm_clear = True
                st.warning("Cliquez à nouveau pour confirmer")
    
    with col2:
        if st.button("💾 Sauvegarder projet", type="primary", use_container_width=True):
            st.info("Fonction de sauvegarde à implémenter")

def show_product_selection_dialog(measurement, measurement_index, measurement_type):
    """Dialogue pour sélectionner/changer le produit d'une mesure"""
    @st.dialog(f"🏷️ Changer le produit - {measurement['label']}")
    def product_dialog():
        # Infos de la mesure
        st.metric(f"{measurement['type'].capitalize()}", 
                  f"{measurement['value']:.2f} {measurement['unit']}")
        
        # Produit actuel
        current_product = measurement.get('product', {})
        if current_product.get('name'):
            st.info(f"Produit actuel: **{current_product['name']}** ({current_product.get('category', 'N/A')})")
        else:
            st.info("Aucun produit actuellement associé")
        
        st.divider()
        
        # Sélection de catégorie
        categories = st.session_state.product_catalog.get_categories()
        
        if categories:
            # Index par défaut basé sur le produit actuel
            default_category_index = 0
            if current_product.get('category') and current_product['category'] in categories:
                default_category_index = categories.index(current_product['category'])
            
            selected_category = st.selectbox(
                "Catégorie",
                options=categories,
                index=default_category_index,
                key=f"cat_change_{measurement_type}_{measurement_index}"
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
                        
                        # Marquer le produit actuel
                        is_current = (current_product.get('name') == product_name and 
                                    current_product.get('category') == selected_category)
                        
                        if st.button(button_text, 
                                   key=f"change_prod_{measurement_type}_{measurement_index}_{product_name}", 
                                   use_container_width=True,
                                   type="primary" if is_current else "secondary"):
                            # Mettre à jour le produit
                            measurement['product'] = {
                                'name': product_name,
                                'category': selected_category,
                                'price': price,
                                'price_unit': unit,
                                'color': color
                            }
                            measurement['color'] = color
                            
                            # Fermer le dialogue
                            st.session_state[f'editing_product_{measurement_type}_{measurement_index}'] = False
                            st.success(f"Produit changé pour: {product_name}")
                            st.rerun()
            else:
                st.warning(f"Aucun produit dans la catégorie {selected_category}")
        else:
            st.warning("Aucune catégorie disponible dans le catalogue")
        
        st.divider()
        
        # Options
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("❌ Retirer le produit", use_container_width=True):
                measurement['product'] = {}
                measurement['color'] = measurement.get('default_color', '#FF0000')
                st.session_state[f'editing_product_{measurement_type}_{measurement_index}'] = False
                st.success("Produit retiré de la mesure")
                st.rerun()
        
        with col2:
            if st.button("🚫 Annuler", use_container_width=True):
                st.session_state[f'editing_product_{measurement_type}_{measurement_index}'] = False
                st.rerun()
    
    product_dialog()

def calculate_measurement_cost(measurement, product_data):
    """Calcule le coût estimé pour une mesure avec un produit"""
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