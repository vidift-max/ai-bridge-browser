# Missão 196 — gate fail-closed de isolamento AI-01 / AI-02

## Objetivo
Impedir que uma WebView sem atribuição efetiva de AndroidX WebKit `MULTI_PROFILE` receba identidade de IA. Garantir que trabalho pendente continue vinculado ao par exato `tabId/profileId` e que itens obsoletos não sejam redirecionados a outra aba.

## Escopo
- Contas ativas nesta missão: somente AI-01 e AI-02.
- Capacidade futura 20 continua sendo apenas teto arquitetural.
- Sem instalação, login, envio automático, publicação de regras, merge ou deploy.
- Sem uso de API paga ou credenciais de provedores externos.

## 10 rodadas verificáveis

| Rodada | Trabalho | Resultado |
|---|---|---|
| 01/10 | Revalidar execução push M195 #45745131461: `debug-build` e `release-preparation` concluídos com sucesso; `release-final` skipped. | PASS |
| 02/10 | Revalidar execução PR M195 #45745141288: os três jobs concluíram; debug e preparação release SUCCESS, release-final SKIPPED. | PASS |
| 03/10 | Confirmar no log do job 139659241544 que `:app:testDebugUnitTest` e `:app:assembleDebug` finalizaram sem erro. | PASS CI |
| 04/10 | Confirmar artefatos de debug e preparação release da execução PR: IDs 15083665120 e 15082981628. | PASS |
| 05/10 | Confirmar que a preparação release é apenas preparação; assinatura final não foi executada nem habilitada no PR. | PASS |
| 06/10 | Auditar `MainActivity.addTab`: `setProfile` ocorre antes de settings/clientes/navegação e a feature é verificada com `MULTI_PROFILE`. | PASS estático |
| 07/10 | Identificar falha de política: mesmo com `sessionIsolationSupported=false`, a aba podia receber registro AI-01/AI-02. | FALHA ENCONTRADA |
| 08/10 | Corrigir a atribuição em abas novas e restauradas: só registrar/restaurar identidade de IA se MULTI_PROFILE realmente tiver sucesso. Adicionar comparação exata de `tabId/profileId` e descartar itens de fila obsoletos sem retarget. | PASS em código |
| 09/10 | Adicionar `SessionIsolationPolicy` e cinco testes JVM; ampliar os filtros Android CI para push M196 e PRs destinados à base M195. | PASS em código; CI M196 pendente |
| 10/10 | Criar checklist de aceitação física e abrir PR Draft sem merge. | PASS documentação; BLOCKED teste físico |

## Evidência CI herdada da M195
- Run push: [45745131461](https://github.com/vidift-max/ai-bridge-browser/actions/runs/45745131461) — SUCCESS.
- Run pull_request: [45745141288](https://github.com/vidift-max/ai-bridge-browser/actions/runs/45745141288) — SUCCESS.
- Job de debug executou testes JVM, build debug e upload do APK.
- Job de preparação release executou `assembleRelease` e upload do APK de preparação.
- Artefatos da execução PR: debug ID `15083665120` (26,054,345 bytes); release-preparation ID `15082981628` (25,585,571 bytes).
- `release-final` foi SKIPPED, conforme esperado.
- Esses resultados são da M195, não da nova alteração M196.

## Mudanças M196
- `MainActivity`: não registra nem restaura painel AI para WebView se MULTI_PROFILE não foi atribuído; procura destino de fila pelo par exato de IDs; remove da fila itens cujo par não existe mais, sem enviá-los a outra aba.
- `SessionIsolationPolicy.java`: regra pura e testável para gate de conta e identidade exata de fila.
- `SessionIsolationPolicyTest.java`: cinco testes cobrindo gate, identidade exata, divergência de aba, divergência de perfil e IDs vazios.
- `.github/workflows/android-build.yml`: habilita CI na branch M196 e quando PR é destinado à branch M195.

## Critérios ainda bloqueados
- CI do HEAD M196 precisa concluir com sucesso.
- Teste físico no Android precisa confirmar suporte real do WebView instalado a MULTI_PROFILE.
- Criar exatamente dois perfis, autenticar manualmente duas contas ChatGPT distintas e verificar alternância/reinício/logout independente.
- Validar que apagar dados de um perfil não afeta o outro.
- Primeira comunicação AI-01 ↔ AI-02 continua não autorizada e não realizada.
- Sem evidência de dispositivo físico, não declarar sessões independentes prontas.

## Conclusão
**PASS** na correção estática do gate e na cobertura JVM adicionada. **BLOCKED** na validação CI da nova branch e nos testes físicos. Nenhuma conta foi autenticada, nenhum texto foi enviado automaticamente e nada foi mesclado ou implantado.
