# M296 — Certificado instalado e prontidão para atualização in-place

Data: 2026-11-27

## Objetivo e limites

Auditar a continuidade da assinatura do AI-PHONE/AI Bridge Browser antes de qualquer atualização. Esta missão é somente de leitura e documentação. Não consulta nem altera GitHub Secrets/Variables, não gera chave, não executa workflow de Release, não publica, não instala e não altera o tablet.

Escopo funcional permanece AI-01 e AI-02. AI-03 permanece fora do escopo.

## Dez rodadas verificáveis

### 01/10 — Estado da integração M295
**PASS.** PR #242 permanece aberta, Draft e não mesclada. Head SHA auditado: `70b86d3348b70acf3012f46f8130b144cc6925fd`, branch `feat/mission-295-m241-ai-first-contact-integration`, base `feat/mission-241-updater-backport-v2-saas-alpha`. O CI run `45979747666` concluiu SUCCESS nesse SHA. Esta evidência não é uma Release assinada.

### 02/10 — Identidade do aplicativo
**PASS NO CÓDIGO.** `app/build.gradle.kts` declara namespace e applicationId `com.vidiftmax.aibridgebrowser`, versionCode 2, versionName 0.2.0, minSdk 29 e targetSdk 35. O Manifest usa label `AI-PHONE`. O pacote é o identificador; AI Bridge Browser é integrado no AI-PHONE, não um segundo pacote Android independente.

### 03/10 — Evidência mais recente do certificado instalado
**PASS COMO RELATO DO USUÁRIO; NÃO COMO ATTESTATION INDEPENDENTE.** O relatório mais recente fornecido para o aplicativo instalado informa:
- Pacote: `com.vidiftmax.aibridgebrowser`
- Assinatura: Android Debug / SHA256withRSA
- SHA-256 do certificado: `5c0b529a5447f7bf9f69ba2ce0c82e99c070a073544fda16301fecf73591696a`
- Hash SHA-256 do APK instalado informado separadamente: `4362cdd8db837e03d5ccd55d152c2b1cfc67fab98342f8696db4adefcd3d8895`
- Versão informada: 0.1.0 / versionCode 1.

O fingerprint do certificado não é o hash do APK. O agente não acessou diretamente o PackageManager do tablet; portanto, registra-se como evidência fornecida, não como leitura independente.

### 04/10 — Reconciliação de fingerprints históricos
**BLOCKED PARA ESCOLHA AUTOMÁTICA.** A documentação anterior M245 registrou um fingerprint detalhado diferente (`861f7689b6502c8dd7b3dcb8f0c9484816e662d8c4cad8ae8da98d5aacfa8ea5`) e também um valor inicial conflitante (`390cd6d35ca8429bd4c7f77727ee909b2c99e4f830237cd5c1940195b7b189f2`). O relatório mais recente apresentado agora informa `5c0b529a5447f7bf9f69ba2ce0c82e99c070a073544fda16301fecf73591696a`. Não misturar nem substituir esses valores em Secrets/Variables por suposição. Para o gate de Release, usar somente o fingerprint confirmado na tela de assinaturas do pacote instalado que efetivamente receberá a atualização; se a evidência mais recente for confirmada como a leitura atual do mesmo pacote, ela substitui o registro histórico para essa instalação.

### 05/10 — Política de assinatura do atualizador
**PASS CONSERVADOR; LIMITAÇÃO DOCUMENTADA.** `UpdateCenterActivity.verifyPackageAndCertificate` obtém `SigningInfo` do pacote instalado e do APK baixado, lê `getApkContentsSigners()` e delega a `SigningCertificatePolicy.areSameSignerSets`. A política exige igualdade exata, um-a-um, de todos os certificados e bloqueia qualquer diferença. Não foi encontrado uso de `getSigningCertificateHistory()` nem prova de suporte a rotação/lineage. Não relaxar essa regra nesta missão.

