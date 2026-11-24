# Missão 69 — Notificações de novas mensagens

## Objetivo
Notificar o usuário quando os contadores autenticados de mensagens não lidas aumentarem, mesmo quando outra conversa estiver aberta ou quando a caixa de entrada estiver em foco.

## 10 rodadas
1. Auditar o polling atual, que atualiza mensagens somente na conversa ativa.
2. Definir notificação por aumento de unreadCount da inbox autenticada, sem duplicar eventos.
3. Implementar tracker de contagens com baseline inicial sem falsos positivos.
4. Suprimir alertas da conversa atualmente aberta e atualizar baseline quando a contagem cair.
5. Adicionar aviso visual acessível com aria-live e texto agregado.
6. Integrar Notification API somente quando permission === granted; nunca solicitar permissão automaticamente.
7. Atualizar a inbox periodicamente mesmo sem conversa ativa, mantendo polling da conversa ativa separado.
8. Garantir recuperação após erro de rede e impedir que novas conversas gerem falsos alertas no baseline.
9. Cobrir aumentos, reduções, conversa ativa, agregação, reset e integração da UI.
10. Adicionar workflow Browser/Backend e registrar limites e evidências.

## Limites
- A notificação usa apenas unreadCount devolvido pela API autenticada; não altera ACK nem confirma leitura.
- A API Notification do navegador é usada apenas se o usuário já concedeu permissão. Nenhum prompt de permissão é exibido.
- A verificação da inbox ocorre por polling HTTP periódico, não é push em tempo real.
- HTTP Long Poll permanece o transporte realtime do Messenger; WebSocket/SSE continuam desabilitados.

## Verificação — PASS
- Workflow run `45466673280`: completed / SUCCESS.
- Browser Regression: 258/258 testes aprovados.
- Backend Regression: 472 testes aprovados.
- Commit validado: `4e12daf5ec94df2d737bcc2ac69f4315ca601c41`.
