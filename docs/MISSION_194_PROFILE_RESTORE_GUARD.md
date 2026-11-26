# Missão 194 — integridade de perfis e restauração de AI-01 / AI-02

## Objetivo
Impedir que o estado persistido associe identidades AI fora do escopo atual e impedir que duas identidades de IA compartilhem o mesmo perfil de WebView. O teto futuro permanece 20; a operação desta missão permanece em duas contas.

## Rodadas 01–10

| Rodada | Trabalho verificável | Resultado |
|---|---|---|
| 01/10 | Revalidar PRs #193, #194 e #196: todas abertas, Draft e não mescladas no momento da auditoria. | PASS |
| 02/10 | Auditar criação de WebView e confirmar setProfile antes de settings, clientes e navegação, condicionado a MULTI_PROFILE. | PASS estático |
| 03/10 | Auditar restauração durável: identificadores persistidos eram aceitos sem allowlist de AI-01/AI-02. | RISCO CONFIRMADO |
| 04/10 | Implementar allowlist explícita de identidade para restauração desta missão. | PASS em código |
| 05/10 | Validar que cada painel restaurado referencia um par tabId/profileId existente entre as abas recuperadas. | PASS em código |
| 06/10 | Reforçar registro para rejeitar reutilização do mesmo profileId por identidades de IA diferentes. | PASS em código |
| 07/10 | Adicionar testes para aceitar AI-01/AI-02 e rejeitar AI-03, AI-20 e nulo na restauração atual. | PASS — testes adicionados, execução pendente |
| 08/10 | Adicionar teste para rejeitar dois painéis ligados ao mesmo perfil de WebView. | PASS — teste adicionado, execução pendente |
| 09/10 | Detectar também IDs duplicados no estado durável: gerar novos tabId/profileId ao restaurar colisões, impedindo duas WebViews de usar o mesmo perfil de cookies/storage. Adicionar política pura e testes unitários. | PASS em código; execução pendente |
| 10/10 | Documentar critérios de aceite, abrir PR Draft e verificar CI do commit final. | PENDENTE DE CI / teste físico |

## Arquivos alterados
- app/src/main/java/com/vidiftmax/aibridgebrowser/AiAccountCapacityPolicy.java
- app/src/main/java/com/vidiftmax/aibridgebrowser/AIControlCenter.java
- app/src/main/java/com/vidiftmax/aibridgebrowser/MainActivity.java
- app/src/main/java/com/vidiftmax/aibridgebrowser/SessionIdentityPolicy.java
- app/src/test/java/com/vidiftmax/aibridgebrowser/AiAccountCapacityPolicyTest.java
- app/src/test/java/com/vidiftmax/aibridgebrowser/AIControlCenterTest.java
- app/src/test/java/com/vidiftmax/aibridgebrowser/SessionIdentityPolicyTest.java

## Evidências de implementação
- AiAccountCapacityPolicy.isCurrentMissionAccountId permite apenas AI-01 e AI-02 na restauração desta missão.
- MainActivity.restoreDurableTabs descarta painéis com identidade fora da allowlist ou com vínculo tabId/profileId que não corresponda a uma aba restaurada.
- MainActivity.addTab detecta colisões de tabId/profileId durante restauração e cria identificadores novos; o painel antigo não é religado silenciosamente.
- SessionIdentityPolicy e seus testes cobrem identidade nova, duplicada, vazia e conjunto nulo.
- AIControlCenter.register rejeita perfil já vinculado a outro painel, além das verificações anteriores de AI ID, tab ID e capacidade.
- O registro continua com capacidade futura de 20; a interface/ativação da missão continua limitada a 2.
- A fila permanece sem injeção DOM/auto-submit. Nenhuma integração com ChatGPT foi habilitada.

## Critérios de aceite
- [x] AI-01 e AI-02 são as únicas identidades restauráveis nesta missão.
- [x] Um painel restaurado precisa apontar para aba e perfil existentes.
- [x] Dois painéis não podem compartilhar o mesmo profileId.
- [x] Duas WebViews restauradas não reutilizam silenciosamente o mesmo profileId persistido.
- [x] Teto arquitetural 20 e limite atual 2 permanecem separados.
- [ ] CI do commit final verde.
- [ ] Teste no Android real: MULTI_PROFILE disponível e cookies/storage isolados.
- [ ] Login manual em duas contas ChatGPT diferentes.
- [ ] Alternância, reinício, logout e limpeza individual confirmados.
- [ ] Primeira troca supervisionada AI-01 → AI-02 → AI-01.

## Conclusão
**PASS em correções de integridade e testes adicionados; BLOCKED operacionalmente.** Os testes ainda precisam ser executados pelo CI. Não há evidência de duas contas autenticadas, isolamento físico de cookies/storage ou comunicação real entre modelos. Nenhum login, envio de mensagem, deploy, publicação de regras ou merge foi realizado.
