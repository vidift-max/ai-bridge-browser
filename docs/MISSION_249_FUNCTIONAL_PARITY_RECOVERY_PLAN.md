# M249 — Plano de recuperação de paridade funcional antes do atualizador

Data: 2026-11-26

## Objetivo

Executar uma auditoria de origem e de CI para determinar se é seguro restaurar na branch do atualizador os componentes que aparecem no Manifest fornecido do AI-PHONE. Esta missão não inventa Activities ausentes nem altera o comportamento do aplicativo sem código-fonte comprovado. Nenhuma instalação, Release, merge ou alteração de credenciais foi executada.

## Baseline verificado

- Repositório: `vidift-max/ai-bridge-browser`
- Branch de trabalho: `feat/mission-241-updater-backport-v2-saas-alpha`
- Base: `v2-saas-alpha`, SHA `183a478681a3607f8e6612e4d68ab37583a6a5f3`
- Head inicial desta missão: `d0f0071d27a781bda0042d014feddd1c2c2c1df6`
- PR #234: aberta, Draft, não mesclada; 17 commits; 45 arquivos; GitHub informou mergeable=true nesta consulta.
- Compare: 17 commits à frente, 0 atrás.
- Capturas do App Manager preservadas em `evidence/ai-phone-package-identity/`.

## Dez rodadas verificáveis

### 01/10 — Revalidação do estado da PR
**PASS.** PR #234 permanece aberta, Draft e não mesclada. Não houve merge nem publicação.

### 02/10 — Revalidação do Manifest candidato
**PASS.** O Manifest atual declara HomeActivity como launcher, MessengerActivity, MainActivity, UpdateCenterActivity e FileProvider. O package namespace/applicationId está configurado no Gradle como `com.vidiftmax.aibridgebrowser`.

### 03/10 — Inventário dos componentes ausentes da referência
**NO-GO PARA PARIDADE.** O Manifest de referência fornecido anteriormente declara MessengerInviteActivity, Gpt6Activity, CollectiveRoomActivity, CollectiveRoomActivityV2 e alias MessengerLauncher. Esses componentes não constam no Manifest candidato auditado.

### 04/10 — Busca de código-fonte dos componentes
**BLOCKED.** Pesquisa no índice GitHub disponível para `MessengerInviteActivity`, `Gpt6Activity`, `CollectiveRoomActivity`, `CollectiveRoomActivityV2` e `MessengerLauncher` não retornou arquivos. A pesquisa do conector cobre o branch padrão, portanto ausência nos resultados não prova ausência em todo histórico ou branches não indexadas. Não criar stubs com base apenas nos nomes.

### 05/10 — Inspeção da HomeActivity candidata
**PASS COM LIMITES.** A HomeActivity atual contém navegação para MainActivity, MessengerActivity e UpdateCenterActivity. O próprio código marca vários serviços como preparação/local-only; isso não equivale a chamadas, salas coletivas ou integração real. A HomeActivity foi preservada na branch candidata e não será substituída por outra tela.

### 06/10 — Inspeção da MainActivity e do contrato de deep links
**NO-GO PARA PARIDADE.** O Manifest candidato declara MainActivity como `exported=false` e não contém o filtro de deep link HTTPS presente no Manifest de referência. A configuração externa de convites/deep links não está restaurada.

### 07/10 — Revisão do atualizador e superfície de instalação
**PASS ESTÁTICO LIMITADO.** A branch contém UpdateCenterActivity, políticas de URL/redirect, verificação de certificado, intenção de instalação e FileProvider. Isso demonstra implementação estrutural e testes unitários associados, não prova de atualização in-place em dispositivo real.

### 08/10 — Revisão do gate de assinatura
**PASS COMO CONTROLE ESTÁTICO.** O workflow exige material de assinatura e variável de fingerprint esperado; compara o SHA-256 do certificado do APK Release antes de gerar/publicar Release. Nenhum Secret foi lido ou alterado. O fingerprint Android Debug informado pelo usuário não deve ser automaticamente tratado como certificado Release.

### 09/10 — CI real do head M248
**PASS DEBUG.** Run Android Build #1304, ID `45811278978`, associado ao commit `d0f0071d27a781bda0042d014feddd1c2c2c1df6`, terminou SUCCESS. Job `debug-build` SUCCESS: testes unitários, teste do gerador de Manifest e build debug. Job `release-final` SKIPPED, conforme esperado para PR sem workflow_dispatch na branch padrão. Isso não é validação de Release nem teste em dispositivo.

### 10/10 — Decisão e plano de recuperação
**BLOCKED PARA IMPLEMENTAÇÃO FUNCIONAL; NO-GO PARA INSTALAÇÃO.** Não foi localizado, nas fontes consultadas, código-fonte verificável dos componentes ausentes. Implementar Activities vazias ou declarar componentes sem implementação real criaria paridade falsa. O próximo passo correto é localizar a origem real (branch, commit, APK de referência ou arquivos-fonte) e fazer um port seletivo, preservando HomeActivity e o atualizador.

## Matriz de estado

| Área | Resultado |
|---|---|
| PR e branch sem merge | PASS |
| HomeActivity atual preservada | PASS |
| Package ID configurado | PASS |
| MessengerActivity | PASS declarativo |
| MessengerInviteActivity e filtros | NO-GO |
| GPT-6 Activity | NO-GO |
| Salas coletivas e alias launcher | NO-GO |
| MainActivity deep link | NO-GO |
| Estrutura do atualizador | PASS estático |
| Gate de certificado Release | PASS estático |
| CI debug #1304 | PASS |
| CI Release | SKIPPED |
| Teste de atualização em dispositivo | NÃO EXECUTADO |
| Instalação in-place | NÃO AUTORIZADA / NO-GO |

## Próximo insumo técnico necessário

Para restaurar a paridade sem adivinhar, precisamos da origem do Manifest completo enviado pelo usuário: idealmente o repositório/branch/commit de onde saiu o AI-PHONE instalado ou os fontes Java/Kotlin correspondentes. Um APK exportado do AI-PHONE também pode ajudar a extrair package, activities, filtros e certificado, mas não substitui código-fonte legível para manutenção. Não desinstalar o aplicativo nem limpar seus dados.

## Limites

Nenhum merge, workflow_dispatch, Release, instalação, desinstalação, limpeza de dados, alteração de Secrets, force-push ou publicação foi executado. Escopo permanece AI-01 e AI-02; AI-03 desativada.
