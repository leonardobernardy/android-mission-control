#!/system/bin/sh
# Dados de uso e jobs disponíveis ao shell; a saída pode ser limitada pelo fabricante.

echo "=== ULTIMO USO DE APPS DE USUARIO ==="
dumpsys usagestats 2>/dev/null | grep 'package=' | sed -n 's/.*package=\([^ ]*\).*lastTimeUsed="\([^"]*\)".*/\2 | \1/p' | sort -r | head -50

echo ""
echo "=== APPS DE USUARIO SEM USO REGISTRADO (SE DISPONIVEL) ==="
pm list packages -3 2>/dev/null | sed 's/^package://' | while IFS= read -r pkg; do
  [ -n "$pkg" ] || continue
  usage=$(dumpsys usagestats 2>/dev/null | grep -m1 "package=$pkg ")
  printf '%s\n' "$usage" | grep -q 'lastTimeUsed="1969-12-31' && echo "$pkg"
done

echo ""
echo "=== JOBS DE APPS DE USUARIO (SE DISPONIVEIS) ==="
dumpsys jobscheduler 2>/dev/null | grep -E 'JOB #u[0-9]+_a[0-9]+/' | head -40
