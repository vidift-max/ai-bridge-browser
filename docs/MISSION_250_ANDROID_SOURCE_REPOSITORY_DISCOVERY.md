# M250 — Localização da origem Android e reconciliação de repositórios

Data: 2026-11-26

## Objetivo

Prosseguir a recuperação de paridade funcional do AI-PHONE sem criar Activities fictícias nem importar código de repositórios com finalidade diferente. Auditoria somente leitura dos repositórios GitHub disponíveis e registro documental na branch de trabalho do AI Bridge Browser.

## Repositórios e referências verificadas

- AI Bridge Browser: `vidift-max/ai-bridge-browser`, branch `feat/mission-241-updater-backport-v2-saas-alpha`.
- PR #234: aberta, Draft, não mesclada.
- TokenSaver AI: `vidift-max/tokensaver-ai`.
- Phone-02 service repository: `vidift-max/tokensaver-ai-phone-02`, branch `v2-saas-alpha`, head `62999ae4fb9af7b269bf62b776cfbcc484d76973`.
- Android game base: `vidift-max/GODOT-ANDROID-BASE` — descrição identifica Godot Engine 4 Android APK para GAME LAB; não é evidência de origem do AI-PHONE.

## Dez rodadas

### 01/10 — Revisão do estado da PR #234
**PASS.** PR #234 permanece aberta, Draft e não mesclada. Não foi executado merge nem publicação.

### 02/10 — Busca por repositório Android dedicado
**BLOCKED.** A busca de repositórios disponíveis retornou `ai-bridge-browser`, `tokensaver-ai`, `tokensaver-ai-collaboration`, `tokensaver-ai-phone-02` e `GODOT-ANDROID-BASE`; não identificou repositório dedicado ao código-fonte Android do AI-PHONE.

### 03/10 — Verificação do repositório TokenSaver AI
**PASS COM LIMITE.** Branches e estrutura do repositório foram consultadas. O material conhecido do TokenSaver AI é a aplicação desktop Tauri 2/React/TypeScript/Rust e infraestrutura de Phone Runtime/Team Room; não foi encontrada prova de que contenha o app Android com package `com.vidiftmax.aibridgebrowser`.

### 04/10 — Verificação do repositório tokensaver-ai-phone-02
**PASS.** O README declara que o projeto é aplicativo desktop Windows Tauri 2 + React + TypeScript + Rust. Portanto, o nome “phone-02” não significa que seja o código-fonte Android do AI-PHONE.

### 05/10 — Inspeção do manifesto de importação Phone-02
**PASS.** `PHONE02_IMPORT_MANIFEST.md` identifica a origem como `vidift-max/tokensaver-ai`, SHA `e3014c018baa6cc79c8f245ed27370cc966034cd`, e registra `INITIALIZATION_STATUS=BLOCKED`, destino sem commit criado. O documento não identifica um app Android nativo.

### 06/10 — Inventário recursivo do repositório Phone-02
**PASS.** A árvore recursiva do commit `62999ae4fb9af7b269bf62b776cfbcc484d76973` foi consultada. Não foram encontrados `AndroidManifest.xml`, fontes Java/Kotlin ou projeto Android nativo. O repositório contém serviços e documentos de infraestrutura.

### 07/10 — Busca de símbolos de paridade no AI Bridge Browser
**BLOCKED.** Pesquisa GitHub para `MessengerInviteActivity`, `Gpt6Activity`, `CollectiveRoomActivity`, `CollectiveRoomActivityV2` e `MessengerLauncher` não retornou correspondências. A busca de código cobre o branch padrão; não prova ausência em todo histórico ou branches não indexadas.

### 08/10 — Reavaliação da base Android candidata
**NO-GO PARA PORT AUTOMÁTICO.** A branch candidata contém o navegador e o atualizador, mas as Activities do Manifest fornecido pelo usuário não têm implementações de origem comprovadas nos repositórios consultados. Não criar stubs, não inferir lógica a partir dos nomes e não substituir HomeActivity.

### 09/10 — Método Android tecnicamente correto para identificar pacote/assinatura
**PASS DE PLANEJAMENTO.** A documentação Android recomenda usar `PackageInfo.signingInfo` e APIs atuais de assinatura (em vez do campo legado `signatures`), com suporte a histórico de rotação. Um APK exportado do próprio AI-PHONE, ou uma leitura PackageManager do app instalado, permitiria vincular package name e certificado. Fonte: Android Developers, PackageInfo e SigningInfo. Isso é método futuro; não foi executado em dispositivo.

### 10/10 — Decisão de missão
**BLOCKED PARA RECUPERAÇÃO DE CÓDIGO; NO-GO PARA INSTALAÇÃO.** As fontes consultadas não revelaram o repositório/commit que contém a implementação Android correspondente ao AI-PHONE. O caminho seguro é obter a origem Android verdadeira ou APK exportado para inventário, depois localizar os fontes correspondentes. Nenhum código funcional foi inventado.

## Matriz final

| Item | Resultado |
|---|---|
| PR #234 aberta/Draft/não mesclada | PASS |
| Repositório dedicado AI-PHONE Android encontrado | BLOCKED |
| `tokensaver-ai-phone-02` é app Android | NO-GO — é desktop/service |
| `tokensaver-ai` contém origem Android confirmada | NÃO COMPROVADO |
| Símbolos de Activities encontrados via code search | NÃO |
| Port funcional seguro pode começar | BLOCKED |
| Package + certificado via PackageManager/APK | Método identificado, não executado |
| Instalação/atualização in-place | NO-GO |

## Próximo passo

Quando a origem Android for identificada, comparar Manifest, fontes Java/Kotlin, recursos e dependências com a branch do AI Bridge Browser; fazer port seletivo e testes antes de qualquer APK. Se a origem não estiver em repositório acessível, o único insumo útil do usuário será o link do repositório correto ou um APK exportado do AI-PHONE. Não pedir reinstalação nem limpeza de dados.

## Limites de segurança

Nenhum merge, workflow_dispatch, Release, instalação, desinstalação, limpeza de dados, alteração de Secrets, force-push ou publicação foi executado. AI-01 e AI-02 permanecem no escopo; AI-03 desativada.
