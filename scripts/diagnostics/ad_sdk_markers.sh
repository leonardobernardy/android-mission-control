#!/system/bin/sh
# Busca nomes de SDKs de anúncios em APKs que o shell consiga ler.

MARKERS='com/applovin|com/unity3d/ads|com/google/android/gms/ads|com/inmobi|com/mbridge|com/vungle|com/ironsource|com/startapp|com/chartboost|com/bytedance/sdk/openadsdk|com/pangle'
echo "=== INDICIOS DE SDK DE ANUNCIO EM APKs LEGIVEIS ==="
echo "Um SDK de anúncios não é prova de malware. APKs protegidos podem ser ignorados."

pm list packages -3 2>/dev/null | sed 's/^package://' | while IFS= read -r pkg; do
  [ -n "$pkg" ] || continue
  pm path "$pkg" 2>/dev/null | sed 's/^package://' | while IFS= read -r apk; do
    [ -n "$apk" ] || continue
    [ -r "$apk" ] || continue
    markers=$(head -c 8388608 "$apk" 2>/dev/null | tr '\000' '\n' | grep -aoE "$MARKERS" 2>/dev/null | sort -u | tr '\n' ' ')
    [ -n "$markers" ] && printf '%s | %s\n' "$pkg" "$markers"
  done
done
