#!/bin/bash

# ============================================
# PANIC MODE - Mission Control
# Efeitos visuais apenas, nada destrutivo
# ============================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WALLPAPER_DIR="$SCRIPT_DIR/wallpapers"
LOGO_FILE="$SCRIPT_DIR/mission_control_logo.png"

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'

# Função para mudar wallpaper
change_wallpaper() {
    echo -e "${CYAN}[*] Alterando papel de parede...${NC}"
    
    # Criar wallpaper temporal com imagem degradê
    if command -v convert &> /dev/null; then
        convert -size 1920x1080 \
            -define gradient:angle=135 \
            gradient:'#0a0a1a'-'#1a1a3e' \
            -fill '#00d4ff' -font 'Courier' -pointsize 72 \
            -gravity center -annotate +0-100 'MISSION CONTROL' \
            -fill '#ff3366' -pointsize 36 \
            -annotate +0+50 '⚠ SYSTEM MONITORING ACTIVE ⚠' \
            -fill '#00ff88' -pointsize 24 \
            -annotate +0+120 "$(date '+%Y-%m-%d %H:%M:%S')" \
            "$WALLPAPER_DIR/panic_wallpaper.png" 2>/dev/null
    fi
    
    # Tentar mudar wallpaper via gsettings
    if command -v gsettings &> /dev/null; then
        if [ -f "$WALLPAPER_DIR/panic_wallpaper.png" ]; then
            gsettings set org.gnome.desktop.background picture-uri "file://$WALLPAPER_DIR/panic_wallpaper.png"
            gsettings set org.gnome.desktop.background picture-uri-dark "file://$WALLPAPER_DIR/panic_wallpaper.png"
        fi
    fi
    
    # Fallback: feh
    if command -v feh &> /dev/null && [ -f "$WALLPAPER_DIR/panic_wallpaper.png" ]; then
        feh --bg-fill "$WALLPAPER_DIR/panic_wallpaper.png" 2>/dev/null
    fi
    
    echo -e "${GREEN}[✓] Wallpaper alterado${NC}"
}

# Função para animação de terminal
terminal_animation() {
    echo -e "${CYAN}[*] Iniciando animação de terminal...${NC}"
    
    # Criar script de animação
    cat > /tmp/panic_terminal.sh << 'TERMINAL_SCRIPT'
#!/bin/bash

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
MAGENTA='\033[0;35m'
NC='\033[0m'
BOLD='\033[1m'

clear
echo -e "${RED}${BOLD}"
echo "  ╔══════════════════════════════════════════════════════════════╗"
echo "  ║                                                              ║"
echo "  ║   ██████╗ ██╗  ██╗ █████╗ ███╗   ██╗████████╗ ██████╗ ███╗   ██╗  ║"
echo "  ║   ██╔══██╗██║  ██║██╔══██╗████╗  ██║╚══██╔══╝██╔═══██╗████╗  ██║  ║"
echo "  ║   ██████╔╝███████║███████║██╔██╗ ██║   ██║   ██║   ██║██╔██╗ ██║  ║"
echo "  ║   ██╔═══╝ ██╔══██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╗██║  ║"
echo "  ║   ██║     ██║  ██║██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚████║  ║"
echo "  ║   ╚═╝     ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝  ╚═══╝  ║"
echo "  ║                                                              ║"
echo "  ╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

sleep 1

echo -e "${CYAN}[SYSTEM] Inicializando protocolo de segurança...${NC}"
sleep 0.5
echo -e "${YELLOW}[SCAN] Verificando integridade do sistema...${NC}"
sleep 0.8
echo -e "${GREEN}[OK] Kernel verified: $(uname -r)${NC}"
sleep 0.5
echo -e "${CYAN}[NET] Configurando interfaces de rede...${NC}"
sleep 0.6

# Mostrar informações do sistema
echo ""
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BOLD}${CYAN}                    📊 SYSTEM DIAGNOSTICS 📊${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

echo -e "${GREEN}[HOSTNAME]${NC} $(hostname)"
echo -e "${GREEN}[KERNEL]${NC}   $(uname -r)"
echo -e "${GREEN}[UPTIME]${NC}   $(uptime -p)"
echo -e "${GREEN}[CPU]${NC}      $(lscpu | grep 'Model name' | cut -d: -f2 | xargs)"
echo -e "${GREEN}[RAM]${NC}      $(free -h | awk '/^Mem:/{print $2}') total, $(free -h | awk '/^Mem:/{print $3}') usado"
echo -e "${GREEN}[DISCO]${NC}    $(df -h / | awk 'NR==2{print $2 " total, " $3 " usado (" $5 ")"}')"
echo ""

sleep 1

echo -e "${YELLOW}[ADB] Procurando dispositivos Android...${NC}"
sleep 0.5

if command -v adb &> /dev/null; then
    DEVICES=$(adb devices 2>/dev/null | grep -v "List" | grep "device$" | wc -l)
    if [ "$DEVICES" -gt 0 ]; then
        echo -e "${GREEN}[ADB] ✓ $DEVICES dispositivo(s) conectado(s)${NC}"
        adb devices 2>/dev/null | grep "device$" | while read line; do
            SERIAL=$(echo $line | awk '{print $1}')
            MODEL=$(adb -s $SERIAL shell getprop ro.product.model 2>/dev/null | tr -d '\r')
            ANDROID=$(adb -s $SERIAL shell getprop ro.build.version.release 2>/dev/null | tr -d '\r')
            echo -e "${CYAN}  → $SERIAL: $MODEL (Android $ANDROID)${NC}"
        done
    else
        echo -e "${YELLOW}[ADB] Nenhum dispositivo encontrado${NC}"
    fi
else
    echo -e "${YELLOW}[ADB] ADB não instalado${NC}"
fi

echo ""
sleep 0.5

echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${RED}${BOLD}                    ⚠ SYSTEM MONITORING ACTIVE ⚠${NC}"
echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Simular logs
for i in $(seq 1 15); do
    TIMESTAMP=$(date '+%H:%M:%S')
    case $((RANDOM % 5)) in
        0) echo -e "${GREEN}[$TIMESTAMP]${NC} Packet inspection: $(shuf -i 1000-9999 -n 1) packets/sec" ;;
        1) echo -e "${CYAN}[$TIMESTAMP]${NC} Firewall status: ACTIVE [$(shuf -i 10000-65535 -n 1) rules]" ;;
        2) echo -e "${YELLOW}[$TIMESTAMP]${NC} Memory sweep: $(free -h | awk '/^Mem:/{print $3}')/$(free -h | awk '/^Mem:/{print $2}') in use" ;;
        3) echo -e "${MAGENTA}[$TIMESTAMP]${NC} CPU load: $(cat /proc/loadavg | awk '{print $1}') | Threads: $(ps aux | wc -l)" ;;
        4) echo -e "${GREEN}[$TIMESTAMP]${NC} Network scan: $(ip route | grep -oP 'src \K\S+' | head -1) → Online" ;;
    esac
    sleep 0.3
