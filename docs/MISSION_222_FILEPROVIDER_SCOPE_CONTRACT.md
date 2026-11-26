# M222 — Contrato de escopo do Android FileProvider

## Objetivo
Garantir que o provider usado pelo instalador não exponha diretórios amplos e que o mapeamento XML corresponda à pasta privada de download construída pelo atualizador.

## Dez rodadas executadas
1. Inspeção do AndroidManifest.xml e identificação do provider AndroidX efetivamente declarado.
2. Verificação de autoridade dinâmica ${applicationId}.fileprovider.
3. Confirmação de exported=false e grantUriPermissions=true.
4. Verificação de que o provider referencia exclusivamente @xml/file_paths.
5. Inspeção de file_paths.xml: mapeamento app_update_apk aponta para Download/updates/.
6. Comparação com getExternalFilesDir(DIRECTORY_DOWNLOADS)/updates usado pelo atualizador.
7. Confirmação de que o segundo mapeamento permanece limitado ao cache official_documents/.
8. Definição de contrato negativo para rejeitar root-path, external-path, files-path e caminhos amplos.
9. Criação de testes Python com parsing XML real e inspeção da construção de diretório no código Android.
10. Inclusão dos testes no comando já executado pelo CI (unittest discover) e ativação da branch no workflow de push/PR.

## Esclarecimento do caminho
O caminho físico permitido é Download/updates/ relativo ao diretório external-files do aplicativo. O nome lógico do mapeamento FileProvider é app_update_apk; por isso, o URI público gerado usa /app_update_apk/<nome-do-arquivo>. A política M221 valida o URI lógico, enquanto esta missão verifica o mapeamento físico.

## Limites
Os testes estáticos confirmam o contrato declarado no manifesto e XML; não substituem teste instrumentado no Android nem comprovam instalação física. Nenhum merge, Release, assinatura, alteração de Secrets, instalação ou ativação de AI-03 foi realizado.
