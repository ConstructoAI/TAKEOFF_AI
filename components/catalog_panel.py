import streamlit as st
from typing import Optional

def CatalogPanel(catalog, selected_category: Optional[str], selected_product: Optional[str]):
    """Panneau pour gérer le catalogue de produits"""
    
    st.subheader("📦 Catalogue de produits")
    
    # Obtenir les catégories
    categories = catalog.get_categories()
    
    if not categories:
        st.warning("Le catalogue est vide. Ajoutez des catégories et produits.")
        
        # Formulaire pour ajouter une catégorie
        with st.form("add_category"):
            st.write("Ajouter une catégorie")
            new_category = st.text_input("Nom de la catégorie")
            if st.form_submit_button("Ajouter"):
                if new_category and catalog.add_category(new_category):
                    catalog.save_catalog()
                    st.success(f"Catégorie '{new_category}' ajoutée")
                    st.rerun()
        return
    
    # Sélection de catégorie
    category = st.selectbox(
        "Catégorie",
        options=categories,
        index=categories.index(selected_category) if selected_category in categories else 0
    )
    
    if category != selected_category:
        st.session_state.selected_category = category
        st.session_state.selected_product = None
        st.rerun()
    
    # Produits de la catégorie
    products = catalog.get_products_by_category(category)
    
    if products:
        st.write(f"**{len(products)} produits dans {category}**")
        
        # Liste des produits
        for product_name, product_data in products.items():
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                # Nom et couleur
                color = product_data.get('color', '#CCCCCC')
                if st.button(
                    f"🎨 {product_name}",
                    key=f"prod_{product_name}",
                    use_container_width=True,
                    help=f"Couleur: {color}"
                ):
                    st.session_state.selected_product = product_name
                    st.success(f"Produit sélectionné: {product_name}")
            
            with col2:
                # Dimensions
                st.text(product_data.get('dimensions', 'N/D'))
            
            with col3:
                # Prix
                price = product_data.get('price', 0)
                unit = product_data.get('price_unit', '')
                st.text(f"{price:.2f}$/{unit}")
            
            with col4:
                # Actions
                if st.button("✏️", key=f"edit_{product_name}"):
                    st.session_state[f'editing_{product_name}'] = True
            
            # Mode édition
            if st.session_state.get(f'editing_{product_name}'):
                with st.form(f"edit_form_{product_name}"):
                    st.write(f"Éditer {product_name}")
                    
                    new_name = st.text_input("Nom", value=product_name)
                    new_dimensions = st.text_input("Dimensions", value=product_data.get('dimensions', ''))
                    new_price = st.number_input("Prix", value=product_data.get('price', 0), min_value=0.0, step=0.01)
                    new_unit = st.text_input("Unité de prix", value=product_data.get('price_unit', 'pi²'))
                    new_color = st.color_picker("Couleur", value=product_data.get('color', '#CCCCCC'))
                    
                    col_save, col_cancel, col_delete = st.columns(3)
                    
                    with col_save:
                        if st.form_submit_button("💾 Sauvegarder", type="primary"):
                            if catalog.update_product(category, product_name, new_name, 
                                                    new_dimensions, new_price, new_unit, new_color):
                                catalog.save_catalog()
                                st.session_state[f'editing_{product_name}'] = False
                                st.success("Produit mis à jour")
                                st.rerun()
                    
                    with col_cancel:
                        if st.form_submit_button("❌ Annuler"):
                            st.session_state[f'editing_{product_name}'] = False
                            st.rerun()
                    
                    with col_delete:
                        if st.form_submit_button("🗑️ Supprimer", type="secondary"):
                            if catalog.delete_product(category, product_name):
                                catalog.save_catalog()
                                st.session_state[f'editing_{product_name}'] = False
                                st.success("Produit supprimé")
                                st.rerun()
    else:
        st.info(f"Aucun produit dans la catégorie {category}")
    
    st.divider()
    
    # Ajouter un nouveau produit
    with st.expander("➕ Ajouter un produit"):
        with st.form("add_product"):
            col1, col2 = st.columns(2)
            
            with col1:
                prod_name = st.text_input("Nom du produit")
                prod_dimensions = st.text_input("Dimensions")
                prod_color = st.color_picker("Couleur", value="#CCCCCC")
            
            with col2:
                prod_price = st.number_input("Prix", min_value=0.0, step=0.01)
                prod_unit = st.text_input("Unité de prix", value="pi²")
            
            if st.form_submit_button("Ajouter le produit"):
                if prod_name and catalog.add_product(category, prod_name, prod_dimensions, 
                                                    prod_price, prod_unit, prod_color):
                    catalog.save_catalog()
                    st.success(f"Produit '{prod_name}' ajouté")
                    st.rerun()
    
    # Actions sur le catalogue
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Exporter
        if st.button("📥 Exporter catalogue", use_container_width=True):
            json_str = catalog.export_catalog_to_string()
            st.download_button(
                "Télécharger JSON",
                json_str,
                "catalogue_produits.json",
                "application/json"
            )
    
    with col2:
        # Importer
        uploaded_catalog = st.file_uploader(
            "Importer catalogue",
            type=['json'],
            key="catalog_upload",
            label_visibility="collapsed"
        )
        if uploaded_catalog:
            if catalog.import_catalog_from_file(uploaded_catalog):
                st.success("Catalogue importé avec succès")
                st.rerun()
    
    with col3:
        # Ajouter une catégorie
        if st.button("➕ Nouvelle catégorie", use_container_width=True):
            st.session_state.show_add_category = True
    
    # Dialogue pour ajouter une catégorie
    if st.session_state.get('show_add_category'):
        with st.form("new_category_form"):
            st.write("Nouvelle catégorie")
            new_cat = st.text_input("Nom de la catégorie")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Ajouter"):
                    if new_cat and catalog.add_category(new_cat):
                        catalog.save_catalog()
                        st.session_state.show_add_category = False
                        st.success(f"Catégorie '{new_cat}' ajoutée")
                        st.rerun()
            
            with col2:
                if st.form_submit_button("Annuler"):
                    st.session_state.show_add_category = False
                    st.rerun()