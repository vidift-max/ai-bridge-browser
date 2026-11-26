# Missão 203 — ciclo de vida seguro da Central de Atualizações

## Objetivo
Evitar que tarefas de consulta/download/verificação tentem atualizar componentes visuais depois que UpdateCenterActivity foi encerrada. Preservar o limite operacional AI-01/AI-02; sem expansão de contas.

## 10 rodadas

| Rodada | Trabalho | Resultado |
|---|---|---|
| 01/10 | Revalidar M202 e sua CI no HEAD final. | PASS — PR #205 aberta/Draft/não mesclada; CI PR e push no HEAD `ce2b5e84e75ce02266c01312da327758eda6d301` concluíram SUCCESS; testes JVM e builds Debug/Release preparação passaram; release-final SKIPPED. |
| 02/10 | Auditar callbacks assíncronos da tela de atualização. | PASS — identificados callbacks postados pelo executor para a UI durante consulta, download e verificação. |
| 03/10 | Adicionar política pura de ciclo de vida. | PASS — `UpdaterUiPolicy.shouldDeliver` só permite entrega quando a Activity está ativa. |
| 04/10 | Centralizar a entrega dos callbacks na função `postUi`. | PASS em código — callbacks verificam estado explícito, isFinishing e isDestroyed. |
| 05/10 | Marcar encerramento da Activity antes de encerrar o executor. | PASS em código — `destroyed=true` é definido antes de `shutdownNow()`. |
| 06/10 | Interromper leitura da resposta de metadados após encerramento. | PASS em código — loop verifica flag e interrupção da thread. |
| 07/10 | Interromper loop de download após encerramento. | PASS em código — evita continuar gravando bytes após teardown detectado. |
| 08/10 | Adicionar testes JVM para os estados da política. | PASS em código — 4 casos: ativa, explicitamente encerrada, finishing e framework destroyed. |
| 09/10 | Configurar CI para branch M203 e PR baseada em M202. | PASS — filtros push e pull_request atualizados. |
| 10/10 | Registrar evidências e abrir PR Draft. | PENDENTE DE CI — PR aberta; aguardar execução no HEAD final. |

## Arquivos alterados
- `app/src/main/java/com/vidiftmax/aibridgebrowser/UpdateCenterActivity.java`
- `app/src/main/java/com/vidiftmax/aibridgebrowser/UpdaterUiPolicy.java`
- `app/src/test/java/com/vidiftmax/aibridgebrowser/UpdaterUiPolicyTest.java`
- `.github/workflows/android-build.yml`
- `docs/MISSION_203_UPDATER_LIFECYCLE.md`

## Evidência M202
- PR #205: https://github.com/vidift-max/ai-bridge-browser/pull/205
- CI PR: run `45748469460` SUCCESS.
- CI push HEAD final: run `45748462509` SUCCESS.
- Em ambos: `debug-build` SUCCESS; `release-preparation` SUCCESS; `release-final` SKIPPED.

## Limites e bloqueios
- CI M203 ainda não concluída no momento da abertura desta PR.
- Não houve teste em Android físico.
- Não foi criada nem publicada release oficial; assinatura final permanece indisponível.
- Não houve instalação, merge, ativação de conta, publicação nem acesso/criação de secrets.
- O ciclo de vida agora bloqueia callbacks e verifica interrupção nos loops; não se afirma cancelamento imediato de todas as conexões HTTP bloqueadas em leitura. Timeouts existentes permanecem ativos.
- Seletor de conta Google para login ChatGPT ainda não foi implementado.
