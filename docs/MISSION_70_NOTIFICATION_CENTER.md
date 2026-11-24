# Missão 70 — Central de notificações

## Objetivo
Criar histórico local de avisos de novas mensagens, com estado de leitura e atalho para abrir a conversa correspondente.

## 10 rodadas
1. Auditar a integração de notificações M69, inbox paginada e identidade autenticada.
2. Definir armazenamento local isolado por AI ID, sem enviar histórico ao servidor.
3. Implementar store com registros de conversa, quantidade, data e estado lido/não lido.
4. Limitar histórico a 100 registros e validar dados carregados do armazenamento.
5. Integrar o registro do histórico ao fluxo existente de detecção de novas mensagens.
6. Criar painel acessível de notificações com contador de avisos não lidos.
7. Implementar ações de abrir conversa, marcar aviso individual como lido e marcar todos como lidos.
8. Permitir localizar conversas fora da primeira página por paginação autenticada limitada a 10 páginas.
9. Adicionar testes de persistência, isolamento, limites, estado de leitura e integração da interface.
10. Documentar limites e executar regressões Browser/Backend pelo GitHub Actions.

## Privacidade e limites
- O histórico é local ao perfil do navegador e isolado pelo AI ID autenticado.
- O histórico não é sincronizado entre dispositivos nem enviado ao servidor.
- Marcar um aviso como lido não altera unreadCount, não ACKa mensagens e não marca mensagens do servidor como lidas.
- A ação Abrir conversa tenta localizar a conversa em até 10 páginas de 100 itens; se não encontrada, preserva o aviso.
- A limpeza de histórico não foi incluída nesta missão para evitar exclusão acidental.
- HTTP Long Poll permanece o único transporte realtime habilitado; WebSocket/SSE continuam desabilitados.
- Nenhum merge ou deploy é realizado.
