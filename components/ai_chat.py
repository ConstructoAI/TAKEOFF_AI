import streamlit as st
from typing import List, Dict
import time

def AIChat(ai_assistant, profile_manager, selected_profile: str, 
          current_project: Dict, chat_history: List[Dict]):
    """Composant de chat avec l'assistant IA"""
    
    # En-tête
    st.subheader("🤖 Assistant IA")
    
    # Profil actif
    profile = profile_manager.get_profile(selected_profile)
    if profile:
        st.info(f"Profil actif: {profile['name']}")
    
    # Zone de chat avec hauteur fixe et scrollbar
    # Créer un conteneur avec hauteur fixe en utilisant CSS
    st.markdown("""
    <style>
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] > [data-testid="stChatMessageContainer"] {
        max-height: 400px;
        overflow-y: auto;
    }
    .chat-container {
        height: 400px;
        overflow-y: auto;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 10px;
        background-color: #f8f9fa;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Conteneur pour l'historique avec hauteur fixe
    chat_container = st.container(height=400)
    
    with chat_container:
        # Afficher l'historique
        for message in chat_history:
            if message['role'] == 'user':
                with st.chat_message("user"):
                    st.write(message['content'])
            else:
                with st.chat_message("assistant"):
                    st.write(message['content'])
    
    # Zone de saisie
    user_input = st.chat_input("Posez votre question...")
    
    if user_input:
        # Ajouter le message utilisateur
        chat_history.append({'role': 'user', 'content': user_input})
        
        # Afficher le message utilisateur
        with st.chat_message("user"):
            st.write(user_input)
        
        # Obtenir la réponse de l'IA
        with st.chat_message("assistant"):
            with st.spinner("Réflexion en cours..."):
                try:
                    # Obtenir le profil complet
                    expert_profile = profile['content'] if profile else ""
                    
                    # Obtenir la réponse
                    response = ai_assistant.get_contextual_response(
                        user_message=user_input,
                        expert_profile=expert_profile,
                        project_context=current_project,
                        max_history=10
                    )
                    
                    # Afficher la réponse
                    st.write(response)
                    
                    # Ajouter à l'historique
                    chat_history.append({'role': 'assistant', 'content': response})
                    
                except Exception as e:
                    error_msg = f"Erreur: {str(e)}"
                    st.error(error_msg)
                    chat_history.append({'role': 'assistant', 'content': error_msg})
        
        # Forcer le rafraîchissement
        st.rerun()
    
    # Actions supplémentaires
    st.divider()
    
    # Boutons d'action
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Analyser PDF", use_container_width=True):
            if current_project.get('pdf_path'):
                with st.spinner("Analyse en cours..."):
                    # Extraire le texte du PDF
                    pdf_text = st.session_state.pdf_processor.get_all_text()
                    
                    if pdf_text:
                        # Limiter la taille
                        if len(pdf_text) > 10000:
                            pdf_text = pdf_text[:10000] + "... [texte tronqué]"
                        
                        # Analyser
                        expert_profile = profile['content'] if profile else ""
                        analysis = ai_assistant.analyze_pdf_content(
                            pdf_text=pdf_text,
                            expert_profile=expert_profile,
                            analysis_type="general"
                        )
                        
                        # Ajouter à l'historique
                        chat_history.append({
                            'role': 'user',
                            'content': "Analyse le contenu du PDF chargé"
                        })
                        chat_history.append({
                            'role': 'assistant',
                            'content': analysis
                        })
                        
                        st.rerun()
                    else:
                        st.warning("Aucun texte trouvé dans le PDF")
            else:
                st.warning("Veuillez d'abord charger un PDF")
    
    with col2:
        if st.button("💡 Suggestions", use_container_width=True):
            with st.spinner("Génération des suggestions..."):
                # Préparer la description du projet
                project_desc = f"Projet avec {len(current_project.get('measurements', []))} mesures"
                if current_project.get('filename'):
                    project_desc += f" sur le fichier {current_project['filename']}"
                
                expert_profile = profile['content'] if profile else ""
                suggestions = ai_assistant.suggest_measurements(
                    project_description=project_desc,
                    expert_profile=expert_profile,
                    existing_measurements=current_project.get('measurements', [])
                )
                
                # Ajouter à l'historique
                chat_history.append({
                    'role': 'user',
                    'content': "Quelles mesures supplémentaires recommandes-tu?"
                })
                chat_history.append({
                    'role': 'assistant',
                    'content': suggestions
                })
                
                st.rerun()
    
    with col3:
        if st.button("🗑️ Effacer chat", use_container_width=True):
            chat_history.clear()
            ai_assistant.clear_history()
            st.success("Historique effacé")
            st.rerun()
    
    # Statistiques
    st.divider()
    
    with st.expander("📊 Statistiques de conversation"):
        st.write(f"Messages: {len(chat_history)}")
        
        user_messages = sum(1 for m in chat_history if m['role'] == 'user')
        ai_messages = sum(1 for m in chat_history if m['role'] == 'assistant')
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Questions", user_messages)
        with col2:
            st.metric("Réponses", ai_messages)
        
        # Résumé de la conversation
        if chat_history:
            st.write("**Derniers échanges:**")
            summary = ai_assistant.get_conversation_summary()
            st.text(summary)