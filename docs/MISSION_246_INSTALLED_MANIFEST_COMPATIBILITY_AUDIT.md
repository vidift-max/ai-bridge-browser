# M246 — Comparação do Manifest instalado do AI-PHONE com a branch candidata

Data: 2026-11-26

## Objetivo

Comparar o AndroidManifest.xml extraído do AI-PHONE fornecido pelo usuário com o Manifest, código e políticas da branch candidata do atualizador. Esta missão é somente de auditoria e documentação: não instala, publica, mescla, remove nem altera credenciais.

## Escopo e evidências

- Repositório: `vidift-max/ai-bridge-browser`
- Branch auditada: `feat/mission-241-updater-backport-v2-saas-alpha`
- PR: #234, Draft / aberta / não mesclada na última consulta.
- Branch base: `v2-saas-alpha`
- Manifest de referência: arquivo AndroidManifest.xml extraído do AI-PHONE e enviado pelo usuário nesta conversa.
- Manifest candidato: `app/src/main/AndroidManifest.xml`, blob `dc103c2cfa298c508e38f52e4957e9433d443514`.
- Manifest base: `app/src/main/AndroidManifest.xml`, blob `67c4155517cc5717e4b6272a13733808e0098a74`.
- Gradle candidato: `app/build.gradle.kts`, blob `27e5311ee96856ba4edb56cb18100d04d696d5e6`.

## Dez rodadas verificáveis

### 01/10 — Leitura do Manifest de referência
**PASS.** O arquivo fornecido declara package `com.vidiftmax.aibridgebrowser`, versionCode 1, versionName 0.1.0 e label `AI-PHONE`.

### 02/10 — Identidade de pacote e versão candidata
**PASS COM LIMITE.** A branch candidata configura `applicationId= com.vidiftmax.aibridgebrowser`, versionCode 2 e versionName 0.2.0. O identificador de pacote coincide e a versão candidata é superior à versão indicada no Manifest enviado. Isso, isoladamente, não prova compatibilidade funcional nem assinatura compatível.

### 03/10 — Activity launcher
**PASS.** O Manifest de referência declara `.HomeActivity` como launcher. O Manifest candidato também declara `.HomeActivity` como launcher. A tela inicial principal está preservada nominalmente.

### 04/10 — Activities de mensagens e convite
**NO-GO.** O Manifest de referência declara `MessengerActivity` e `MessengerInviteActivity`, incluindo filtros de convite `aibridge://invite` e links HTTPS `*.web.app/i/`. O Manifest candidato declara `MessengerActivity`, mas não declara `MessengerInviteActivity` nem seus filtros. A busca direta pelo arquivo-fonte `MessengerInviteActivity.java` na branch candidata retornou 404/NOT_FOUND. Não está comprovada a preservação do fluxo de convite.

### 05/10 — GPT-6 e salas coletivas
**NO-GO.** O Manifest de referência declara `Gpt6Activity`, `CollectiveRoomActivity` e `CollectiveRoomActivityV2`. Esses componentes não aparecem no Manifest candidato; a busca pelos respectivos arquivos-fonte na branch candidata retornou 404/NOT_FOUND. A referência também declara o alias launcher `MessengerLauncher` apontando para `CollectiveRoomActivityV2`; esse alias está ausente no candidato.

### 06/10 — Navegador e deep links
**NO-GO.** O Manifest de referência declara `MainActivity` com `exported=true`, `launchMode=singleTop`, configurações de mudança e filtro VIEW/BROWSABLE para `https://*.web.app/invite`. O Manifest candidato declara `MainActivity` com `exported=false` e sem o filtro de deep link. O botão da HomeActivity candidata inicia MainActivity explicitamente, mas isso não substitui o contrato externo de deep links presente na referência.

### 07/10 — Permissões e capacidades declaradas
**NO-GO PARA PARIDADE.** A referência declara `INTERNET`, `REQUEST_INSTALL_PACKAGES`, `ACCESS_NETWORK_STATE`, `RECORD_AUDIO` e `MODIFY_AUDIO_SETTINGS`. O Manifest candidato declara apenas `INTERNET`, `REQUEST_INSTALL_PACKAGES` e `ACCESS_NETWORK_STATE`. Portanto, as permissões de áudio da referência não foram preservadas no Manifest candidato. Não inferir se são necessárias ao fluxo atual sem auditoria funcional separada.

### 08/10 — Infraestrutura do atualizador
**PASS ESTÁTICO LIMITADO.** O candidato declara `UpdateCenterActivity` e AndroidX FileProvider com autoridade `${applicationId}.fileprovider` e recurso `@xml/file_paths`; o arquivo `file_paths.xml` existe. A permissão `REQUEST_INSTALL_PACKAGES` também está declarada. Isso comprova presença estrutural do atualizador, não uma instalação real nem compatibilidade completa com o aplicativo de referência.