### 06/10 — Testes de assinatura
**PASS PARA POLÍTICA JVM.** `SigningCertificatePolicyTest` cobre signatário idêntico, ordem diferente, bytes diferentes, signatários ausentes/adicionais, arrays/entradas nulas ou vazias e correspondência um-a-um. Esses testes validam a política pura, não verificam o certificado físico instalado nem um APK Release real.

### 07/10 — Gate do workflow de Release
**PASS ESTÁTICO; RELEASE NÃO EXECUTADA.** `.github/workflows/android-build.yml` exige os quatro Secrets de assinatura e a variável `AI_PHONE_EXPECTED_SIGNING_CERT_SHA256`; constrói o APK Release, verifica com `apksigner` e compara o fingerprint real do artefato com o esperado antes de publicar. O job Release só é elegível por `workflow_dispatch` na branch padrão `v2-saas-alpha`. Nenhum Secret ou Variable foi consultado/alterado e nenhum workflow manual foi disparado.

### 08/10 — Ausência de Release/artefato oficial
**BLOCKED.** A API de Releases do repositório retornou lista vazia. Não há APK Release oficial publicado para download pelo atualizador. O CI M295 produziu build Debug; o job `release-final` foi SKIPPED. Build Debug não é substituto de APK Release assinado.

### 09/10 — Compatibilidade do Manifest
**NO-GO PARA ATUALIZAÇÃO IN-PLACE ATÉ RECONCILIAÇÃO.** A auditoria M246 comparou o Manifest fornecido do app instalado com o Manifest candidato M241 e encontrou ausência de `MessengerInviteActivity`, `Gpt6Activity`, `CollectiveRoomActivity`, `CollectiveRoomActivityV2`, alias `MessengerLauncher`, filtros de deep link e permissões de áudio declaradas na referência. O Manifest presente na branch M295 continua herdado da base M241; a integração do primeiro contato não resolveu essa paridade. Não tratar o APK M295 como atualização compatível do app instalado antes de recuperar/justificar cada componente necessário.

### 10/10 — Decisão operacional
**NO-GO PARA RELEASE/INSTALAÇÃO IN-PLACE; PASS PARA AUDITORIA.**
- A assinatura do app instalado foi reportada como Android Debug.
- Há fingerprints históricos divergentes e nenhuma assinatura Release efetiva foi comparada.
- O atualizador aceita somente igualdade exata dos conjuntos de signatários.
- Não existe Release oficial.
- A paridade completa do Manifest continua pendente.

Não preencher `AI_PHONE_EXPECTED_SIGNING_CERT_SHA256` com valor presumido; não gerar nova chave para tentar substituir a chave existente; não publicar Release; não desinstalar, reinstalar, atualizar ou limpar dados do tablet.

## Gate necessário antes de qualquer atualização

1. Confirmar o fingerprint completo atual diretamente na seção de assinatura do pacote `com.vidiftmax.aibridgebrowser` no tablet e identificar ferramenta/versão/data.
2. Obter, por procedimento autorizado e seguro, o certificado público do keystore que será usado para assinar a Release; comparar localmente com o fingerprint confirmado. Nunca enviar keystore, Base64 ou senhas ao chat.
3. Se a chave que assinou o app instalado não estiver disponível, manter NO-GO para atualização in-place e planejar separadamente uma migração de dados com autorização explícita; não tentar contornar a proteção do Android.
4. Resolver a paridade do Manifest M246 e testar os fluxos preservados.
5. Somente após todos os gates, solicitar autorização específica para o procedimento de Release. A aprovação de CI não autoriza publicação.

## Evidências consultadas

