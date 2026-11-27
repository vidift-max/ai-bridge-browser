# M297 — Auditoria de recuperação da paridade Android

Data: 2026-11-27

## Objetivo

Identificar a origem mais provável do Manifest fornecido para o AI-PHONE instalado e determinar se os componentes ausentes da candidata M295 podem ser recuperados com segurança. Escopo: AI-01 e AI-02. Auditoria read-only, com registro documental; nenhum código funcional foi portado nesta missão.

## Dez rodadas verificáveis

### 01/10 — Revalidação da candidata M295
**PASS.** PR #242 permanece OPEN, Draft e não merged. Head SHA atual: `2c99d81157864705ae3f96cf584041971176d7f6`. CI run `45980325360` concluiu SUCCESS nesse SHA; job `debug-build` executou testes Android, testes do gerador de Manifest e build APK Debug. O job Release não foi executado/publicado.

### 02/10 — Identificação da branch com Manifest correspondente
**PASS COMO CORRESPONDÊNCIA DE CÓDIGO.** A branch `feat/mission-224-ai-first-contact-launch`, head `0cb1df90c9d7d98479d0f8b5316dcc05444bb3ab`, contém `app/src/main/AndroidManifest.xml` blob `029adff39c953c86707a4b82cbc87bc592bb931b`. O Manifest declara as Activities e filtros relatados no inventário do app instalado: `HomeActivity`, `MessengerActivity`, `Gpt6Activity`, `MessengerInviteActivity`, `CollectiveRoomActivity`, `CollectiveRoomActivityV2`, alias `MessengerLauncher` e `MainActivity` exportada com deep link HTTPS `/invite`. Também declara os filtros `aibridge://invite`, HTTPS `*.web.app/i/` e permissões de áudio. Isso é forte correspondência estrutural com o Manifest fornecido, mas não é prova criptográfica de que o APK instalado foi construído desse commit.

### 03/10 — Identidade e versão da branch correspondente
**PASS COMO CORRESPONDÊNCIA DE METADADOS.** `app/build.gradle.kts` na branch M224 (blob `16fd71683c8bf28b8eca369c1bd7f9e379194f46`) define package `com.vidiftmax.aibridgebrowser`, minSdk 29, targetSdk 35, versionCode 1 e versionName 0.1.0 — os mesmos valores informados para o app instalado. Isso torna M224 a origem de código mais provável entre as branches auditadas; não identifica sozinho o artefato APK exato.

### 04/10 — Inventário dos componentes ausentes em M295
**PASS.** A árvore M224 possui 92 entradas em `app/src/main`; M295 possui 63. Foram identificados 29 caminhos presentes em M224 e ausentes em M295 (28 arquivos e um diretório), incluindo três assets de onboarding, recursos visuais, atividades de Messenger/convites/GPT-6/sala coletiva, políticas de retenção e componentes de áudio/voz. A ausência é sistêmica, não apenas um erro no Manifest.

Arquivos de Activity ausentes:
- `Gpt6Activity.java` — SHA `54e7d74ca2125de5d5abe788eda339ad407f1aa0`
- `MessengerInviteActivity.java` — SHA `5ab8b68be02e7e6c95b0d9751ede45e355a01fd1`
- `CollectiveRoomActivity.java` — SHA `50545e944ba3c37445b21b99078fe90a5d93a233`
- `CollectiveRoomActivityV2.java` — SHA `74bfd0f984438d77ef32273a7cf6edd95c32585b`

### 05/10 — Dependências de voz e áudio
**NO-GO PARA RESTAURAÇÃO PARCIAL.** `CollectiveRoomActivityV2` referencia `VoiceIceServerConfig`, `WebRtcVoiceEngine`, `VoiceSignalPayload`, controles de sala e classes auxiliares de voz. `WebRtcVoiceEngine` importa `org.webrtc.*`. A branch M224 declara a dependência Android WebRTC fixada `io.github.webrtc-sdk:android:150.7871.08`; M295/M241 não a declara. Também faltam classes de áudio e permissões `RECORD_AUDIO` / `MODIFY_AUDIO_SETTINGS`. Copiar somente Activity/Manifest produziria uma integração incompleta ou falha de compilação.

### 06/10 — Compatibilidade do cliente Messenger
**NO-GO PARA PORTAR APENAS A TELA DE CONVITE.** `MessengerInviteActivity` M224 depende de operações como `isFirebaseTransport`, `redeemGroupInvite`, `getConversation` e `MessengerRetentionPolicy`. O `MessengerHttpClient` M224 (SHA `06507dfda291993dbbf099d38ffbbaf4c7a8b082`) tem 19.729 caracteres e expõe esses métodos. O cliente M295/M241 (SHA `1edf40ff1011a9799fc8005f8f13432c1b0301c5`) tem 7.463 caracteres e não expõe essas operações. Os contratos são diferentes; copiar a Activity isoladamente não compila nem restaura o comportamento.

