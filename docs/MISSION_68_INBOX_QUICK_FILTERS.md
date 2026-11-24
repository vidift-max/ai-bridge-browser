# Missão 68 — Filtros rápidos da caixa de entrada

## Objetivo
Permitir localizar imediatamente conversas não lidas ou fixadas, combinando os filtros rápidos com busca textual e tipo de conversa.

## 10 rodadas
1. Auditar o contrato atual da inbox, contadores unread e preferências locais de fixação.
2. Definir os modos ALL, UNREAD e PINNED sem criar endpoints nem alterar a API.
3. Estender o filtro puro da inbox para aceitar modo e IDs fixados.
4. Garantir que UNREAD exige unreadCount inteiro positivo e PINNED depende da lista local.
5. Adicionar seletor acessível com Todas, Não lidas e Fixadas.
6. Integrar seletor à renderização e usar a mesma store local da Missão 67.
7. Preservar composição com busca textual, tipo PRIVATE/GROUP e ordenação de fixadas.
8. Tratar armazenamento local indisponível e valores de filtro desconhecidos de modo seguro.
9. Adicionar testes para resultados, composição de filtros, estado desconhecido e integração da UI.
10. Adicionar workflow dedicado de regressão Browser/Backend e registrar limites/evidências.

## Limites
- Não lidas usa somente unreadCount retornado pela API autenticada; não calcula nem altera ACK.
- Fixadas continuam locais ao perfil do navegador, sem sincronização entre dispositivos.
- Nenhuma alteração de backend, autenticação, mensagens ou transporte.
- HTTP Long Poll permanece o único transporte realtime habilitado; WebSocket/SSE continuam desabilitados.

## Verificação
Aguardando GitHub Actions para o commit final.
