# M252 — Recuperação da origem Android histórica do AI-PHONE

Data: 2026-11-26

Branch de trabalho atual: `feat/mission-241-updater-backport-v2-saas-alpha`  
PR atual: #234  
Objetivo: localizar a origem Android que explica o Manifest instalado anteriormente e recuperar evidência verificável antes de qualquer port seletivo.

## Resultado executivo

**PASS — a origem Android histórica foi localizada dentro do próprio repositório.**

A branch histórica `feat/mission-136-android-browser-apk-readiness` contém exatamente os componentes que estavam faltando na branch candidata e no Manifest de referência: `Gpt6Activity`, `MessengerInviteActivity`, `CollectiveRoomActivity`, `CollectiveRoomActivityV2` e o alias `MessengerLauncher`.

Isso muda a conclusão de M250: **não é mais necessário procurar um repositório Android separado para explicar esses componentes.** Eles existiram no próprio `ai-bridge-browser`, em uma branch Android histórica.

A branch histórica também contém uma dependência WebRTC explícita e todo o conjunto de classes de áudio/voz que a branch candidata atual não possui. Portanto, ainda não é seguro copiar somente as quatro Activities sem mapear suas dependências.

## Dez rodadas

### 01/10 — Busca de branches Android
**PASS.** Foram encontradas branches históricas Android, incluindo:
- `feat/mission-136-android-browser-apk-readiness`
- `feat/mission-197-android-acceptance-readiness`
- `feat/mission-198-ci-and-android-onboarding`
- `feature/android-phone-registry-client-m36`

### 02/10 — Manifest histórico M136
**PASS FORTE.** O Manifest da M136 contém:
- label `AI-PHONE`;
- `HomeActivity`;
- `MessengerActivity`;
- `Gpt6Activity`;
- `MessengerInviteActivity`;
- `CollectiveRoomActivity`;
- `CollectiveRoomActivityV2`;
- alias `MessengerLauncher`;
- FileProvider;
- MainActivity exportada com deep link HTTPS.

O SHA do Manifest histórico é `e0df2d14b63daae5e1e498bb253c68453a856e2c`.

### 03/10 — Confirmação das Activities históricas
**PASS.** Os arquivos-fonte foram recuperados diretamente da branch M136:
- `Gpt6Activity.java` — blob `54e7d74ca2125de5d5abe788eda339ad407f1aa0`
- `MessengerInviteActivity.java` — blob `5ab8b68be02e7e6c95b0d9751ede45e355a01fd1`
- `CollectiveRoomActivity.java` — blob `50545e944ba3c37445b21b99078fe90a5d93a233`
- `CollectiveRoomActivityV2.java` — blob `74bfd0f984438d77ef32273a7cf6edd95c32585b`

### 04/10 — Confirmação da origem de áudio/voz
**PASS.** A árvore histórica contém `AudioRecorder`, `AudioPlayback`, `AudioMonitor`, `WebRtcVoiceEngine`, `VoiceCallSession`, `VoiceSignalPayload`, `VoiceIceCandidateBuffer`, `VoiceIceServerConfig`, `VoiceIceServerConfigVault` e `VoiceRoomControl`.

Isso prova que a funcionalidade de voz não era apenas um nome no Manifest.

### 05/10 — Dependência WebRTC
**PASS / IMPACTO IDENTIFICADO.** O `app/build.gradle.kts` histórico usa `io.github.webrtc-sdk:android:150.7871.08`. A branch candidata atual não possui essa dependência. Portanto, um port seletivo das Activities de sala/voz sem suas dependências seria tecnicamente incompleto.

### 06/10 — Dependências de Messenger
**PASS.** A árvore histórica contém o conjunto de modelos/transportes usados pelas telas: `MessengerHttpClient`, `MessengerRemoteConfig`, `MessengerTransport`, `MessengerSession`, `MessengerMessage`, `MessengerMembership`, `MessengerInvitationDraft`, `MessengerRemoteEnvelope`, `MessengerTransportRecord`, entre outros.

A branch candidata atual mantém boa parte desses arquivos, mas não todos os componentes históricos.

### 07/10 — Comparação da árvore Java
**PASS.** A branch histórica M136 contém dezenas de arquivos Java que não existem na candidata atual. Entre os ausentes estão componentes de áudio, WebRTC, diagnóstico Firebase e suporte de sala coletiva.

Conclusão: o problema não era apenas “Activities faltantes”; existe uma árvore funcional histórica maior.

### 08/10 — Evidência de build histórico
**PASS.** O commit histórico `3dd805279a3d1119d042f3e7e40245a6a17608cd` registra build Android bem-sucedido. O workflow Android Build #1114, run ID `45590339497`, terminou SUCCESS.

O mesmo histórico documenta o Android Build #1112, run ID `45571636197`, com testes, build Debug, upload do APK Debug e preparação de Release bem-sucedidos; a assinatura final foi SKIPPED por ausência de secrets de Release.

### 09/10 — Artefatos históricos ainda disponíveis
**PASS.** O run `45590339497` ainda possui artefatos não expirados:
- `ai-phone-debug-apk`, ID `15009219871`, 26.053.774 bytes, digest do artefato `e886c15d18ae448e0af12cc9272f18b77a86462f5e60e03dadb2dc66bfe81ed8`;
- `ai-phone-release-preparation`, ID `15010532201`, 25.585.319 bytes, digest `67302be01189501eb341f7c9706900703b155865d09cc5ecf6279021a2183faa`.

Os artefatos são de CI histórico e **não devem ser tratados como Release oficial nem como prova de assinatura compatível com o AI-PHONE atualmente instalado**.

### 10/10 — Decisão
**PASS para descoberta da origem; NO-GO para port automático.**

Agora sabemos onde os componentes Android históricos estão. O próximo trabalho deve ser uma recuperação seletiva baseada em dependências:
1. comparar árvore histórica M136 com a candidata atual;
2. separar componentes necessários para o AI Bridge Browser/AI Messenger de componentes não necessários;
3. verificar dependências e testes;
4. portar somente o conjunto necessário;
5. executar CI;
6. somente depois reavaliar compatibilidade do Manifest.

Nenhum arquivo funcional histórico foi copiado para a branch atual nesta missão. Isso foi deliberado para evitar importar uma árvore antiga inteira sem análise.

## Evidência principal

Branch histórica: `feat/mission-136-android-browser-apk-readiness`  
HEAD histórico: `3dd805279a3d1119d042f3e7e40245a6a17608cd`

Manifest histórico e Activities agora estão identificados como origem interna do próprio repositório.

## Limites

Não houve instalação, desinstalação, Release, workflow_dispatch, alteração de Secrets/Variables, merge, force-push ou alteração do aplicativo instalado.

AI-03 permanece desativada. O escopo continua AI-01 e AI-02.
