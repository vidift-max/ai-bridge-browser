# M302 — auditoria do núcleo de relay AI-01 ↔ AI-02

## 01/10 — Orquestrador
**PASS.** `TwoAiChatOrchestrator` aceita somente o par AI-01/AI-02, exige prompt não vazio e limita a quantidade de turnos pela política.

## 02/10 — Isolamento no gate
**PASS.** `AiConversationLaunchPolicy` bloqueia identidades ausentes, abas iguais, perfis iguais, perfis não verificados, páginas não prontas e host ChatGPT ausente.

## 03/10 — Perfil real do WebView
**PASS.** `MainActivity` configura o perfil antes das demais operações do WebView e compara o nome retornado por Android com o profileId solicitado.

## 04/10 — Envio
**PASS.** O relay chama exclusivamente `ChatGPTDomBridge.send()`. A fila genérica de mensagens não é usada pelo primeiro contato.

## 05/10 — Resposta nova
**PASS.** A resposta precisa ser diferente do baseline capturado antes do envio.

## 06/10 — Geração observada
**PASS.** O orquestrador exige observar `generating=true` antes de aceitar uma resposta como finalizada.

## 07/10 — Estabilidade
**PASS.** A mesma resposta nova precisa aparecer em pelo menos três leituras consecutivas sem geração ativa.

## 08/10 — Evidência
**PASS.** `AiBridgeEvidence` registra somente turno, AI remetente e quantidade de caracteres; não persiste o texto integral da resposta.

## 09/10 — Ciclo de vida
**PASS.** Navegação, pausa, `onStop`, `onDestroy` e perda do renderer interrompem o orquestrador. Não há execução em background permanente.

## 10/10 — Veredito
**PASS para o núcleo de relay em auditoria estática. NO-GO para prova física.**

A auditoria não substitui a execução no Android. Ainda precisam ser comprovados no aparelho: duas contas autenticadas, dois perfis WebView distintos, composer/send reais do ChatGPT e uma sequência real de turnos.

Nenhum merge, release, deploy, instalação, limpeza de dados/cache, alteração de secrets ou geração de chave foi realizado.