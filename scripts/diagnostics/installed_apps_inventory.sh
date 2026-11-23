#!/system/bin/sh
# Inventário somente de leitura dos apps instalados pelo usuário.

echo "=== APPS DE USUARIO | ORIGEM | VERSAO | PERMISSOES A REVISAR ==="
pm list packages -3 -i 2>/dev/null | sed 's/^package://' | while IFS= read -r entry; do
  pkg=$(printf '%s\n' "$entry" | cut -d' ' -f1)
  [ -n "$pkg" ] || continue
  installer=$(printf '%s\n' "$entry" | sed -n 's/.*installer=//p')
  [ -n "$installer" ] || installer="não informado"
  details=$(dumpsys package "$pkg" 2>/dev/null)
  version=$(printf '%s\n' "$details" | grep -m1 'versionName=' | sed 's/.*versionName=//')
  flags=""
  printf '%s\n' "$details" | grep -qi 'SYSTEM_ALERT_WINDOW: granted=true' && flags="$flags SOBREPOSICAO"
  printf '%s\n' "$details" | grep -qi 'REQUEST_INSTALL_PACKAGES: granted=true' && flags="$flags INSTALA_APK"
  printf '%s\n' "$details" | grep -Eqi 'READ_SMS: granted=true|RECEIVE_SMS: granted=true' && flags="$flags SMS"
  printf '%s\n' "$details" | grep -qi 'BIND_ACCESSIBILITY_SERVICE' && flags="$flags ACESSIBILIDADE_DECLARADA"
  printf '%s\n' "$details" | grep -Eqi 'BIND_DEVICE_ADMIN|DEVICE_ADMIN_ENABLED' && flags="$flags ADMIN_DECLARADO"
  [ -n "$version" ] || version="não informado"
  [ -n "$flags" ] || flags="—"
  printf '%s | %s | %s | %s\n' "$pkg" "$installer" "$version" "$flags"
done
