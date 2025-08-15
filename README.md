---
title: TAKEOFF AI - Construction Estimation
emoji: 🏗️
colorFrom: blue
colorTo: green
sdk: streamlit
sdk_version: 1.48.0
app_file: app.py
pinned: false
---

# 🏗️ TAKEOFF AI - Système d'Estimation de Construction

TAKEOFF AI est une application web moderne pour l'estimation de construction, intégrant l'intelligence artificielle Claude d'Anthropic pour assister les professionnels dans leurs projets.

## ✨ Fonctionnalités principales

- **📄 Visualisation PDF** : Chargez et annotez vos plans de construction
- **📐 Outils de mesure avancés** : 5 modes de mesure (distance, surface, périmètre, angle, calibration)
- **🎯 Système d'accrochage intelligent** : Accrochage automatique aux lignes et points
- **📦 Catalogue de produits** : Gérez votre catalogue de matériaux avec prix et dimensions
- **🤖 Assistant IA intégré** : Obtenez des conseils d'expert et des analyses contextuelles
- **📊 Rapports détaillés** : Exportez vos estimations en CSV, JSON ou PDF
- **🌐 Interface web moderne** : Accessible depuis n'importe quel navigateur

## 🚀 Utilisation de cette application

### Configuration requise

Pour utiliser l'assistant IA, vous devez disposer d'une clé API Anthropic Claude :

1. Créez un compte sur [Anthropic](https://console.anthropic.com/)
2. Générez une clé API
3. Entrez votre clé dans la barre latérale de l'application

### Guide d'utilisation

#### 1. Charger un PDF
- Cliquez sur "Charger un PDF" dans la colonne de gauche
- Sélectionnez votre plan de construction
- Le PDF s'affichera dans la zone centrale

#### 2. Calibrer l'échelle
- Sélectionnez l'outil "Calibration"
- Mesurez une distance connue sur le plan
- Entrez la valeur réelle pour définir l'échelle

#### 3. Effectuer des mesures
- **Distance** : Mesurez des longueurs linéaires
- **Surface** : Calculez des aires (polygones)
- **Périmètre** : Mesurez le contour d'une forme
- **Angle** : Calculez des angles entre deux lignes
- Associez des produits du catalogue aux mesures

#### 4. Utiliser l'assistant IA
- Entrez votre clé API Claude dans la barre latérale
- Posez des questions sur votre projet
- Obtenez des recommandations personnalisées
- Demandez des analyses de coûts et matériaux

#### 5. Exporter les résultats
- Consultez l'onglet "Totaux" pour voir le récapitulatif
- Exportez vos données en CSV ou JSON
- Générez des rapports détaillés

## 🛠️ Fonctionnalités techniques

### Outils de mesure
- **Accrochage intelligent** : Détection automatique des points et lignes
- **Précision** : Calculs basés sur la calibration d'échelle
- **Annotations** : Ajout de notes et commentaires sur les mesures
- **Historique** : Sauvegarde de toutes les mesures effectuées

### Catalogue de produits
- **Base de données** : Stockage local des produits et prix
- **Recherche** : Filtrage rapide par nom, catégorie ou prix
- **Association** : Liaison directe produits-mesures
- **Calculs automatiques** : Quantités et coûts totaux

### Assistant IA Claude
- **Analyse contextuelle** : Compréhension des plans de construction
- **Recommandations** : Suggestions de matériaux et techniques
- **Estimations** : Aide aux calculs de coûts et délais
- **Expertise** : Conseils basés sur les bonnes pratiques du secteur

## 📋 Exemples d'usage

### Pour un architecte
- Analyse rapide des surfaces habitables
- Calcul des matériaux pour les cloisons
- Estimation des coûts de construction

### Pour un entrepreneur
- Quantification précise des matériaux
- Planification des commandes
- Suivi des coûts en temps réel

### Pour un maître d'ouvrage
- Vérification des quantités facturées
- Contrôle des budgets
- Validation des devis

## 🔧 Installation locale (optionnelle)

Si vous souhaitez exécuter l'application sur votre machine :

```bash
# Cloner le repository
git clone https://huggingface.co/spaces/[username]/takeoff-ai
cd takeoff-ai

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run app.py
```

## 🛡️ Sécurité et confidentialité

- **Données locales** : Vos PDF et mesures restent dans votre session
- **Clé API** : Stockage sécurisé, jamais partagée
- **Confidentialité** : Aucune sauvegarde permanente des données
- **HTTPS** : Communications chiffrées

## 📚 Ressources

- **Documentation Streamlit** : [streamlit.io](https://streamlit.io)
- **API Anthropic Claude** : [docs.anthropic.com](https://docs.anthropic.com)
- **Support Hugging Face** : [huggingface.co/docs](https://huggingface.co/docs)

## 🤝 Contribution

Ce projet est open source. Les contributions sont les bienvenues :

1. Fork le projet
2. Créez votre branche feature
3. Committez vos modifications
4. Ouvrez une Pull Request

## 📄 Licence

Projet sous licence MIT - Libre d'utilisation commerciale et personnelle.

---

**Développé avec ❤️ pour les professionnels de la construction**

[![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Spaces-blue)](https://huggingface.co/spaces)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![Claude AI](https://img.shields.io/badge/Claude-AI-orange)](https://anthropic.com)
