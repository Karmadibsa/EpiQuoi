#!/bin/bash
set -euo pipefail

echo "📦 Création du venv dans MCP_Server..."

python3 -m venv venv

echo "🔧 Activation du venv..."
source venv/bin/activate

echo "⬆️  Mise à jour de pip..."
python3 -m pip install --upgrade pip

echo "📥 Installation des dépendances..."
python3 -m pip install -r requirements.txt

echo "✅ Installation terminée !"
echo ""
echo "Pour utiliser le venv :"
echo "  source venv/bin/activate"
echo ""
echo "Pour lancer le serveur MCP :"
echo "  python3 server.py"
echo ""
echo "⚠️ IMPORTANT : vérifie que tu utilises le bon python (celui de ./venv) :"
echo "  which python3"
echo "  python3 -c \"import uvicorn; print('uvicorn OK')\""
