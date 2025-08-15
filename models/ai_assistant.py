import os
from typing import List, Dict, Optional
from anthropic import Anthropic
import json

class AIAssistant:
    """Assistant IA utilisant l'API Claude d'Anthropic"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialise l'assistant avec une clé API
        
        Args:
            api_key: Clé API Anthropic (si None, cherche dans les variables d'environnement)
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        
        if not self.api_key:
            raise ValueError("Clé API Anthropic requise. Définissez ANTHROPIC_API_KEY ou passez la clé en paramètre.")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = "claude-opus-4-20250514"
        self.conversation_history = []
    
    def clear_history(self):
        """Efface l'historique de conversation"""
        self.conversation_history = []
    
    def add_to_history(self, role: str, content: str):
        """Ajoute un message à l'historique"""
        self.conversation_history.append({
            'role': role,
            'content': content
        })
    
    def get_contextual_response(self, 
                              user_message: str,
                              expert_profile: str,
                              project_context: Dict,
                              max_history: int = 10) -> str:
        """
        Obtient une réponse contextuelle de l'IA
        
        Args:
            user_message: Message de l'utilisateur
            expert_profile: Profil d'expert à utiliser
            project_context: Contexte du projet (mesures, etc.)
            max_history: Nombre maximum de messages d'historique à inclure
        
        Returns:
            Réponse de l'IA
        """
        try:
            # Préparer le contexte du projet
            context_info = self._prepare_project_context(project_context)
            
            # Construire le prompt système
            system_prompt = f"""{expert_profile}

CONTEXTE DU PROJET ACTUEL:
{context_info}

INSTRUCTIONS:
- Réponds de manière professionnelle et précise
- Utilise le contexte du projet pour des réponses pertinentes
- Reste dans ton domaine d'expertise
- Fournis des conseils pratiques et applicables
- Si tu as besoin de plus d'informations, demande-les clairement
"""
            
            # Préparer les messages
            messages = []
            
            # Ajouter l'historique récent
            history_start = max(0, len(self.conversation_history) - max_history)
            for msg in self.conversation_history[history_start:]:
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })
            
            # Ajouter le nouveau message
            messages.append({
                'role': 'user',
                'content': user_message
            })
            
            # Appeler l'API Claude
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.7,
                system=system_prompt,
                messages=messages
            )
            
            # Extraire la réponse
            ai_response = response.content[0].text
            
            # Ajouter à l'historique
            self.add_to_history('user', user_message)
            self.add_to_history('assistant', ai_response)
            
            return ai_response
            
        except Exception as e:
            return f"Erreur lors de la communication avec l'assistant IA: {str(e)}"
    
    def analyze_pdf_content(self, 
                          pdf_text: str,
                          expert_profile: str,
                          analysis_type: str = "general") -> str:
        """
        Analyse le contenu textuel d'un PDF
        
        Args:
            pdf_text: Texte extrait du PDF
            expert_profile: Profil d'expert à utiliser
            analysis_type: Type d'analyse (general, measurements, materials, etc.)
        
        Returns:
            Analyse de l'IA
        """
        try:
            # Limiter la taille du texte si nécessaire
            max_chars = 10000
            if len(pdf_text) > max_chars:
                pdf_text = pdf_text[:max_chars] + "... [texte tronqué]"
            
            # Construire le prompt selon le type d'analyse
            analysis_prompts = {
                "general": "Analyse ce document et fournis un résumé des éléments importants pour un projet de construction.",
                "measurements": "Identifie toutes les mesures, dimensions et quantités mentionnées dans ce document.",
                "materials": "Liste tous les matériaux, produits et équipements mentionnés avec leurs spécifications.",
                "costs": "Extrais toutes les informations de coûts, prix et budget présentes dans le document."
            }
            
            prompt = f"""{expert_profile}

DOCUMENT À ANALYSER:
{pdf_text}

INSTRUCTION:
{analysis_prompts.get(analysis_type, analysis_prompts['general'])}

Fournis une analyse structurée et professionnelle.
"""
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.5,
                system=prompt,
                messages=[{
                    'role': 'user',
                    'content': 'Analyse le document ci-dessus selon les instructions.'
                }]
            )
            
            return response.content[0].text
            
        except Exception as e:
            return f"Erreur lors de l'analyse du PDF: {str(e)}"
    
    def suggest_measurements(self,
                           project_description: str,
                           expert_profile: str,
                           existing_measurements: List[Dict]) -> str:
        """
        Suggère des mesures pertinentes pour le projet
        
        Args:
            project_description: Description du projet
            expert_profile: Profil d'expert à utiliser
            existing_measurements: Mesures déjà effectuées
        
        Returns:
            Suggestions de l'IA
        """
        try:
            # Formater les mesures existantes
            measurements_text = ""
            if existing_measurements:
                measurements_text = "MESURES DÉJÀ EFFECTUÉES:\n"
                for i, m in enumerate(existing_measurements, 1):
                    measurements_text += f"{i}. {m.get('label', 'Sans nom')} - "
                    measurements_text += f"Type: {m.get('type', 'inconnu')} - "
                    measurements_text += f"Valeur: {m.get('value', 0):.2f} {m.get('unit', '')}\n"
            
            prompt = f"""{expert_profile}

DESCRIPTION DU PROJET:
{project_description}

{measurements_text}

INSTRUCTION:
En te basant sur la description du projet et les mesures existantes, suggère les mesures supplémentaires qui seraient nécessaires pour compléter l'estimation. Pour chaque suggestion, explique pourquoi elle est importante et comment l'effectuer correctement.

Organise tes suggestions par priorité et par type de travaux.
"""
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                temperature=0.6,
                system=prompt,
                messages=[{
                    'role': 'user',
                    'content': 'Quelles mesures supplémentaires recommandes-tu?'
                }]
            )
            
            return response.content[0].text
            
        except Exception as e:
            return f"Erreur lors de la génération des suggestions: {str(e)}"
    
    def _prepare_project_context(self, project_context: Dict) -> str:
        """Prépare le contexte du projet pour l'IA"""
        context_parts = []
        
        # Informations sur le fichier
        if project_context.get('filename'):
            context_parts.append(f"Fichier: {project_context['filename']}")
        
        # Calibration
        if project_context.get('calibration'):
            cal = project_context['calibration']
            context_parts.append(f"Calibration: {cal['value']} {cal['unit']}")
        
        # Mesures
        measurements = project_context.get('measurements', [])
        if measurements:
            context_parts.append(f"\nNombre de mesures: {len(measurements)}")
            
            # Grouper par type
            by_type = {}
            for m in measurements:
                m_type = m.get('type', 'inconnu')
                if m_type not in by_type:
                    by_type[m_type] = []
                by_type[m_type].append(m)
            
            context_parts.append("\nMesures par type:")
            for m_type, items in by_type.items():
                context_parts.append(f"- {m_type.capitalize()}: {len(items)} mesures")
                
                # Afficher quelques exemples
                for item in items[:3]:
                    label = item.get('label', 'Sans nom')
                    value = item.get('value', 0)
                    unit = item.get('unit', '')
                    product = item.get('product', {})
                    product_name = product.get('name', 'Aucun produit')
                    
                    context_parts.append(f"  • {label}: {value:.2f} {unit} ({product_name})")
                
                if len(items) > 3:
                    context_parts.append(f"  • ... et {len(items) - 3} autres")
        else:
            context_parts.append("Aucune mesure effectuée pour le moment")
        
        return "\n".join(context_parts)
    
    def get_conversation_summary(self) -> str:
        """Retourne un résumé de la conversation"""
        if not self.conversation_history:
            return "Aucune conversation en cours"
        
        summary_parts = [f"Conversation avec {len(self.conversation_history)} messages:"]
        
        for i, msg in enumerate(self.conversation_history[-6:]):  # Derniers 6 messages
            role = "Utilisateur" if msg['role'] == 'user' else "Assistant"
            content = msg['content']
            if len(content) > 100:
                content = content[:97] + "..."
            summary_parts.append(f"{role}: {content}")
        
        if len(self.conversation_history) > 6:
            summary_parts.append(f"... et {len(self.conversation_history) - 6} messages précédents")
        
        return "\n".join(summary_parts)