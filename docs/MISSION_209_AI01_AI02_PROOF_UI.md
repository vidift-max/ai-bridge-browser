# Mission 209 — prova AI-01 ↔ AI-02 visível e controlada

## Objetivo
Preparar a interface para que uma execução física dos dois ChatGPTs mostre o progresso do roundtrip sem expor credenciais ou armazenar o texto completo das respostas.

## 10 rodadas
01. Auditar a implementação M208 antes da prova física.
02. Corrigir a extração JSON do orquestrador.
03. Garantir que a resposta nova continue sendo o único gatilho de relay.
04. Exibir o resumo limitado de evidência durante cada turno.
05. Exibir o resultado final de 10 turnos na interface.
06. Manter a indicação explícita de que a prova física ainda está pendente.
07. Preservar o limite exclusivo AI-01/AI-02.
08. Não persistir conteúdo integral das respostas como evidência da missão.
09. Adicionar verificação Android/JVM dedicada.
10. Manter PR aberto e sem merge/release/deploy.

## Gate físico
Somente um teste em Android com duas contas ChatGPT autenticadas poderá converter esta preparação em prova de comunicação real.

Critérios:
- dois WebViews com perfis isolados verificados;
- AI-01 e AI-02, somente;
- usuário inicia manualmente;
- 10 turnos alternados;
- interface termina mostrando turnos=10 e alternância=OK;
- nenhuma alegação de prova física sem execução observada.

## Reconciliação M209
Esta branch foi reconstruída diretamente do HEAD M208 (19feace90bf20efa05f6edd88fbe545a1bbbccf4), preservando o código e os testes M208 e reaplicando apenas as alterações específicas de M209. O workflow de push aponta para esta branch de reconciliação. A PR antiga #212 permanece aberta para auditoria e não é substituída silenciosamente.
