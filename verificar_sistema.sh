#!/bin/bash
# Script para testar o sistema completo
# Execute: bash verificar_sistema.sh

echo "=================================================="
echo "VERIFICACAO FINAL DO SISTEMA"
echo "=================================================="

echo ""
echo "1. Verificando Python..."
python --version

echo ""
echo "2. Verificando dependências..."
pip list | grep -E "Flask|SQLAlchemy|Flask-Login"

echo ""
echo "3. Executando diagnóstico..."
python diagnostico_completo.py

echo ""
echo "4. Executando análise de segurança..."
python analise_seguranca.py

echo ""
echo "=================================================="
echo "VERIFICACAO CONCLUIDA"
echo "=================================================="
echo ""
echo "Proximas etapas:"
echo "1. Iniciar aplicação: python app_clinica.py"
echo "2. Acessar: http://127.0.0.1:5000"
echo "3. Login: luisaizza / 123"
echo "=================================================="
