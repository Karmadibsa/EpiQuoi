#!/bin/bash
# Script pour créer et configurer le venv du MCP Server

echo "📦 Création du venv dans MCP_Server..."

# Créer le venv
python3 -m venv venv

# Activer le venv
echo "🔧 Activation du venv..."
source venv/bin/activate

# Mettre à jour pip
echo "⬆️  Mise à jour de pip..."
pip install --upgrade pip

# Installer les dépendances
echo "📥 Installation des dépendances..."
pip install -r requirements.txt

echo "✅ Installation terminée !"
echo ""
echo "Pour utiliser le venv :"
echo "  source venv/bin/activate"
echo ""
echo "Pour lancer le serveur MCP :"
echo "  python3 server.py"
