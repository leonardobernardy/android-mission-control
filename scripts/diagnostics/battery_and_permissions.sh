#!/system/bin/sh
# Resumos somente de leitura; a saída varia entre Androids e fabricantes.

echo "=== BATERIA ==="
dumpsys battery 2>/dev/null | grep -E 'level:|status:|health:|temperature:' | head -10

echo ""
echo "=== TOP DE USO DE BATERIA (SE DISPONIVEL) ==="
dumpsys batterystats --charged 2>/dev/null | grep -E 'Estimated power use|Uid u0a[0-9]+|u0a[0-9]+:' | head -30

echo ""
echo "=== PROCESSOS DE APPS DE USUARIO ATIVOS ==="
ps -A -o USER,NAME 2>/dev/null | awk 'NR==1 || $1 ~ /^u[0-9]+_a[0-9]+$/' | head -40

echo ""
echo "=== PERMISSOES SENSIVEIS CONCEDIDAS A APPS DE USUARIO ==="
pm list packages -3 2>/dev/null | sed 's/^package://' | while IFS= read -r pkg; do
  [ -n "$pkg" ] || continue
  details=$(dumpsys package "$pkg" 2>/dev/null)
  flags=""
  printf '%s\n' "$details" | grep -qi 'ACCESS_FINE_LOCATION: granted=true' && flags="$flags LOCALIZACAO"
  printf '%s\n' "$details" | grep -qi 'RECORD_AUDIO: granted=true' && flags="$flags MICROFONE"
  printf '%s\n' "$details" | grep -qi 'CAMERA: granted=true' && flags="$flags CAMERA"
  printf '%s\n' "$details" | grep -qi 'READ_SMS: granted=true' && flags="$flags SMS"
  [ -n "$flags" ] && printf '%s |%s\n' "$pkg" "$flags"
done
