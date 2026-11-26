# Missão 197 — verificação de perfil e prontidão de aceitação Android

## Objetivo
Fortalecer a prova de atribuição MULTI_PROFILE e explicitar o que ainda falta para validar AI-01 e AI-02 em dispositivo físico.

## 10 rodadas

| Rodada | Trabalho verificável | Resultado |
|---|---|---|
| 01/10 | Reconsultar PR #199 e CI final M196 no HEAD `5eaee2ea57f54f72250c9e492091500d3ab8be2e`. | PASS |
| 02/10 | Confirmar execução PR #45745524819: `debug-build` SUCCESS, `release-preparation` SUCCESS, `release-final` SKIPPED. | PASS |
| 03/10 | Confirmar testes JVM `:app:testDebugUnitTest` com BUILD SUCCESSFUL; build debug também SUCCESSFUL. O log não expõe contagem total de testes, então não atribuir número global. | PASS |
| 04/10 | Confirmar artefatos M196: debug ID `15083585832` (26,054,468 bytes) e release-preparation ID `15082853449` (25,586,428 bytes). | PASS |
| 05/10 | Auditar o uso de AndroidX WebKit 1.18.0 e confirmar API `WebViewCompat.getProfile` para ler perfil atribuído. | PASS estático |
| 06/10 | Identificar que o app marcava isolamento suportado após `setProfile` sem conferir o nome do perfil efetivamente associado. | FALHA DE VERIFICAÇÃO ENCONTRADA |
| 07/10 | Implementar read-back `getProfile(webView).getName()` e só aceitar a atribuição se o nome retornado for exatamente igual ao profileId solicitado. | PASS em código |
| 08/10 | Adicionar dois testes JVM: nome retornado igual; divergente/nulo/vazio bloqueado. | PASS em código; CI M197 pendente |
| 09/10 | Revisar aceitação física e registrar que limpeza individual de perfil ainda não existe; proibir limpeza global como substituto. | PASS documentação |
| 10/10 | Preparar PR Draft M197 sem merge, deploy, instalação ou login. | PASS |

## Evidência CI herdada M196
- PR #199: https://github.com/vidift-max/ai-bridge-browser/pull/199 — Draft, aberta e não mesclada.
- HEAD M196: `5eaee2ea57f54f72250c9e492091500d3ab8be2e`.
- Run PR #45745524819: SUCCESS.
- Jobs: `debug-build` SUCCESS; `release-preparation` SUCCESS; `release-final` SKIPPED.
- Log confirma `:app:testDebugUnitTest`, `:app:assembleDebug` e preparação release concluídos.
- Artefatos: debug `15083585832`; release-preparation `15082853449`.
- Essa evidência valida o HEAD M196, não as alterações posteriores da M197.

## Mudanças M197
- `MainActivity`: após `WebViewCompat.setProfile`, consulta `WebViewCompat.getProfile(webView).getName()`; somente considera isolamento válido se o nome real corresponder ao profileId solicitado.
- `SessionIsolationPolicy`: nova regra pura `isAssignedProfile(expected, actual)`.
- `SessionIsolationPolicyTest`: dois testes novos cobrem correspondência e bloqueio de mismatch/nulo/vazio.
- Checklist físico atualizado para exigir read-back de perfil.
- Checklist agora declara claramente que o aplicativo não implementa limpeza individual de perfil; não usar APIs globais como substituto.

## Referência técnica
A documentação oficial AndroidX WebKit descreve perfis separados e as APIs `WebViewCompat#setProfile`, `WebViewCompat#getProfile`, `ProfileStore` e dados por perfil:
https://developer.android.com/jetpack/androidx/releases/webkit

## Bloqueios
- CI do HEAD M197 ainda precisa concluir.
- Teste físico com WebView instalado e duas contas ChatGPT distintas ainda não realizado.
- Logout/limpeza independente não pode receber PASS: fluxo dedicado ainda não foi implementado.
- Primeira comunicação AI-01 ↔ AI-02 continua não autorizada e não realizada.
- Não há evidência de isolamento real de cookies/sessões no dispositivo.

## Conclusão
**PASS** na verificação de read-back implementada e na documentação de limites. **BLOCKED** para CI do HEAD M197 e validação física. M196 está aprovado no CI, mas isso não equivale à prova física. Escopo permanece somente AI-01 e AI-02.
