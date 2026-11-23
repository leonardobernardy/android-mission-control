# Scripts de diagnóstico Android

Scripts somente de leitura para executar no shell do Android com ADB. Eles mostram informações que ajudam a investigar anúncios e apps desconhecidos; não confirmam malware e não removem nada.

## Scripts

- installed_apps_inventory.sh: apps de usuário, origem/versão e indicadores de permissões especiais.
- ad_sdk_markers.sh: procura nomes conhecidos de SDKs de anúncios nas APKs legíveis pelo shell. É uma heurística e pode não conseguir ler APKs protegidos pelo Android.
- notification_ad_channels.sh: procura nomes de canais de notificação que parecem promoção/anúncio.
- battery_and_permissions.sh: resumo de bateria, processos de apps e algumas permissões concedidas.
- usage_and_jobs.sh: uso recente de apps e tarefas agendadas visíveis ao shell.

## Execução

Com o telefone desbloqueado, a depuração USB ativada e este computador autorizado:

    adb push scripts/diagnostics /data/local/tmp/android-diagnostics
    adb shell sh /data/local/tmp/android-diagnostics/installed_apps_inventory.sh

Troque o nome do script para executar os outros. Para remover a cópia temporária depois:

    adb shell rm -r /data/local/tmp/android-diagnostics

O acesso a dados de pacote varia entre fabricantes e versões do Android. Revise os resultados no telefone; nome de permissão, canal de anúncio ou instalador ausente, isoladamente, não prova que um app seja malicioso. Os relatórios podem revelar nomes de apps instalados: não os publique sem revisão.
