# Assistente de diagnóstico Android para Windows

Interface gráfica local para aparelhos conectados por USB. Usa apenas a biblioteca padrão do Python e o Android Debug Bridge (ADB).

## O que faz

- Detecta aparelhos autorizados pelo ADB e diferencia estados como unauthorized e offline.
- Lê modelo, versão do Android, bateria e lista de apps instalados pelo usuário.
- Mostra origem de instalação e alguns indicadores de permissões especiais para revisão manual.
- Permite salvar um relatório de texto localmente, somente quando você escolhe o caminho.
- Pode desinstalar um app de usuário selecionado, depois de uma confirmação explícita. A desinstalação apaga os dados daquele app.
- Se não houver depuração USB, abre um roteiro de limpeza manual no próprio telefone.

Os indicadores são heurísticas. Uma permissão ou instalação fora da loja não prova que um app seja vírus. O programa não coleta logs, não transmite relatórios, não acessa arquivos privados dos apps, não remove apps automaticamente e não usa root.

## Requisitos

- Windows 10/11.
- Python 3.10 ou mais recente, com Tkinter (incluído nas distribuições comuns do Python para Windows).
- Android SDK Platform-Tools (adb.exe). O app procura em windows-cleaner/platform-tools/adb.exe, no SDK padrão do usuário e no PATH.

Baixe as Platform-Tools da página oficial do Android Developers: https://developer.android.com/tools/releases/platform-tools. Se preferir uma cópia portátil, coloque a pasta platform-tools dentro desta pasta windows-cleaner; o executável não é versionado no Git.

## Uso

1. No celular, desbloqueie a tela e conecte um cabo USB de dados.
2. Para diagnóstico pelo PC, ative Opções do desenvolvedor > Depuração USB no aparelho e aceite o aviso RSA que aparece na tela.
3. Clique duas vezes em Start_Android_Cleaner.bat.
4. Escolha o aparelho, clique em Fazer diagnóstico e revise os indicadores. Se decidir remover um app, selecione-o e confirme a desinstalação.

Se o ADB mostrar unauthorized, desbloqueie o celular e aceite o aviso. Se não aparecer aparelho, troque para um cabo/porta de dados, escolha transferência de arquivos e confira o driver USB do fabricante.

## Limite quando a depuração está desligada

Sem depuração USB autorizada, o computador não pode comandar a desinstalação nem examinar os dados privados dos apps. MTP/Transferência de arquivos permite copiar arquivos acessíveis; não concede acesso de administrador ao Android. Um APK enviado pelo PC também precisa ser instalado pelo usuário e, como app comum, não pode remover silenciosamente outros apps. Use o roteiro Sem depuração USB? para a limpeza manual.

O ADB exige que o dono desbloqueie o aparelho e aceite a chave RSA do computador. Este programa não tenta contornar essa proteção. Consulte a documentação oficial sobre ADB e autorização USB: https://developer.android.com/tools/adb.