done

echo ""
echo -e "${RED}${BOLD}🔒 SECURITY PROTOCOL ENGAGED${NC}"
echo -e "${CYAN}Press any key to close...${NC}"
read -n 1 -s
TERMINAL_SCRIPT
    
    chmod +x /tmp/panic_terminal.sh
    
    # Abrir terminal com animação
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash /tmp/panic_terminal.sh &
    elif command -v konsole &> /dev/null; then
        konsole -e bash /tmp/panic_terminal.sh &
    elif command -v xfce4-terminal &> /dev/null; then
        xfce4-terminal -e "bash /tmp/panic_terminal.sh" &
    else
        xterm -e bash /tmp/panic_terminal.sh &
    fi
    
    echo -e "${GREEN}[✓] Terminal de animação aberto${NC}"
}

# Função para tocar som
play_sound() {
    echo -e "${CYAN}[*] Tocando som de alerta...${NC}"
    
    # Criar arquivo de som com sox
    if command -v sox &> /dev/null; then
        sox -n /tmp/panic_alert.wav synth 0.5 sine 880 synth 0.5 sine 1100 pad 0 1 vol 0.3 2>/dev/null
        paplay /tmp/panic_alert.wav 2>/dev/null || aplay /tmp/panic_alert.wav 2>/dev/null
    fi
    
    # Fallback: beep do系统
    if command -v beep &> /dev/null; then
        beep -f 800 -l 200 -n -f 1000 -l 200 -n -f 1200 -l 200 2>/dev/null
    fi
    
    echo -e "${GREEN}[✓] Som reproduzido${NC}"
}

# Função para mostrar informações do dispositivo
show_device_info() {
    echo -e "${CYAN}[*] Coletando informações do dispositivo...${NC}"
    
    if command -v adb &> /dev/null; then
        DEVICE_SERIAL=$(adb devices 2>/dev/null | grep "device$" | head -1 | awk '{print $1}')
        
        if [ -n "$DEVICE_SERIAL" ]; then
            MODEL=$(adb -s $DEVICE_SERIAL shell getprop ro.product.model 2>/dev/null | tr -d '\r')
            BRAND=$(adb -s $DEVICE_SERIAL shell getprop ro.product.brand 2>/dev/null | tr -d '\r')
            ANDROID=$(adb -s $DEVICE_SERIAL shell getprop ro.build.version.release 2>/dev/null | tr -d '\r')
            BATTERY=$(adb -s $DEVICE_SERIAL shell dumpsys battery 2>/dev/null | grep "level:" | awk '{print $2}' | tr -d '\r')
            
            echo ""
            echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${BOLD}${CYAN}                 📱 DEVICE INFORMATION 📱${NC}"
            echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo ""
            echo -e "${GREEN}[MODEL]${NC}   $BRAND $MODEL"
            echo -e "${GREEN}[ANDROID]${NC} $ANDROID"
            echo -e "${GREEN}[BATTERY]${NC} $BATTERY%"
            echo -e "${GREEN}[SERIAL]${NC}  $DEVICE_SERIAL"
            echo ""
        fi
    fi
}

# Função principal
main() {
    echo -e "${RED}${BOLD}"
    echo "  ╔══════════════════════════════════════════════════════════════╗"
    echo "  ║                                                              ║"
    echo "  ║            🚨 PANIC MODE ACTIVATED 🚨                        ║"
    echo "  ║                                                              ║"
    echo "  ║            Mission Control - Security Protocol                ║"
    echo "  ║                                                              ║"
    echo "  ╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo ""
    
    # Criar diretório de wallpapers
    mkdir -p "$WALLPAPER_DIR"
    
    # Executar efeitos
    change_wallpaper
    show_device_info
    play_sound
    terminal_animation
    
    echo ""
    echo -e "${GREEN}${BOLD}[✓] PANIC MODE COMPLETO${NC}"
    echo -e "${CYAN}Todos os efeitos visuais foram ativados.${NC}"
    echo -e "${YELLOW}Nenhum arquivo foi modificado ou deletado.${NC}"
}

# Executar
main
