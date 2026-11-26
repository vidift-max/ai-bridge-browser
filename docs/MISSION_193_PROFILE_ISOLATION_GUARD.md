# Missão 193 — Guardas de identidade para perfis ChatGPT AI-01 / AI-02

## Objetivo e limites
Reduzir o risco de duas abas receberem acidentalmente o mesmo identificador lógico de perfil e tornar explícita a condição mínima para classificar uma atribuição como perfil separado. Escopo local-first: sem APIs pagas, provedores externos, hospedagem, login automatizado, injeção DOM, envio de mensagens ou ativação de dispositivos. Isto não prova isolamento físico de cookies/armazenamento nem conversa real entre modelos.

## Rodadas 01–10
| Rodada | Trabalho verificável | Resultado |
|---|---|---|
| 01/10 | Conferir PRs anteriores e fixar base na M192 (0195529655b6e9e95f47e0f025bf231ca76bfbf2). | PASS — PR #193 e #194 continuam Draft/open/unmerged no snapshot consultado. |
| 02/10 | Revisar SESSION_ISOLATION.md e AndroidX WebKit 1.18.0. | PASS — MULTI_PROFILE e setProfile são feature-gated; teste real no dispositivo pendente. |
| 03/10 | Inspecionar criação/restauração em MainActivity.java. | PASS — profileId persiste/restaura, mas não havia verificação explícita de colisão entre perfis ativos. |
| 04/10 | Definir política pura de unicidade e elegibilidade. | PASS — SessionProfilePolicy rejeita IDs vazios/repetidos e exige feature, atribuição e unicidade. |
| 05/10 | Integrar verificação de colisão ao addTab. | PASS em código — IDs restaurados duplicados recebem novo ID antes da criação do WebView. |
| 06/10 | Preservar a ordem crítica da API WebView. | PASS por inspeção — setProfile continua antes de settings, clientes e navegação. |
| 07/10 | Adicionar testes para ID único, duplicado, vazio e lista inicial. | PASS em código — testes adicionados; execução ainda não confirmada. |
| 08/10 | Testar o gate de declaração de isolamento. | PASS em código — feature ausente, falha de atribuição ou ID duplicado resulta em false. |
| 09/10 | Revisar limites e aceitação manual. | PASS documental — login manual e teste em dispositivo obrigatórios; nenhuma automação ChatGPT adicionada. |
| 10/10 | Registrar evidências e preparar PR Draft. | PASS de entrega de código; BLOCKED operacionalmente até CI e teste físico. |

## Arquivos alterados
- app/src/main/java/com/vidiftmax/aibridgebrowser/SessionProfilePolicy.java — política pura de unicidade/elegibilidade.
- app/src/main/java/com/vidiftmax/aibridgebrowser/MainActivity.java — verifica colisões entre abas ativas e não marca isolamento sem os três requisitos.
- app/src/test/java/com/vidiftmax/aibridgebrowser/SessionProfilePolicyTest.java — testes positivos e negativos.
- docs/MISSION_193_PROFILE_ISOLATION_GUARD.md — este relatório.

## Critérios pendentes
- [ ] Executar ./gradlew :app:testDebugUnitTest :app:assembleDebug em CI e registrar jobs.
- [ ] Instalar em dispositivo autorizado e confirmar suporte real de MULTI_PROFILE.
- [ ] Autenticar manualmente duas contas de teste distintas e verificar cookies, local storage, alternância e reinício.
- [ ] Fazer logout/limpeza individual e confirmar que a outra conta permanece autenticada.
- [ ] Demonstrar troca real AI-01 → AI-02 → AI-01. A fila atual ainda não envia texto ao ChatGPT.
- [ ] Confirmar que falha do provider ou perfil compartilhado impede usar duas contas distintas.

## Decisão
O código impede colisão de identidade lógica entre perfis ativos e adiciona testes determinísticos para essa política. Isso não demonstra isolamento do provedor Android WebView, autenticação de duas contas ou comunicação entre modelos.

**Resultado: PASS para guarda de unicidade e testes adicionados; BLOCKED para isolamento real e primeiro contato AI-01 ↔ AI-02.** Nenhum teste foi declarado executado, nenhum login foi realizado, nenhuma mensagem foi enviada e nenhum deploy/merge foi feito.
