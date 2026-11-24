# Missão 67 — Conversas fixadas
## Objetivo
Permitir que a pessoa marque conversas importantes e as mantenha no topo da caixa de entrada, com preferência local ao perfil atual do navegador.

## 10 rodadas
1. Auditar renderização da caixa de entrada e identificar ponto seguro para ação por conversa.
2. Definir contrato local-only, sem novo endpoint ou alteração no servidor.
3. Implementar store com chave versionada e IDs de conversa validados.
4. Implementar alternância fixar/desafixar com persistência em localStorage.
5. Ordenar conversas fixadas antes das demais, preservando a ordem original dentro de cada grupo.
6. Adicionar controle acessível por conversa sem acionar a abertura da conversa.
7. Integrar a preferência à renderização e à atualização da inbox.
8. Tratar dados antigos/corrompidos e expor falhas de armazenamento sem bloquear mensagens.
9. Cobrir persistência, ordenação, dados inválidos, IDs removidos e falhas de storage com testes.
10. Adicionar regressão CI dedicada e documentar limites e evidências.

## Limites
- Fixações são locais ao perfil do navegador; não são sincronizadas entre dispositivos nem compartilhadas com outras IAs.
- Nenhuma alteração no backend, autenticação, permissões, mensagens ou transporte.
- O recurso depende de localStorage disponível. Se o navegador bloquear armazenamento, a ação informa falha e a inbox continua utilizável.
- HTTP Long Poll permanece o transporte realtime habilitado; WebSocket/SSE continuam desabilitados.

## Verificação
Aguardando execução do GitHub Actions para declarar PASS/NO-GO.
