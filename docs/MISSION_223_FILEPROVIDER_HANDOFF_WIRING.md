# M223 — Android FileProvider installer handoff wiring

## Objetivo
Fechar a lacuna entre os contratos estáticos de diretório/URI e o código real que entrega o APK ao instalador Android. O teste verifica a ligação entre applicationId, autoridade do provider, alias lógico, caminho físico, MIME, ação e permissões.

## Dez rodadas de engenharia
1. Revisar a autoridade declarada no Manifest e o applicationId Android.
2. Vincular a autoridade em runtime (getPackageName() + ".fileprovider") à configuração declarativa.
3. Vincular a pasta privada Download/updates/ ao alias lógico app_update_apk.
4. Confirmar que o nome do artefato usado no download é app-release.apk.
5. Exigir geração de URI via FileProvider.getUriForFile, rejeitando Uri.fromFile e file://.
6. Exigir a ação Intent.ACTION_VIEW e o MIME Android de pacote APK.
7. Restringir flags ao grant de leitura e NEW_TASK, sem permissão de escrita.
8. Verificar que InstallerIntentPolicy.isSafeHandoff ocorre após a criação da URI e antes de startActivity.
9. Verificar que a validação de arquivo bloqueado/read-only antecede a criação da URI e que o hash continua vinculado ao APK.
10. Executar a suíte Python no CI Android junto com os testes JVM e builds Debug/Release-preparation.

## Evidência e limites
A suíte em scripts/tests/test_android_fileprovider_handoff.py lê Manifest, file_paths.xml, UpdateCenterActivity.java e InstallerIntentPolicy.java reais e verifica as relações acima. É uma validação estática de wiring; não executa AndroidX FileProvider em dispositivo/emulador e não comprova que o instalador foi aberto em hardware físico.

Nenhuma assinatura ou Secret foi acessada. Nenhuma Release foi publicada, nenhum APK foi instalado, nenhum PR foi mesclado e AI-03 permanece desabilitada.
