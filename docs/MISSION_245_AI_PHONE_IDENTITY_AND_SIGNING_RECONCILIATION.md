# M245 — Reconciliação de identidade do AI Phone / AI Bridge Browser e assinatura

Data: 2026-11-26

## Objetivo

Reconciliar a identificação do aplicativo Android integrado, registrar a evidência de assinatura informada pelo usuário e definir o estado seguro da atualização. Esta missão não publica, instala, remove nem atualiza APKs.

## Dez rodadas verificáveis

### 01/10 — Identidade do repositório
**PASS.** Repositório auditado: `vidift-max/ai-bridge-browser`. A branch de trabalho da M241 é `feat/mission-241-updater-backport-v2-saas-alpha`.

### 02/10 — Identidade do pacote Android
**PASS.** Em `app/build.gradle.kts`, tanto `namespace` quanto `applicationId` são `com.vidiftmax.aibridgebrowser` na branch da M241.

### 03/10 — Nome visível do aplicativo
**PASS.** Em `app/src/main/AndroidManifest.xml`, o label da aplicação é `AI-PHONE`. Portanto, o App Manager pode exibir o nome AI-PHONE, embora o pacote seja o pacote Android usado pelo projeto AI Bridge Browser. Não se deve exigir que apareça um segundo aplicativo independente chamado AI Bridge Browser.

### 04/10 — Manifesto e componentes integrados
**PASS.** O Manifesto da branch M241 declara HomeActivity como launcher e inclui MessengerActivity, MainActivity e UpdateCenterActivity, além do FileProvider. A evidência de código confirma que a experiência de navegador/atualizador está no aplicativo identificado visualmente como AI-PHONE.

### 05/10 — Versão candidata
**PASS COM LIMITE.** A branch M241 declara `versionName=0.2.0` e `versionCode=2`. A branch padrão `v2-saas-alpha` ainda declara `0.1.0` / `1`. A versão da branch não prova qual versão está instalada no tablet.

### 06/10 — Evidência de certificado fornecida
**PASS COMO EVIDÊNCIA INFORMADA; NÃO COMO ATTESTATION INDEPENDENTE.** O usuário forneceu um relatório App Manager com esquema v2, certificado X.509, assunto/emissor `CN=Android Debug`, algoritmo `SHA256withRSA` e fingerprint SHA-256:
`861f7689b6502c8dd7b3dcb8f0c9484816e662d8c4cad8ae8da98d5aacfa8ea5`.
O relatório foi atribuído pelo usuário ao AI Phone integrado com AI Bridge Browser. Não houve acesso independente ao tablet nem verificação direta do pacote pelo agente.

### 07/10 — Reconciliação dos dois fingerprints enviados
**PASS.** O valor enviado inicialmente (`390cd6d35ca8429bd4c7f77727ee909b2c99e4f830237cd5c1940195b7b189f2`) não coincide com o SHA-256 do relatório detalhado (`861f7689b6502c8dd7b3dcb8f0c9484816e662d8c4cad8ae8da98d5aacfa8ea5`). Para esta missão, somente o valor do relatório detalhado fica registrado como fingerprint informado; o valor inicial fica marcado como conflitante/não confirmado e não deve alimentar configuração de Release.

### 08/10 — Revisão do gate de assinatura Release
**PASS NA REVISÃO ESTÁTICA.** O workflow `.github/workflows/android-build.yml` exige os quatro Secrets de assinatura e a variável `AI_PHONE_EXPECTED_SIGNING_CERT_SHA256`; compara o certificado do APK Release com o fingerprint esperado e interrompe a publicação se estiver ausente ou divergente. Nenhum Secret foi lido ou alterado.

### 09/10 — Evidência de CI
**PASS PARA BUILD DEBUG; RELEASE NÃO EXECUTADA.** O commit `ea2880a713f49ef3ad6e19b5f061a49a206e15f3` tem o workflow run `45803369955` (run #1298) concluído com sucesso. O job `debug-build` passou; o job `release-final` foi ignorado, como esperado para evento de PR. Isso não comprova APK Release, instalação ou compatibilidade de assinatura.

### 10/10 — Estado de segurança e decisão
**BLOCKED PARA ATUALIZAÇÃO IN-PLACE.** O certificado informado tem sujeito `Android Debug`. O certificado Release efetivo ainda não foi comparado com esse fingerprint. Não gerar chave nova, não presumir continuidade, não preencher a variável com um fingerprint conflitante e não publicar. Preservar o app e seus dados. A próxima etapa é obter evidência inequívoca de que o fingerprint completo veio da tela de assinaturas do pacote `com.vidiftmax.aibridgebrowser` instalado e, em separado, comprovar o certificado do APK Release assinado antes de qualquer publicação.

## Estado da PR e da cadeia

- PR #234: Draft / aberta / não mergeada no último resultado de busca consultado.
- Branch M241: 11 commits à frente da branch padrão, sem commits atrás no compare consultado.
- Base consultada: `183a478681a3607f8e6612e4d68ab37583a6a5f3`.
- Head consultado: `ea2880a713f49ef3ad6e19b5f061a49a206e15f3`.
- CI no head consultado: debug-build SUCCESS; release-final SKIPPED.
- Não foi executado merge, workflow_dispatch, publicação, instalação, desinstalação, limpeza de dados ou alteração de Secrets.

## Critérios de encerramento

- Identidade reconciliada: AI-PHONE é o rótulo visível; `com.vidiftmax.aibridgebrowser` é o applicationId da implementação auditada.
- Fingerprint detalhado informado: `861f7689b6502c8dd7b3dcb8f0c9484816e662d8c4cad8ae8da98d5aacfa8ea5`.
- Fingerprint inicial `390cd6...`: divergente e não confirmado.
- Diagnóstico de assinatura: certificado Debug informado.
- Atualização: BLOCKED até comparação comprovada entre assinatura instalada e assinatura do APK Release.
- AI-01 e AI-02 permanecem no escopo; AI-03 continua desativada.

## Nota de segurança

O rótulo visível, o nome do repositório e o nome da Activity não substituem a verificação do identificador de pacote. O certificado de Debug não deve ser tratado como certificado de Release. Não desinstalar o aplicativo para contornar divergência de assinatura, pois isso pode causar perda de dados locais.
