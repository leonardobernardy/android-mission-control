#!/system/bin/sh
# Procura palavras promocionais nos canais de notificação visíveis ao sistema.

echo "=== CANAIS DE NOTIFICACAO COM NOMES PROMOCIONAIS ==="
dumpsys notification 2>/dev/null | awk '
  /^      AppSettings: / { pkg=$2 }
  /NotificationChannel\{mId=/ {
    line=tolower($0)
    if (line ~ /propaganda|ads?|promo|offer|recomend|advert|sponsor/) {
      gsub(/NotificationChannel\{/, "")
      printf "%s | %s\n", pkg, substr($0, 1, 180)
    }
  }
'
echo "Se nenhum canal aparecer, isso não significa que o aparelho esteja livre de anúncios ou malware."
