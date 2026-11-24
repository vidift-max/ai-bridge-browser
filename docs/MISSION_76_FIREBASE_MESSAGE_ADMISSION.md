# Missão 76 — Admissão de destinatários Firebase

## Dez rodadas
1. Baseline: PR #74 e HEAD M75 a70ed2304388af521758394a4c41b6c7e9e73f42 conferidos; PR Draft e sem merge.
2. Auditoria: sendMessage montava destinatários sem consultar membership remoto atual.
3. Remetente: AI_ID precisa constar em members da conversa consultada.
4. Destinatário: cada destinatário solicitado precisa constar em members.
5. Anti-loop: autoenvio é rejeitado.
6. Anti-duplicação: IDs repetidos são rejeitados.
7. Limite: até 20 participantes e 19 destinatários além do remetente.
8. Integração: sendMessage consulta a conversa antes do POST e interrompe se faltar membership.
9. Testes: sete testes cobrem sucesso e seis condições de rejeição.
10. CI/documentação: workflow Android dedicado e este relatório adicionados.

## Garantias e limites
A consulta de membership é prévia, não transacional. Firebase Security Rules continuam sendo a autoridade final; se a membership mudar entre GET e POST, as regras remotas devem negar o POST. Nenhum token é exibido ou registrado. Não envia mensagem real, não altera regras, não cria projeto, não faz deploy e não faz merge. O round-trip real AI-01↔AI-02 com ACK permanece pendente.