- PR #242, Draft, aberta, não merged; head `70b86d3348b70acf3012f46f8130b144cc6925fd`.
- CI run `45979747666`: SUCCESS no mesmo SHA; testes unitários, testes do gerador e build Debug.
- `SigningCertificatePolicy.java` SHA `44fef2eac2947ef3f9d0decf1cb5c87ef42e9ca2`.
- `SigningCertificatePolicyTest.java` SHA `fa0b454d537bd59caa67e4df239564345c79301c`.
- `UpdateCenterActivity.java`: verificação de `SigningInfo` e igualdade exata dos signatários.
- `app/build.gradle.kts` SHA `27e5311ee96856ba4edb56cb18100d04d696d5e6`.
- `app/src/main/AndroidManifest.xml` SHA `dc103c2cfa298c508e38f52e4957e9433d443514`.
- `docs/MISSION_246_INSTALLED_MANIFEST_COMPATIBILITY_AUDIT.md`.
- API de Releases: lista vazia na consulta de 2026-11-27.

## Ações explicitamente não executadas

Nenhum merge, release, workflow_dispatch, deploy, alteração de Secrets/Variables, geração de chave, instalação, atualização, desinstalação, limpeza de cache/dados ou ação no tablet.


## Adendo M304 — reconciliação da evidência atual (2026-11-27)

Este adendo prevalece sobre a redação histórica da rodada 04/10 acima somente quanto à identificação do certificado atualmente reportado para a instalação examinada. O usuário apresentou novamente o relatório do App Manager, associado ao pacote `com.vidiftmax.aibridgebrowser`, com fingerprint SHA-256 completo:

`5c0b529a5447f7bf9f69ba2ce0c82e99c070a073544fda16301fecf73591696a`

**Resultado atualizado:** PASS como evidência fornecida pelo usuário para o certificado da instalação atual. Os fingerprints históricos `861f7689b6502c8dd7b3dcb8f0c9484816e662d8c4cad8ae8da98d5aacfa8ea5` e `390cd6d35ca8429bd4c7f77727ee909b2c99e4f830237cd5c1940195b7b189f2` permanecem apenas como registros históricos e não devem ser usados para essa instalação atual.

**O que não foi resolvido:** não há evidência do certificado público do keystore de Release que será usado para assinar o APK futuro. Portanto, a igualdade entre o signer da instalação atual e o signer do futuro Release continua BLOCKED. Não alterar `AI_PHONE_EXPECTED_SIGNING_CERT_SHA256`, Secrets ou Variables; não gerar chave; não executar Release.

### Atualização M303 da paridade do Manifest

A branch M295 recebeu a recuperação parcial M303. O Manifest atual declara `RECORD_AUDIO` e `MODIFY_AUDIO_SETTINGS`, registra `.CollectiveRoomActivity` como não exportada e cria o alias exportado `.MessengerLauncher` apontando para essa Activity local. Isso resolve somente a presença desses três elementos no candidato. Não equivale à Activity remota V2 nem restaura os filtros/handlers de convite e deep link.

Continuam ausentes/integrados de forma incompleta: `MessengerInviteActivity`, `Gpt6Activity`, `CollectiveRoomActivityV2`, WebRTC e handlers compatíveis de deep link. O alias atual aponta para `CollectiveRoomActivity`, não para V2. O Gradle atual não declara dependência `org.webrtc`; importar a implementação V2 sem fechar essa dependência/API seria inseguro.

### Estado atual da revisão

- PR #242: OPEN / Draft / não merged.
- Head: `83b8074a84790bc8a9286f80102a6517e3a2d3e7`.
- O wrapper de status do commit não retornou checks; o wrapper de workflow-runs disponível filtra execuções disparadas por pull_request e não comprova a execução push configurada para esta branch. Logo, CI para essa HEAD: NÃO COMPROVADO.
- M303 adicionou testes JVM para codec e retenção, mas não há resultado de execução confirmado para essa HEAD.
- Nenhum merge, Release, instalação, alteração de Secrets/Variables ou ação no dispositivo.

**Decisão M304:** certificado instalado atual identificado conforme relato do usuário; atualização in-place continua NO-GO até comprovar que o certificado público da chave de Release corresponde a `5c0b529a5447f7bf9f69ba2ce0c82e99c070a073544fda16301fecf73591696a`, restaurar/justificar a paridade funcional do Manifest e obter CI verde na HEAD exata.
