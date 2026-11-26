# Missão 195 — ativação do CI Android para AI-01 / AI-02

## Escopo
Corrigir o filtro de eventos do workflow Android Build para que PRs da trilha de isolamento de duas contas executem os testes JVM e builds Android. O escopo permanece AI-01 e AI-02; o teto futuro continua 20.

## 10 rodadas

| Rodada | Trabalho verificável | Resultado |
|---|---|---|
| 01/10 | Revalidar PRs #194, #196 e #197: todas abertas, Draft e não mescladas. | PASS |
| 02/10 | Auditar `.github/workflows/android-build.yml`: o filtro pull_request não incluía a branch-base da Missão 193/194. | BLOCKER CONFIRMADO |
| 03/10 | Auditar o projeto Gradle: projeto usa Kotlin DSL em `settings.gradle.kts` e `app/build.gradle.kts`, com módulo `:app`. | PASS |
| 04/10 | Confirmar que o job de testes usa `gradle :app:testDebugUnitTest`, coerente com o módulo incluído. | PASS estático |
| 05/10 | Adicionar `feat/mission-193-two-account-boundary` e `feat/mission-194-profile-restore-guard` aos destinos de pull_request. | PASS em código |
| 06/10 | Adicionar branch da Missão 195 ao filtro de push para validação futura de commits nessa linha. | PASS em código |
| 07/10 | Preservar release-final condicionado a `workflow_dispatch`; não habilitar assinatura em PR. | PASS estático |
| 08/10 | Abrir PR Draft com base na branch M194 para provocar o evento pull_request previsto no filtro. | PASS |
| 09/10 | Consultar execuções Actions associadas à branch e ao HEAD da PR. | Aguardando GitHub Actions |
| 10/10 | Registrar evidências e limitações: CI só será PASS após jobs concluírem; nenhum dispositivo físico foi testado. | BLOCKED até execução |

## Mudança
Somente `.github/workflows/android-build.yml` foi alterado:
- push: inclui `feat/mission-195-android-ci-gate`.
- pull_request: inclui `feat/mission-193-two-account-boundary` e `feat/mission-194-profile-restore-guard`.
- Os comandos de testes/build existentes foram preservados.
- A etapa de assinatura final continua exclusiva de `workflow_dispatch`.

## Critérios
- [x] Corrigir os filtros de eventos para branches M193/M194.
- [x] Manter teste JVM e builds debug/release-preparation existentes.
- [x] Não solicitar nem expor segredos de assinatura.
- [ ] Executar `:app:testDebugUnitTest` no GitHub Actions.
- [ ] Confirmar build debug e release-preparation.
- [ ] Executar teste físico Android de MULTI_PROFILE e isolamento de cookies/storage.
- [ ] Login manual nas duas contas e teste de alternância/reinício/logout.
- [ ] Primeira troca supervisionada AI-01 ↔ AI-02.

## Conclusão
**PASS na correção dos filtros do workflow; BLOCKED na validação até a execução do CI e testes físicos.** Não houve merge, deploy, assinatura final, instalação, login ou envio de mensagens. Nenhuma conta além de AI-01 e AI-02 foi ativada.
