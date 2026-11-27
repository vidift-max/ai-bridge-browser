# M299 — endurecimento do DOM bridge e reconciliação de capacidade Android

## 01/10 — Estado inicial
**PASS.** PR #242 permaneceu OPEN/Draft/não merged. HEAD de referência da M298: `a6bfff8be118a619b15b11c6c134ea302e015a20`. Escopo mantido em AI-01/AI-02; AI-03 não ativada.

## 02/10 — Auditoria do caminho real de envio
**PASS.** O caminho próprio de primeiro contato usa `ChatGPTDomBridge.send()`, que chama `prepareAndSend(document,text)`. A fila genérica `deliverPendingMessages()` continua fail-closed e não injeta texto automaticamente. Portanto não há mistura entre a fila genérica e o relay AI-01↔AI-02.

## 03/10 — Auditoria do ciclo de vida
**PASS.** Navegação interrompe o orquestrador em `onPageStarted`; crash do renderer descarta a aba; `onStop()` e `onDestroy()` também chamam `stop()`. Pausar a automação cancela o relay. Não foi necessário alterar esse comportamento.

## 04/10 — Endurecimento da descoberta do composer
**PASS.** O DOM bridge agora prioriza contenteditable com role textbox e acrescenta seletores para Lexical e elementos identificados como composer antes do fallback textarea/contenteditable genérico. Isso reduz dependência de um único tipo de editor sem afirmar que os seletores atuais do site foram provados em um dispositivo real.

## 05/10 — Endurecimento do evento de input
**PASS.** `setComposerValue()` agora usa `InputEvent` quando disponível e possui fallback seguro para `Event`. A mudança preserva o envio pelo botão existente e não altera autenticação, cookies ou sessão.

## 06/10 — Teste determinístico do DOM bridge
**PASS.** Criado `scripts/tests/test_chatgpt_dom_bridge.js`. O teste cobre envio por contenteditable, envio por textarea, leitura da última resposta e bloqueio quando o composer não existe.

## 07/10 — Reconciliação da capacidade de abas
**PASS.** `MainActivity.MAX_TABS` estava em 6 enquanto a arquitetura/política do projeto já suporta 20 registros. Foi alinhado para 20. Isso não ativa AI-03 nem aumenta o limite operacional da missão: a política atual continua permitindo somente AI-01 e AI-02.

## 08/10 — CI adversarial e correção
**BLOCKED temporário, resolvido.** A primeira execução do novo teste falhou por duas causas do próprio fixture Node: comparação cross-realm com `deepStrictEqual` e ausência de `HTMLTextAreaElement` no sandbox. Não era falha do APK. As duas causas foram corrigidas no teste. Os runs intermediários foram descartados como validação final.

## 09/10 — CI final
**PASS.** Run `45983725257`, commit `9854db792f6ded9ef1d0adeb66c77d9666072135`: Android unit tests SUCCESS; Manifest generator SUCCESS; DOM bridge contract test SUCCESS; Debug APK build SUCCESS; Release-final SKIPPED.

## 10/10 — Veredito
**PASS para endurecimento técnico; NO-GO para primeiro contato físico.**

### Alterações finais
- DOM bridge: contenteditable/Lexical/composer selectors + InputEvent fallback.
- Teste Node determinístico do contrato DOM.
- CI passou a executar o teste DOM.
- Capacidade estrutural de abas alinhada a 20.
- Nenhuma alteração de Firebase, Secrets, signing keys, release, deploy ou instalação.
- Nenhum login automático foi criado.
- Nenhuma prova física de duas contas ChatGPT foi fabricada.

### Evidência final
- HEAD: `27af5ec70e445c15f4aa59f9ae56b3cf90a0b46f`
- CI: `45983569402` — SUCCESS
- Release: SKIPPED
- PR #242: OPEN / Draft / não merged
- Primeiro contato físico AI-01↔AI-02: ainda pendente.

## Limite importante

O teste novo valida o contrato JavaScript em um DOM simulado. Ele **não** prova que os seletores correspondem ao ChatGPT atualmente servido no Android nem prova duas contas reais. Essa prova só poderá ser feita no aparelho, com as duas sessões autenticadas e isoladas.
