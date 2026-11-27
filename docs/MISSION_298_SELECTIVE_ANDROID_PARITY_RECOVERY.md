# M298 — Recuperação seletiva da paridade Android

Data: 2026-11-27

## Objetivo

Recuperar somente componentes Android locais e autossuficientes que possam ser integrados à candidata M295 sem introduzir transporte Firebase inseguro, alterar o contrato do Messenger, substituir o atualizador M241 ou ampliar o escopo além de AI-01 e AI-02.

## Dez rodadas verificáveis

### 01/10 — Estado atual da PR e branch
**PASS.** PR #242 permanece OPEN, Draft, não merged e mergeable. Base `feat/mission-241-updater-backport-v2-saas-alpha`, SHA `d2861ab8e257cd07e095c31de708fe4264c89bd2`. Branch de integração `feat/mission-295-m241-ai-first-contact-integration`, HEAD antes da M298 `dc384ea57432c0315efc879cf06b8a749edb4525`.

### 02/10 — Revalidação da divergência M224
**NO-GO PARA MERGE AMPLO.** Comparação atualizada entre M295 e `feat/mission-224-ai-first-contact-launch`: status `diverged`, merge-base `1e947423f61b26fe9bd38fd787c494607b5d44dd`, M224 1.878 commits à frente e 134 atrás. O valor de 108 commits atrás registrado na documentação M297 ficou desatualizado; a consulta atual retorna 134. Nenhum merge/cherry-pick amplo.

### 03/10 — Preservação do pacote e atualizador
**PASS.** A candidata M295 mantém `applicationId=com.vidiftmax.aibridgebrowser`, `versionCode=2`, `versionName=0.2.0`, minSdk 29 e targetSdk 35. Manifest M295 continua restrito aos componentes registrados na base M241; nenhuma Activity de convite, GPT-6 ou sala coletiva foi adicionada. Atualizador, política de assinatura e gates de Release não foram alterados.

### 04/10 — Inventário dos recursos locais
**PASS.** Árvore recursiva da M224 identificou três documentos estáticos de onboarding e dois drawables vetoriais. Os documentos são independentes de Firebase, HTTP, identidade remota e WebRTC. Os drawables encontrados são duplicados entre si (mesmo blob SHA) e não são necessários para a tela atual, portanto não foram copiados.

### 05/10 — Compatibilidade da HomeActivity atual
**PASS COM ESCOPO LIMITADO.** M295 já contém `HomeActivity` e `WifiDeviceDiagnostics`. A tela atual tem seção de missão e diálogo local de apresentação, mas não expõe os três documentos completos. Foi preservada a implementação M295 da HomeActivity e acrescentado somente acesso aos documentos via Android Assets e diálogo com rolagem. Nenhuma Activity M224 inteira foi transplantada.

### 06/10 — GPT-6 standalone
**NO-GO PARA PORT.** `Gpt6Activity` M224 chama `MessengerHttpClient.getGpt6Status()` e `sendToGpt6()`. O cliente M295/M241 não implementa esses métodos: oferece operações de telefone, conversas, mensagens, fetch e ACK. Copiar a Activity isoladamente não compila e não cria integração GPT-6. Nenhuma rota ou API foi inventada.

### 07/10 — Convites e Firebase
**NO-GO PARA PORT/REATIVAÇÃO.** `MessengerInviteActivity` depende de `isFirebaseTransport`, `redeemGroupInvite`, `getConversation` e `MessengerRetentionPolicy`, ausentes no contrato atual do cliente. As auditorias anteriores identificaram riscos em regras client-driven do Firebase. Nenhuma Activity, regra, credencial ou fluxo Firebase foi copiado/ativado.

### 08/10 — Sala coletiva, áudio e WebRTC
**NO-GO PARA PORT PARCIAL.** As Activities coletivas dependem de classes auxiliares de sala/voz, `org.webrtc.*`, dependência `io.github.webrtc-sdk:android:150.7871.08` e permissões de áudio ausentes em M295. Copiar apenas Activities ou Manifest seria incompleto. Nenhuma permissão de microfone ou dependência foi adicionada.

### 09/10 — Recuperação local implementada
**PASS DE CÓDIGO; CI PENDENTE NA CRIAÇÃO DESTE RELATÓRIO.** Foram adicionados à branch M295:
- `app/src/main/assets/AI_PHONE_WELCOME.md` — blob SHA `9e3c867ccafe24a8850f4323d0af4d4399314282`;
- `app/src/main/assets/AI_PHONE_PROJECT_AND_PARTICIPATION.txt` — blob SHA `d8d60975ccabe48f94a02f57d48046afb36767da`;
- `app/src/main/assets/AI_PHONE_WIFI_AND_MESSENGER_GUIDE.txt` — blob SHA `695cd460317fdd9a6a745525d328ce716eba301d`.

A `HomeActivity.java` foi alterada seletivamente para expor três botões de leitura e carregar os arquivos de Assets em um diálogo rolável. Blob SHA resultante: `e306fb2e3421079fbbdda883545e8244e9cafa10`. Nenhum conteúdo de conta, token, senha, cookie ou dado de conversa é lido ou transmitido por esses leitores.

### 10/10 — Veredito e limites
**PASS PARA RECUPERAÇÃO LOCAL DE ONBOARDING. NO-GO PARA PARIDADE COMPLETA, GPT-6, CONVITES, SALA E VOZ.**
- A restauração seletiva ficou limitada a três documentos estáticos e sua visualização local.
- M241 updater, versionCode 2 / versionName 0.2.0, proteção de assinatura e release gates foram preservados.
- AI-01/AI-02 continuam sendo o limite operacional; AI-03 não foi ativada.
- O CI deve validar a compilação no HEAD final desta missão.
- Não há prova de APK Release, instalação, atualização in-place ou teste físico dos documentos.
- Primeiro contato real AI-01 ↔ AI-02 continua pendente de duas sessões ChatGPT autenticadas e isoladas no dispositivo.

## Evidências

- PR #242: OPEN / Draft / não merged.
- Base M241: `d2861ab8e257cd07e095c31de708fe4264c89bd2`.
- HEAD antes da M298: `dc384ea57432c0315efc879cf06b8a749edb4525`.
- Divergência M224 atual: 1.878 ahead / 134 behind; merge-base `1e947423f61b26fe9bd38fd787c494607b5d44dd`.
- M224 Gpt6Activity SHA `54e7d74ca2125de5d5abe788eda339ad407f1aa0`.
- M224 HomeActivity SHA `8bfa3c3e1429d83975e6b253f8239eb7de458826`; M295 HomeActivity anterior SHA `6d7a01257b44eff9fb6aaf300b901bee573675dc`.
- M295 MessengerHttpClient SHA `1edf40ff1011a9799fc8005f8f13432c1b0301c5`.
- Run M297 `45981014522`: SUCCESS, job debug-build SUCCESS, release-final SKIPPED.
- Run inicial do código M298 `45981706991`: em andamento no momento da consulta, antes da inclusão deste relatório; não representa validação do HEAD final da M298.

## Limites respeitados

Nenhum merge, Release, deploy, instalação, desinstalação, limpeza de cache/dados, alteração de Secrets/Variables, credencial Firebase, regra RTDB, permissão de microfone ou integração externa foi executado.
