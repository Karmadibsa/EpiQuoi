#!/bin/bash
set -euo pipefail

echo "📦 Création du venv dans MCP_Server..."

python3 -m venv venv

echo "🔧 Activation du venv..."
source venv/bin/activate

echo "⬆️  Mise à jour de pip..."
python -m pip install --upgrade pip

echo "📥 Installation des dépendances..."
python -m pip install -r requirements.txt

echo "✅ Installation terminée !"
echo ""
echo "Pour utiliser le venv :"
echo "  source venv/bin/activate"
echo ""
echo "Pour lancer le serveur MCP :"
echo "  python server.py"
