# M247 — Evidência visual do APK e vínculo com a identidade do AI-PHONE

Data: 2026-11-26

## Objetivo

Registrar e avaliar a nova captura de tela do Analisador do AI-PHONE, relacionando os dados visíveis com a configuração Android do repositório. A missão não instala, publica, mescla, remove nem altera credenciais.

## Evidência de origem

Captura enviada pelo usuário nesta conversa: tela "AI-PHONE — Analisador".

Dados legíveis na captura:
- 2.584 classes.
- "Nenhum rastreador encontrado".
- 22 bibliotecas listadas.
- Checksum MD5 do APK: `1041fa3be74be84d788c31612d616bf`.
- Checksum SHA-1 do APK: `338d8bbe1590597460502db34e20b4407dca4c7e`.
- Checksum SHA-256 do APK: `3ee1145ad39e5604e8c28c46ef16f09b7df42dd816784b82a607e44d58ce2f78`.
- Assinatura: "Verificado".
- Esquema de assinatura: v2.
- Emissor: `C=US,O=Android,CN=Android Debug`.
- Algoritmo: `SHA256withRSA`.
- SHA-256 do certificado: `861f7689b6502c8dd7b3dcb8f0c9484816e662d8c4cad8ae8da98d5aacfa8ea5`.

## Dez rodadas verificáveis

### 01/10 — Leitura da tela e identificação do analisador
**PASS.** A captura identifica a tela como "AI-PHONE — Analisador". Ela constitui evidência visual fornecida pelo usuário, não inspeção independente do APK pelo agente.

### 02/10 — Verificação da assinatura
**PASS LIMITADO.** O analisador mostra "Verificado" e esquema v2. Isso sustenta que o analisador reconheceu a assinatura do APK examinado como válida segundo sua verificação. Não comprova que o APK seja o pacote Android esperado.

### 03/10 — Fingerprint do certificado
**PASS COMO EVIDÊNCIA VISUAL.** A captura mostra SHA-256 do certificado `861f7689b6502c8dd7b3dcb8f0c9484816e662d8c4cad8ae8da98d5aacfa8ea5`, igual ao fingerprint informado anteriormente pelo usuário. O emissor mostrado é `Android Debug`.

### 04/10 — Separação entre hash do APK e hash do certificado
**PASS.** O SHA-256 do APK é `3ee1145ad39e5604e8c28c46ef16f09b7df42dd816784b82a607e44d58ce2f78`; o SHA-256 do certificado é `861f7689b6502c8dd7b3dcb8f0c9484816e662d8c4cad8ae8da98d5aacfa8ea5`. São valores distintos e representam objetos diferentes. Não usar o checksum do APK como fingerprint de assinatura.

### 05/10 — Algoritmo e esquema
**PASS COMO DADO EXIBIDO.** A tela informa algoritmo `SHA256withRSA` e esquema v2. O registro é fiel à captura; não foi feita validação criptográfica independente dos bytes do APK nesta missão.

### 06/10 — Tipo de certificado
**PASS COMO DADO EXIBIDO; BLOQUEIO PARA RELEASE.** O emissor é `C=US,O=Android,CN=Android Debug`. Portanto, esta evidência corresponde a certificado identificado como Debug, não comprova o certificado de uma Release oficial.

### 07/10 — Identidade de pacote no repositório
**PASS NO CÓDIGO.** A configuração Gradle do projeto declara `applicationId = com.vidiftmax.aibridgebrowser`. O Manifest de referência enviado pelo usuário também declara esse pacote conforme a auditoria M246. Isso confirma a identidade pretendida no código, mas não vincula, por si só, a captura a esse pacote instalado.

### 08/10 — Vínculo entre a captura e o pacote instalado
**BLOCKED.** A captura não exibe o nome completo do pacote Android, nem uma tela de detalhes do aplicativo que associe o APK analisado a `com.vidiftmax.aibridgebrowser`. Assim, ainda não é possível afirmar com prova visual direta que o fingerprint mostrado pertence ao pacote específico instalado.

### 09/10 — Vínculo entre checksum e artefato candidato
**BLOCKED.** Não foi fornecido um APK binário candidato para comparar com o checksum `3ee1145ad39e5604e8c28c46ef16f09b7df42dd816784b82a607e44d58ce2f78`. A busca no repositório não encontrou referência versionada a `app-release.apk` nem artefato Release correspondente. Não há comparação binária nem atestação de proveniência.

### 10/10 — Decisão de atualização
**BLOCKED PARA ATUALIZAÇÃO IN-PLACE.** A captura fortalece o registro do certificado Debug e separa corretamente o checksum do APK do fingerprint do certificado. Entretanto, não revela o package ID do APK analisado e não comprova assinatura compatível com um APK Release. A incompatibilidade funcional do Manifest candidato registrada na M246 também permanece sem correção demonstrada.

## Próxima evidência necessária do usuário

No App Manager, abrir os detalhes do mesmo AI-PHONE e capturar a tela que mostre explicitamente o nome do pacote / Package name / Application ID. O valor esperado a confirmar é:

`com.vidiftmax.aibridgebrowser`

Se o App Manager oferecer uma ação "Compartilhar APK" ou exportar o APK, não é necessário desinstalar nem alterar o aplicativo. O usuário pode enviar apenas a tela de detalhes do pacote; não compartilhar chaves privadas, senhas ou tokens.

## Decisão final

- Assinatura APK v2 reconhecida como verificada pelo analisador: **PASS limitado**.
- Fingerprint SHA-256 do certificado registrado: **PASS como evidência visual**.
- SHA-256 do APK registrado separadamente: **PASS como evidência visual**.
- Associação entre fingerprint e package ID específico: **BLOCKED**.
- Compatibilidade com Release: **BLOCKED**.
- Atualização in-place: **NÃO AUTORIZADA / NÃO EXECUTADA**.

Nenhum merge, Release, workflow_dispatch, instalação, desinstalação, limpeza de dados ou alteração de Secrets foi executado. AI-01 e AI-02 continuam no escopo; AI-03 permanece desativada.
