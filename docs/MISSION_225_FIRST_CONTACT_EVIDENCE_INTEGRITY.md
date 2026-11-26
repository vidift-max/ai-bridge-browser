# M225 — Integridade das evidências do primeiro contato AI-01 ↔ AI-02

## Objetivo
Garantir que uma execução só seja declarada concluída quando os turnos estiverem registrados em sequência, alternando AI-01 e AI-02, com evidência de integridade sem armazenar o conteúdo integral das respostas.

## Dez rodadas de engenharia
1. Auditar o registro de evidências existente e identificar ausência de validação de sequência.
2. Definir a sequência canônica: turnos ímpares AI-01, turnos pares AI-02.
3. Rejeitar lacunas, duplicatas, ordem incorreta, remetentes desconhecidos e respostas vazias.
4. Calcular SHA-256 de cada resposta para permitir verificação de integridade sem guardar seu texto.
5. Registrar tamanho da resposta e horário de captura em epoch milliseconds.
6. Expor lista imutável de eventos para consumidores internos.
7. Exigir que o orquestrador valide contagem completa e alternância antes de emitir sucesso.
8. Adicionar testes JVM para hash conhecido, ordem, remetente, duplicatas, conteúdo vazio e imutabilidade.
9. Adicionar testes estáticos para privacidade e validação final do orquestrador.
10. Executar CI push e PR no mesmo SHA; manter PR Draft e sem merge, release, instalação ou contato real.

## Dados por turno
- Número sequencial.
- Identidade remetente AI-01 ou AI-02.
- Quantidade de caracteres.
- SHA-256 da resposta.
- Timestamp de captura em epoch milliseconds.

O conteúdo integral da resposta não é mantido em AiBridgeEvidence. O resumo não é prova criptográfica assinada nem prova da identidade da conta; é um registro local de integridade e sequência.

## Critério de sucesso
O orquestrador só chama onFinished quando o número de eventos é igual ao número de turnos solicitado e toda a sequência está válida. Qualquer divergência termina em erro explícito, nunca em PASS.

## Limites
- Evidência permanece em memória durante a execução; não é persistida nem exportada.
- SHA-256 comprova igualdade do conteúdo apresentado ao registrador, não a origem/autenticidade da resposta.
- CI não comprova conversa real no dispositivo.
- AI-03 permanece fora do escopo.
- Nenhum merge, publicação, instalação ou conversa real foi executado nesta missão.
