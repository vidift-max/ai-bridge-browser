# M251 — Auditoria de canal de Release, atualizador e identidade Android

Data: 2026-11-26  
Branch: `feat/mission-241-updater-backport-v2-saas-alpha`  
PR: #234

## Objetivo
Continuar a recuperação segura do AI-PHONE após M250, verificando se já existe um artefato Android oficial, se o atualizador pode encontrar uma Release e se a branch candidata preserva a identidade/assinatura do app instalado. Auditoria somente leitura, seguida de registro documental.

## Dez rodadas verificáveis

### 01/10 — Estado atualizado da PR #234
**PASS.** GitHub retornou PR aberta, Draft, não mesclada, base `v2-saas-alpha`, head `34e1e603d15175e0c4879708a1959fd7210cecf2`. Nesta consulta, `mergeable=true` (diferente do `false` registrado em M250). Isso significa que o GitHub não reportou conflito de merge naquele instante; não é aprovação funcional nem autorização para mesclar.

### 02/10 — Inventário de Releases oficiais
**PASS / BLOQUEIO CONFIRMADO.** A API pública de Releases do repositório retornou lista vazia (`[]`). Portanto, não há atualmente Release publicada para o endpoint `/releases/latest` do atualizador consumir. O próprio código trata HTTP 404 como “ainda não existe versão oficial publicada”. Nenhum workflow de publicação foi disparado.

### 03/10 — Verificação de artefato APK publicado
**BLOCKED.** Não há Release e não foi identificado asset APK oficial associado a uma Release. Um build Debug de CI não equivale a APK Release assinado, nem comprova compatibilidade com o AI-PHONE instalado.

### 04/10 — Comparação do Manifest da branch candidata com a base
**PASS COM DIFERENÇAS.** O Manifest da branch candidata adiciona `REQUEST_INSTALL_PACKAGES`, `FileProvider` e `UpdateCenterActivity`; a base `v2-saas-alpha` não contém esses elementos. Ambos mantêm label `AI-PHONE`, launcher `.HomeActivity`, `.MessengerActivity` e `.MainActivity`. O Manifest enviado pelo usuário anteriormente continha outras Activities/alias/deep link que continuam sem paridade demonstrada. Não declarar equivalência integral.

### 05/10 — Identidade de pacote no código
**PASS NO CÓDIGO; NÃO PROVA NO DISPOSITIVO.** `app/build.gradle.kts` define `applicationId = com.vidiftmax.aibridgebrowser`; o atualizador também fixa esse package. Isso confirma a identidade pretendida da build desta branch, mas não vincula criptograficamente a build ao pacote instalado no telefone.

### 06/10 — Política de assinatura do atualizador
**PASS COM LIMITAÇÃO CONSERVADORA.** `UpdateCenterActivity.verifyPackageAndCertificate` lê `PackageInfo.signingInfo` do app instalado e do APK baixado e compara os conjuntos de signatários por igualdade exata. A política bloqueia pacote/certificado divergente. A implementação não demonstra suporte a rotação de chave por lineage; não relaxar a comparação sem teste específico e prova do histórico de assinatura do app instalado.

### 07/10 — Verificação do hash e origem do APK
**PASS NO CÓDIGO.** O atualizador valida SHA-256 do arquivo baixado, tamanho máximo, metadados de versão, nome do pacote, asset único da Release, HTTPS/redirecionamento e revalida o APK antes de abrir o instalador. Isso é análise estática do código, não teste em dispositivo nem prova de Release funcional.

### 08/10 — Segurança do handoff ao instalador
**PASS NO CÓDIGO; TESTE DE DISPOSITIVO PENDENTE.** O código usa FileProvider com URI `content://`, MIME APK e concessão de leitura; valida autoridade, caminho e flags permitidas. O Android ainda exige confirmação do usuário e permissão de instalação de fontes desconhecidas conforme configuração do aparelho. Nenhuma instalação foi solicitada.

### 09/10 — CI associado ao HEAD
**EM ANDAMENTO NA CONSULTA.** GitHub retornou workflow Android Build #1306, run ID `45812679827`, status `in_progress`, associado ao HEAD consultado. Não registrar PASS até obter conclusão e jobs. Este run pode terminar após esta auditoria; o estado final deverá ser consultado separadamente.

### 10/10 — Decisão operacional
**NO-GO PARA INSTALAÇÃO/ATUALIZAÇÃO; BLOCKED PARA PARIDADE COMPLETA.** Sem Release oficial, sem APK Release, sem certificado instalado vinculado de forma independente e sem origem Android que explique todas as Activities do Manifest fornecido, não há base para instalar ou atualizar in-place. A PR segue Draft e não mesclada.

## Matriz de decisão

| Item | Resultado |
|---|---|
| PR #234 aberta e Draft | PASS |
| PR #234 não mesclada | PASS |
| Mergeability no momento da consulta | PASS técnico (`true`), não autorização |
| Release oficial publicada | NÃO — lista vazia |
| APK Release oficial disponível | BLOCKED |
| Package ID pretendido na branch | PASS no código |
| Package ID instalado provado criptograficamente | PENDENTE |
| Comparação de assinatura no atualizador | PASS estático, igualdade exata |
| Rotação de certificado suportada | NÃO COMPROVADO |
| Manifest integralmente compatível com referência do usuário | NÃO |
| Workflow Android Build #1306 | IN_PROGRESS |
| Instalação/atualização in-place | NO-GO |

## Próximas ações seguras
1. Consultar o resultado final do run #1306 e seus jobs; não inferir sucesso enquanto estiver em andamento.
2. Localizar a origem Android real ou obter APK exportado do AI-PHONE para inventário de package, Activities, versão e assinatura.
3. Confirmar o certificado instalado por evidência direta antes de preencher `AI_PHONE_EXPECTED_SIGNING_CERT_SHA256` ou criar qualquer Release.
4. Resolver a paridade do Manifest com a origem verdadeira antes de considerar build de atualização.

## Limites
Nenhum merge, Release, workflow_dispatch, instalação, desinstalação, limpeza de dados, alteração de Secrets/Variables, force-push ou publicação foi executado. Não foi solicitado ao usuário que altere o aparelho. Escopo continua AI-01/AI-02; AI-03 desativada.
