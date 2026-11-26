# Missão 198 — correção do CI Android e requisitos de onboarding

## Objetivo
Investigar o CI ausente da M197, corrigir os filtros do workflow Android e registrar os requisitos solicitados para atualização dentro do app e seleção de conta Google antes do login ChatGPT.

## 10 rodadas

| Rodada | Trabalho verificável | Resultado |
|---|---|---|
| 01/10 | Reconsultar PR #200, branch e HEAD M197. | PASS — PR #200 aberta, Draft, não mesclada; HEAD `9f60f2e6f488ecaa8f773d9d1e11b573f15da26b`. |
| 02/10 | Verificar estado de merge e diff atual da PR #200. | PASS — `mergeable=true` na consulta M198; não houve merge. |
| 03/10 | Consultar runs associados ao HEAD M197. | BLOCKED — wrapper de runs por commit retornou lista vazia; isso não prova falha de build, apenas ausência de run PR observável. |
| 04/10 | Auditar `.github/workflows/android-build.yml`. | FALHA ENCONTRADA — M196 estava duplicada no filtro push; M196 não constava como base permitida em pull_request, apesar de PR #200 usar M196 como base. |
| 05/10 | Inspecionar configuração Android e estado de autenticação. | PASS — `applicationId=com.vidiftmax.aibridgebrowser`, `versionCode=1`, `versionName=0.1.0`; MainActivity abre ChatGPT em WebView e não possui seletor nativo de conta Google identificado nesta auditoria. |
| 06/10 | Definir contrato seguro de atualizações in-app. | PASS documentação — versão, manifesto HTTPS, hash, assinatura, mesmo package/certificado, incremento versionCode e confirmação do instalador Android. |
| 07/10 | Definir fluxo de seleção Google/ChatGPT sem contornar OAuth. | PASS documentação — escolha da conta e continuação pelo login oficial; nenhuma coleta de senha, cópia de cookies ou promessa de login automático. |
| 08/10 | Corrigir filtros do workflow Android em branch isolada M198. | PASS em código — remove duplicação, adiciona M196 e M197 como bases PR e adiciona branch M198 ao push. |
| 09/10 | Criar especificação dos dois requisitos e indexá-la no README. | PASS documentação — `docs/ANDROID_UPDATE_AND_GOOGLE_ACCOUNT_SELECTION.md`. |
| 10/10 | Abrir PR Draft #201, verificar mergeability e observar CI. | PASS operacional — PR #201 aberta, Draft, não mesclada, `mergeable=true`; push run #45746980170 observado. Jobs debug-build e release-preparation estavam em andamento na última consulta. |

## Evidências

- PR M197: https://github.com/vidift-max/ai-bridge-browser/pull/200
- PR M198: https://github.com/vidift-max/ai-bridge-browser/pull/201
- HEAD M197 auditado: `9f60f2e6f488ecaa8f773d9d1e11b573f15da26b`.
- Branch M198: `feat/mission-198-ci-and-android-onboarding`, criada a partir do HEAD M197.
- Correção inicial do workflow: `f241948a272bf29e3adc8a6bef78765c65fc99fd`.
- Especificação: `bcff77dd838b2368b10ca712715857dc624df69c`.
- Índice README: `d5876d01449e03549db0e3c3e1d9769872b8e762`.
- Correção adicional do regex de assinatura: `1dc75657e43a7a9095b3a9b190c5d06e56636848`.
- Workflow corrigido: `.github/workflows/android-build.yml`.
- Documento de requisitos: `docs/ANDROID_UPDATE_AND_GOOGLE_ACCOUNT_SELECTION.md`.

## Diagnóstico CI M197

O workflow da M197 tinha:
- `feat/mission-196-session-isolation-gate` repetida no filtro de push.
- `feat/mission-196-session-isolation-gate` ausente do filtro `pull_request.branches`, embora essa fosse a base de PR #200.
- A branch M197 estava listada no push, mas a configuração de PR não estava completa.

M198 corrige os filtros e inclui a base M197 para PRs desta linha de trabalho. O workflow também foi reformatado e o padrão de busca de arquivos de assinatura foi conferido para manter escapes de regex corretos.

## CI M198

- Run Android Build #45746980170.
- Evento: `push`.
- HEAD inicial do run: `24b3972e707d1711cf6909ba8cfb4e9100f3e6c8`.
- No último fetch, `debug-build` estava executando `:app:testDebugUnitTest`; `release-preparation` estava configurando Gradle; `release-final` estava SKIPPED, conforme esperado para evento push.
- Esse run começou antes da correção final do escape do regex, embora a etapa release-final que o utiliza estivesse SKIPPED. É necessário validar o novo HEAD após a correção.
- O wrapper de runs por commit filtra apenas eventos pull_request; para push, a lista de Actions foi consultada pela API de runs.

## Requisitos novos formalizados

### Atualizações dentro do app
A área Atualizações deverá mostrar versão instalada, consultar versão nova, exibir notas, baixar, validar hash/assinatura e encaminhar ao instalador Android. O Android pode exigir confirmação do usuário. O mesmo applicationId e certificado de release devem ser preservados; versionCode aumenta a cada versão. APK debug e release-preparation nunca serão publicados como atualização final.

### Seleção de conta Google
A interface deverá oferecer escolha de conta antes do login ChatGPT e seguir pelo fluxo oficial Google/ChatGPT. Escolher Gmail não garante sessão automática: depende de vínculo e autenticação autorizada. Não armazenar senha, copiar cookies entre perfis nem interceptar OAuth. AI-01 e AI-02 permanecem isoladas.

## Limites / bloqueios
- CI do HEAD final M198 ainda precisa de execução observável e resultado final.
- Nenhuma tela de atualização, manifesto ou download in-app foi implementado nesta missão; foram definidos requisitos e critérios de aceite.
- Nenhum seletor nativo Google foi implementado nesta missão; foi definido o comportamento seguro.
- Assinatura de release e canal de distribuição continuam dependentes de configuração aprovada e segredos protegidos.
- Teste físico com duas contas e WebView MULTI_PROFILE continua pendente.
- Não houve login, envio de mensagem, instalação, release, publicação, deploy ou merge.
- Escopo permanece AI-01 e AI-02; não ativar AI-03+.

## Conclusão
**PASS** para diagnóstico estático, correção dos filtros e documentação dos requisitos. **BLOCKED** para CI efetivamente concluído no HEAD final, APK de release assinado, atualização in-app funcional, seletor Google funcional e aceitação física. A PR #201 permanece Draft e não mesclada.
