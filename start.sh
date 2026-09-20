#!/bin/bash

# ============================================
# Mission Control - Script de Inicialização
# ============================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "  ╔══════════════════════════════════════════════════════════════╗"
echo "  ║                                                              ║"
echo "  ║            ⚡ MISSION CONTROL - STARTUP ⚡                    ║"
echo "  ║                                                              ║"
echo "  ╚══════════════════════════════════════════════════════════════╝"
echo ""

# Verificar dependências
echo "[1/4] Verificando dependências..."

if ! command -v python3 &> /dev/null; then
    echo "  ✗ Python3 não encontrado"
    echo "  → Instale: sudo apt install python3 python3-pip"
    exit 1
fi
echo "  ✓ Python3 encontrado"

if ! command -v adb &> /dev/null; then
    echo "  ⚠ ADB não encontrado (funcionalidade limitada)"
    echo "  → Instale: sudo apt install android-tools-adb"
else
    echo "  ✓ ADB encontrado"
fi

# Verificar/instalar dependências Python
echo ""
echo "[2/4] Verificando pacotes Python..."

if [ ! -d "venv" ]; then
    echo "  → Criando ambiente virtual..."
    python3 -m venv venv
fi

source venv/bin/activate

pip install -q -r requirements.txt 2>/dev/null
echo "  ✓ Pacotes instalados"

# Verificar dispositivos ADB
echo ""
echo "[3/4] Verificando dispositivos Android..."

if command -v adb &> /dev/null; then
    DEVICES=$(adb devices 2>/dev/null | grep -v "List" | grep "device$" | wc -l)
    if [ "$DEVICES" -gt 0 ]; then
        echo "  ✓ $DEVICES dispositivo(s) conectado(s):"
        adb devices 2>/dev/null | grep "device$" | while read line; do
            SERIAL=$(echo $line | awk '{print $1}')
            MODEL=$(adb -s $SERIAL shell getprop ro.product.model 2>/dev/null | tr -d '\r')
            echo "    → $SERIAL ($MODEL)"
        done
    else
        echo "  ⚠ Nenhum dispositivo encontrado"
        echo "    → Conecte via USB ou ative depuração USB"
    fi
else
    echo "  ⚠ ADB não disponível"
fi

# Obter IP local
echo ""
echo "[4/4] Configurando servidor..."

IP=$(hostname -I | awk '{print $1}')
PORT=8080

echo ""
echo "  ╔══════════════════════════════════════════════════════════════╗"
echo "  ║                                                              ║"
echo "  ║            🚀 SERVIDOR PRONTO PARA INICIAR                   ║"
echo "  ║                                                              ║"
echo "  ║  Acesse no celular:                                          ║"
echo "  ║  → http://$IP:$PORT                                         ║"
echo "  ║                                                              ║"
echo "  ║  Acesse no PC:                                               ║"
echo "  ║  → http://localhost:$PORT                                    ║"
echo "  ║                                                              ║"
echo "  ╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "  Pressione Ctrl+C para parar o servidor"
echo ""

# Iniciar servidor
python3 main.py