### 09/10 — Assinatura e CI
**PASS PARA CI DEBUG; RELEASE BLOQUEADA/NÃO EXECUTADA.** O workflow exige os Secrets de assinatura e `AI_PHONE_EXPECTED_SIGNING_CERT_SHA256`, compara o certificado do APK Release com o valor esperado e bloqueia em caso de ausência ou divergência. O run #1299, ID `45806819112`, terminou SUCCESS: job `debug-build` SUCCESS (testes unitários, teste do gerador de manifesto e build debug); job `release-final` SKIPPED. Nenhum Secret foi lido ou alterado; nenhum APK Release foi produzido nesta execução.

### 10/10 — Decisão de compatibilidade
**NO-GO PARA ATUALIZAÇÃO IN-PLACE NESTA BRANCH.** Embora package ID, label, launcher principal e infraestrutura básica do atualizador coincidam, a branch candidata não preserva diversos componentes, filtros de convite/deep link, alias de launcher e permissões presentes no Manifest de referência. Além disso, a continuidade da assinatura instalada ainda não foi comprovada independentemente. Não publicar nem instalar esta candidata como atualização do AI-PHONE até que a paridade funcional necessária seja reconciliada e o certificado seja confirmado.

## Matriz resumida

| Área | Resultado |
|---|---|
| Package ID | PASS |
| Label AI-PHONE | PASS |
| HomeActivity launcher | PASS |
| MessengerActivity | PASS |
| MessengerInviteActivity / links de convite | NO-GO |
| Gpt6Activity | NO-GO |
| CollectiveRoomActivity / V2 | NO-GO |
| MessengerLauncher alias | NO-GO |
| MainActivity exported e deep link | NO-GO |
| Permissões de áudio | NO-GO para paridade |
| UpdateCenterActivity / FileProvider | PASS estático |
| CI debug | PASS |
| Release assinada | NÃO EXECUTADA |
| Continuidade do certificado instalado | BLOCKED / não comprovada |

## Próximas condições para liberar nova avaliação

1. Identificar a origem/código-fonte correspondente ao Manifest de referência e recuperar os componentes funcionais ausentes sem sobrescrever a HomeActivity atual.
2. Restaurar ou justificar explicitamente cada Activity, alias, filtro de convite/deep link, atributo exported e permissão que precise permanecer.
3. Executar testes de Manifest/integração que comprovem os fluxos preservados e obter CI verde na nova revisão.
4. Confirmar inequivocamente o fingerprint SHA-256 do pacote instalado `com.vidiftmax.aibridgebrowser`.
5. Comparar a assinatura do APK Release candidato com a assinatura instalada antes de qualquer publicação ou instalação.

## Limites respeitados

Nenhum merge, Release, workflow_dispatch, instalação, desinstalação, limpeza de dados, alteração de Secrets ou publicação foi executado. AI-01 e AI-02 continuam sendo o único escopo; AI-03 permanece desativada.


## Adendo M304 — estado após recuperação seletiva M303 (2026-11-27)

A comparação original desta auditoria foi feita contra a candidata M241 e é histórica. A branch M295 agora contém recuperação parcial dos seguintes elementos:

- `RECORD_AUDIO` e `MODIFY_AUDIO_SETTINGS` declaradas no Manifest;
- `.CollectiveRoomActivity` registrada como não exportada;
- alias exportado `.MessengerLauncher` apontando para `.CollectiveRoomActivity`;
- componentes locais `MessengerRetentionPolicy` e `CollectiveRoomMessageCodec`, com testes JVM adicionados.

**Não declarar paridade completa.** Permanecem ausentes ou sem integração compatível: `MessengerInviteActivity`, `Gpt6Activity`, `CollectiveRoomActivityV2`, WebRTC e os handlers de deep link. O alias atual não aponta para `CollectiveRoomActivityV2`. O Manifest não recebeu filtros de convite/deep link sem handlers correspondentes. O Gradle desta branch não declara dependência WebRTC, e a implementação V2 de origem importa `org.webrtc` e várias APIs que não estão presentes na implementação HTTP da branch M295.

### Evidência de branch

- PR #242 permanece OPEN / Draft / não merged.
- Head auditada: `83b8074a84790bc8a9286f80102a6517e3a2d3e7`.
- Manifest M295: blob `ad8a5a85a89920ce2ae6fb4864a5a0648527c90d`.
- `CollectiveRoomActivity.java`: blob `60dbfd3b5366971b09a33655f752454b3b988ff5`.
- Build e testes unitários nessa HEAD: não comprovados por CI nesta auditoria.

**Veredito atualizado: NO-GO para atualização in-place.** M303 reduziu a diferença do Manifest, mas não resolveu compatibilidade integral nem prova de execução. Nenhuma instalação, Release, merge ou ação no dispositivo foi realizada.
