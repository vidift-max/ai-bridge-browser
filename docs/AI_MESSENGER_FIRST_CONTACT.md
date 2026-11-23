# Missão — Primeiro contato AI Messenger sem Render

## 10 rodadas

1. Removida a configuração Render da branch; nenhuma implantação Render foi mantida.
2. Definido Firebase Realtime Database Spark como transporte gratuito de texto/rendezvous.
3. Criadas Security Rules vinculando UID autenticado ao AI_ID provisionado.
4. Implementado cliente Android Firebase REST com autenticação anônima.
5. Integrado o cliente ao Messenger HTTP sem quebrar o modo HTTPS existente.
6. Integrados os dois pontos do app que criam o cliente remoto.
7. Corrigido o índice UID→AI_ID das regras.
8. Adicionados testes de validação e mensagens de configuração.
9. Adicionado fluxo de exibição do UID para provisionamento controlado.
10. Fechada a documentação, mantendo a fronteira de prova: CI não é primeiro contato físico.

## Estado

- Código: IMPLEMENTADO nesta branch.
- Render: FORA DA SOLUÇÃO.
- Custo do transporte escolhido: Spark no-cost, dentro das quotas oficiais.
- Projeto Firebase real: ainda precisa ser criado pelo proprietário da conta.
- Identidades Phone-01/Phone-02: ainda precisam ser provisionadas no projeto Firebase.
- Primeiro contato físico entre dois AI-PHONES: **PENDENTE**.
- Voz/WebRTC: permanece depois da prova de texto.

## Critério de verdade

Somente declarar PRIMEIRO CONTATO quando Phone-01 enviar uma mensagem pela Internet e Phone-02 receber/respondê-la, com evidência nos dois aparelhos. Build/CI não substitui esse teste.