### 07/10 — Risco de convites Firebase client-driven
**NO-GO PARA REATIVAR CONVITES DO CLIENTE.** A rota M224 usa transporte Firebase para resgatar convites de grupo. As auditorias de segurança anteriores de PR #236 e missões M269–M273 identificaram falhas nas regras/autorizações client-driven, incluindo permissões excessivas e validação incompleta de expiração/consumo. A documentação M224 não substitui essa revisão de segurança. Não reativar criação/resgate de convites Firebase nem tratar o fluxo como pronto para produção. Preferir backend confiável com token hash, destinatário e expiração validados no servidor, admissão/consumo atômicos e testes adversariais.

### 08/10 — Divergência de histórico e risco de merge
**NO-GO PARA MERGE OU CHERRY-PICK AMPLO.** Comparação M241 → M224 retornou `status=diverged`, merge-base `1e947423f61b26fe9bd38fd787c494607b5d44dd`, 1.878 commits à frente e 108 atrás. A PR #228 (base M223, head M224) permanece OPEN/Draft/não merged. Não mesclar a branch M224 inteira sobre M295/M241: o histórico é divergente e contém mudanças de escopo amplo. Usar os blobs apenas como referência para uma recuperação seletiva, após mapear dependências e segurança.

### 09/10 — Diferenças funcionais em MainActivity e preservação do atualizador
**PASS COM BLOQUEIO DE PARIDADE.** `MainActivity.java` M224 (SHA `c8acfb620f75e73e8868678946fd07b1a1aa5680`, 53.382 caracteres) contém cinco métodos que não existem na versão M295 (SHA `b1f5cba8dea324e08d7d2c61d6f19d023d020715`, 48.975 caracteres): `inviteUrlFromIntent`, `onNewIntent`, `openCollectiveRoom`, `openInviteInCurrentTab` e `promptCollectiveRoomUrl`. Isso confirma perda adicional de rotas de convite/sala, além das Activities ausentes. Entretanto, não substituir o MainActivity M295 pelo M224: o candidato M295 inclui a integração de primeiro contato e herda a versão 2/0.2.0 e o atualizador M241. Também não substituir `app/build.gradle.kts` nem workflow M241 pelos arquivos M224: M224 usa versionCode 1/0.1.0 e configuração de assinatura antiga por variáveis de ambiente, enquanto M241 implementa versionCode 2/0.2.0 e gates de Release por Secrets/fingerprint.

### 10/10 — Decisão e plano seguro
**PASS NA DESCOBERTA; NO-GO PARA ATUALIZAÇÃO/RESTAURAÇÃO AUTOMÁTICA.**
- M224 é a melhor correspondência estrutural conhecida para o Manifest e versão do aplicativo instalado.
- M295/M241 é a base com atualizador e integração AI-01/AI-02, mas não preserva toda a superfície Android relatada.
- A restauração completa exige port seletivo de Activities, rotas, assets, políticas, recursos, dependências e contratos Messenger; não basta editar o Manifest.
- Convites Firebase client-driven continuam bloqueados por segurança.
- Não há prova de APK Release assinado nem de continuidade de certificado.

Próximo trabalho técnico recomendado: produzir uma matriz de dependências por componente e recuperar primeiro somente recursos locais/sem transporte remoto, mantendo convites/sala Firebase desativados até backend seguro. Depois integrar os fluxos de sala por transporte autorizado e validar o Manifest mesclado no CI. Só após paridade e assinatura confirmadas pode ser reavaliada atualização in-place.

## Evidências consultadas

- PR #242: OPEN / Draft / não merged; head `2c99d81157864705ae3f96cf584041971176d7f6`.
- M295 CI run `45980325360`: SUCCESS no mesmo SHA.
- PR #228: OPEN / Draft / não merged; head `0cb1df90c9d7d98479d0f8b5316dcc05444bb3ab`.
- M224 Android CI run `45768337547`: SUCCESS; `release-final` SKIPPED.
- Manifest M224 blob `029adff39c953c86707a4b82cbc87bc592bb931b`.
- Gradle M224 blob `16fd71683c8bf28b8eca369c1bd7f9e379194f46`.
- MainActivity M224 SHA `c8acfb620f75e73e8868678946fd07b1a1aa5680`; M295 SHA `b1f5cba8dea324e08d7d2c61d6f19d023d020715`.
- MessengerHttpClient M224 SHA `06507dfda291993dbbf099d38ffbbaf4c7a8b082`; M295 SHA `1edf40ff1011a9799fc8005f8f13432c1b0301c5`.
- Branches M224/M241 comparadas; merge-base `1e947423f61b26fe9bd38fd787c494607b5d44dd`.

## Limites respeitados

Nenhum merge, cherry-pick, alteração de Manifest/código funcional, workflow Release, publicação, deploy, instalação, desinstalação, limpeza de dados ou alteração de Secrets/Variables foi executado.
