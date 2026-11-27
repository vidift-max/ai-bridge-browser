# M253 — AUDITORIA DE DEPENDÊNCIAS E CONJUNTO MÍNIMO DE RECUPERAÇÃO ANDROID

Data: 2026-11-26
Branch: feat/mission-241-updater-backport-v2-saas-alpha
PR: #234
Escopo: AI-01 / AI-02
AI-03: permanece desativada

## Resultado executivo

**PASS — origem Android histórica recuperada e mapeada.**
**NO-GO — cópia automática da árvore histórica não autorizada/não recomendada.**
**BLOCKED — port funcional completo ainda depende de integração seletiva, testes e compatibilidade com a branch atual.**

A branch histórica `feat/mission-136-android-browser-apk-readiness` contém a implementação Android que explica os componentes ausentes encontrados nas auditorias M246–M252. A origem está no mesmo repositório, portanto a hipótese de "fonte Android externa desconhecida" fica superada.

A branch atual já contém parte importante da infraestrutura Messenger/credenciais, mas não contém quatro Activities históricas e vários componentes de áudio/WebRTC necessários para reproduzir a funcionalidade histórica.

## 10 rodadas executadas

### 01/10 — Estado da PR e baseline
- PR #234 permanece aberta e Draft.
- Base: `v2-saas-alpha`.
- Head: `d713469813b717508954ea89f1989ac194b952f8`.
- Nenhum merge, release ou instalação foi executado.
- Resultado: **PASS** para isolamento operacional.

### 02/10 — Comparação do Gradle atual × histórico
Atual:
- applicationId: `com.vidiftmax.aibridgebrowser`
- compileSdk: 37
- minSdk: 29
- targetSdk: 35
- versionCode/versionName: 2 / 0.2.0
- AndroidX Core 1.17.0
- AndroidX WebKit 1.18.0

Histórico M136:
- mesmo package/SDKs;
- versionCode/versionName: 1 / 0.1.0;
- adicionava `io.github.webrtc-sdk:android:150.7871.08`;
- mantinha JUnit 4.13.2 e JSON de teste 20260814.

Resultado: **PASS** para identidade/dependências básicas; **BLOCKED** para WebRTC até port seletivo.

### 03/10 — Comparação do Manifest
O Manifest histórico contém, além da base atual:
- `Gpt6Activity`
- `MessengerInviteActivity`
- `CollectiveRoomActivity`
- `CollectiveRoomActivityV2`
- alias `MessengerLauncher`
- RECORD_AUDIO
- MODIFY_AUDIO_SETTINGS
- deep links de convite `aibridge://invite/...` e HTTPS `*.web.app/i/...`
- MainActivity exportada=true e singleTop.

A branch atual não contém esse conjunto completo.

Resultado: **PASS** para identificar o delta; **NO-GO** para aplicar o Manifest histórico integral sem revisão.

### 04/10 — Activities históricas recuperadas
Arquivos históricos confirmados:
- `Gpt6Activity.java` — blob `54e7d74ca2125de5d5abe788eda339ad407f1aa0`
- `MessengerInviteActivity.java` — blob `5ab8b68be02e7e6c95b0d9751ede45e355a01fd1`
- `CollectiveRoomActivity.java` — blob `50545e944ba3c37445b21b99078fe90a5d93a233`
- `CollectiveRoomActivityV2.java` — blob `74bfd0f984438d77ef32273a7cf6edd95c32585b`

Nenhum desses quatro arquivos existe na branch candidata atual.

Resultado: **PASS** para recuperação de origem.

### 05/10 — Infraestrutura já existente na branch atual
Confirmada na branch atual:
- `MessengerActivity.java`
- `MessengerHttpClient.java`
- `MessengerRemoteConfig.java`
- `AiPhoneCredentialVault.java`
- `MessengerRetentionPolicy.java`

Portanto não é necessário importar automaticamente a versão histórica desses componentes.

Resultado: **PASS** para redução de escopo.

### 06/10 — Dependências históricas ausentes
Para o conjunto histórico, foram confirmados como ausentes na branch atual:
- `InviteLinkParser.java`
- `AudioRecorder.java`
- `AudioPlayback.java`
- `AudioMonitor.java`
- `WebRtcVoiceEngine.java`
- `VoiceCallSession.java`
- `VoiceSignalPayload.java`
- `VoiceIceCandidateBuffer.java`
- `VoiceIceServerConfig.java`
- `VoiceIceServerConfigVault.java`
- `VoiceRoomControl.java`
- `FirebaseMessengerClient.java`

Resultado: **PASS** para inventário; **BLOCKED** para compilação das quatro Activities antes da recuperação seletiva.

### 07/10 — Grafo mínimo de dependências
Grafo funcional mínimo identificado:

`Gpt6Activity`
→ `MessengerHttpClient` + `AiPhoneCredentialVault` + JSON
→ infraestrutura já presente.

`MessengerInviteActivity`
→ `InviteLinkParser`
→ `MessengerHttpClient`
→ `FirebaseMessengerClient`
→ `CollectiveRoomActivityV2`.

`CollectiveRoomActivityV2`
→ Messenger remoto/Firebase
→ áudio local
→ WebRTC
→ sinalização/ICE
→ controles de sala.

Logo, as quatro Activities não devem ser copiadas isoladamente.

Resultado: **PASS** para definição do conjunto mínimo.

### 08/10 — Segurança e compatibilidade
A recuperação não autoriza:
- alterar Secrets/Variables;
- gerar Release;
- instalar APK;
- desinstalar AI-PHONE;
- substituir assinatura;
- fazer merge;
- force-push.

O atualizador M241 continua separado do port funcional. O fingerprint do app instalado continua não confirmado criptograficamente para continuidade Release.

Resultado: **PASS** para preservação das barreiras.

### 09/10 — Plano de port seletivo
Conjunto candidato para a próxima implementação, sujeito a revisão de código:
1. quatro Activities históricas;
2. parser de convite;
3. cliente Firebase;
4. áudio de nota;
5. monitoramento de áudio;
6. WebRTC;
7. estado/sinalização/ICE;
8. configuração segura de ICE;
9. controle de voz;
10. dependência WebRTC;
11. delta mínimo de Manifest.

Não importar automaticamente a árvore histórica inteira.

Resultado: **PASS** para plano de execução.

### 10/10 — Decisão da missão
**PASS:** a origem histórica Android foi localizada no mesmo repositório e os componentes ausentes foram identificados por blob SHA.

**NO-GO:** não fazer cherry-pick/cópia massiva da branch M136.

**BLOCKED:** funcionalidade histórica completa ainda não está presente na branch M241; requer port seletivo + testes.

Próxima missão recomendada: implementar o primeiro lote pequeno e verificável, começando pelo grafo Messenger/GPT-6/convites, antes de ativar WebRTC.

## Evidências principais

Branch histórica:
`feat/mission-136-android-browser-apk-readiness`

HEAD histórico:
`3dd805279a3d1119d042f3e7e40245a6a17608cd`

Manifest histórico:
`e0df2d14b63daae5e1e498bb253c68453a856e2c`

Gradle histórico:
`16fd71683c8bf28b8eca369c1bd7f9e379194f46`

Gradle atual:
`27e5311ee96856ba4edb56cb18100d04d696d5e6`

Manifest atual:
`dc103c2cfa298c508e38f52e4957e9433d443514`

## Regra para M254

M254 deve fazer **port seletivo em pequenos lotes**, com compilação/testes verificáveis entre lotes. Não deve importar a árvore M136 inteira e não deve tocar no canal Release/assinatura do dispositivo.
