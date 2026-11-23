# Android Mission Control

Ferramentas locais para diagnóstico e suporte de aparelhos Android. O repositório contém o painel existente e scripts de leitura via ADB; o assistente gráfico para Windows fica em windows-cleaner/.

## Limpeza assistida no Windows

Abra windows-cleaner/Start_Android_Cleaner.bat. O assistente identifica o ADB, lista aparelhos autorizados, mostra apps de usuário e alguns indicadores para revisão, e permite exportar um relatório local. A remoção de um app exige seleção e confirmação explícita.

Sem depuração USB autorizada, o assistente abre um roteiro manual. Transferência MTP permite copiar arquivos, mas não dá ao PC acesso para examinar dados privados ou remover apps. O programa não tenta contornar o bloqueio, não usa root e não limpa nada automaticamente.

## Scripts de diagnóstico ADB

Os scripts somente de leitura estão em scripts/diagnostics/. Eles ajudam a revisar apps, origem de instalação, permissões, canais de notificação e indicadores de SDK de anúncios. Esses indicadores não confirmam malware.

Consulte cada pasta para requisitos, comandos e limitações. Não publique relatórios sem revisar os nomes de apps e outras informações do aparelho.
