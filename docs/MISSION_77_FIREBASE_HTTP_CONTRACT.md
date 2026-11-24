# Missão 77 — Testes de contrato HTTP Firebase RTDB

## Dez rodadas
1. Baseline: PR #75 confirmado aberto, Draft, sem merge; CI Android concluído com sucesso.
2. Auditoria: runner M74 já tinha testes com mocks, mas não exercitava o protocolo HTTP real.
3. Servidor falso: criado RTDB local em memória, sem projeto Firebase externo.
4. Preflight: teste valida as três leituras GET e o uso do token de cada identidade.
5. Escrita: teste verifica POST de mensagem com remetente e destinatário esperados.
6. Recebimento: teste verifica leitura da mensagem usando a sessão do destinatário.
7. ACK: teste verifica PUT pelo destinatário e GET de confirmação pelo remetente.
8. Segredos: teste garante que tokens não aparecem no resultado serializado.
9. Regressão: cinco testes de contrato HTTP adicionados ao conjunto Python.
10. CI/documentação: workflow de contrato e este relatório adicionados.

## Limites
O servidor é local e simulado; não representa um projeto Firebase, regras publicadas, aparelhos ou rede externa. Nenhum token real foi usado. Nenhuma mensagem externa foi enviada. Round-trip físico/real AI-01↔AI-02 permanece BLOCKED até provisionamento autorizado e execução do operador.
