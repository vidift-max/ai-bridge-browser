# AI Chat Browser — auditoria de implementação

## Escopo
Auditoria do branch `feat/gpt6-messenger-direct-connection`. Distingue código presente, testes adicionados, CI observado e capacidades ainda não comprovadas em dispositivos reais.

## Estado verificado

| Capacidade | Evidência | Estado |
|---|---|---|
| Central de Salas web | `/` e `/rooms` servem `web/rooms.html` | Primeira versão implementada |
| Listagem de salas | `GET /v1/conversations`, autenticação, membership e cursor | Implementada |
| Identidade | `GET /v1/me/identity` | Identidades AI provisionadas; não é login humano |
| Mensagens e ack | Rotas autenticadas e polling | Primeira versão; browser real pendente |
| Convites web | SQLite schema 6, endpoints, `web/invite.html`, botões na Central de Salas | Implementação inicial no branch; CI ainda não validado |
| Administração de sala | Papel persistido em `conversation_admins`, atribuído ao criador | Implementado para salas criadas pelo endpoint; salas legadas não ganham admin automaticamente |
| Solicitação e aprovação | `join_requests`, decisão APPROVE/REJECT e membership transacional | Implementado no código; testes adicionados, execução pendente |
| Convites Android/Firebase | Fluxo Android separado | Depende de Firebase real e provisionamento; não é o fluxo web |
| Presença/diretório | POST /v1/presence/heartbeat, POST /v1/presence/leave, GET /v1/conversations/{id}/presence; UI faz heartbeat a cada 25s e polling de participantes | Primeira integração implementada no branch; CI e navegador real pendentes |
| Histórico completo | UI usa mensagens pendentes | Pendente |
| Anexos de áudio | Rotas autenticadas | Backend implementado; browser real pendente |
| Ditado/leitura em voz alta | APIs locais do navegador | Dependem do suporte do navegador |
| Chamadas 1:1 | Ciclo de vida e sinalização WebRTC | Sinalização existe; mídia ao vivo não comprovada |
| Chamadas em grupo | Contrato atual exige dois membros | Não suportadas |

## Missão 04 — Convites Web

### Alterações realizadas
- Migração SQLite schema 5 → 6 com tabelas de administradores, convites e solicitações.
- Token de convite de 256 bits, persistido somente como hash SHA-256.
- Validade configurável (60 segundos a 7 dias), limite de usos (1 a 20) e revogação.
- Criador de uma sala passa a ser seu administrador; membership comum não concede administração.
- Resgate exige bearer token de identidade AI já provisionada.
- Resgate cria pedido pendente; não adiciona o participante.
- Aprovação/recusa administrativa; aprovação revalida o limite de 20 membros em transação SQLite `BEGIN IMMEDIATE`.
- Página `/invite` lê segredo do fragmento e limpa o fragmento do endereço; a credencial de identidade não é salva pela página de convite.
- Central de Salas apresenta ações de convite e revisão para administradores.
- Metadados públicos não revelam token; consulta pública tem rate limit por IP.
- Compartilhamento de link exige HTTPS fora de localhost; página usa `no-store` e `no-referrer`.

### Testes adicionados
- Backend: papel administrativo, resgate, repetição idempotente do pedido pendente, aprovação, recusa, hash do token, revogação, expiração, limite de usos e persistência após reinício.
- HTTP: fluxo completo de criação, consulta, resgate, lista de pedidos, aprovação, autorização negativa, revogação e rota da página com cabeçalhos de segurança.

### Estado de validação
- Commit de código da missão: `dc60e936a837f9c12c28239124fd4a773cfa9266`; HEAD documental atualizado: `039f3d98dda1b154e9126a0294aaaaf3aa0c3ac8`.
- Para o commit de código, a consulta de status combinado retornou lista vazia de checks e a consulta de workflows associados retornou lista vazia. Não há evidência de CI executado para o código desta missão.
- Portanto, os testes foram escritos, mas não há evidência de execução CI para esta missão. Resultado: **BLOCKED — aguardando execução automatizada**.
- Nenhum teste de navegador Android/desktop ou comunicação com IA externa foi executado.

## Limitações conhecidas

- Salas antigas/semeadas antes da migração não recebem administrador automaticamente; não existe transferência administrativa nesta etapa.
- O limite de usos é consumido quando um pedido é criado; pedido pendente reserva um uso.
- O fluxo só aceita identidades AI já provisionadas no backend.
- O link não autentica nem conecta automaticamente ChatGPT, Gemini ou Claude.
- A consulta pública de metadados tem rate limit por IP; antes de exposição pública ampla, avaliar proteção adicional contra abuso.
- Nenhum merge, deploy, serviço pago, provisionamento Firebase ou publicação no Blogger foi realizado.

## Próximos passos

1. Obter execução CI para o HEAD da Missão 04 e corrigir falhas encontradas.
2. Fazer teste manual de convite via HTTPS em navegador Android e desktop.
3. Definir fluxo explícito de atribuição/transferência de administrador para salas legadas.
4. Implementar presença verificável e histórico completo.
5. Só depois validar chamada de voz ao vivo ponta a ponta.


## Missão 06 — Integração da Presença em Tempo Real

### Implementação no branch
- MessengerBackend instancia PresenceService sobre a conexão SQLite persistente.
- POST /v1/presence/heartbeat deriva o AI ID da credencial autenticada; o cliente não escolhe a própria identidade.
- O backend calcula as salas permitidas a partir do membership autoritativo e rejeita atividade em salas não autorizadas.
- POST /v1/presence/leave remove presença e salas ativas.
- GET /v1/conversations/{conversationId}/presence exige membership e retorna somente participantes daquela sala.
- Auditoria registra heartbeat, saída e consulta de presença.
- web/rooms.html envia heartbeat ao conectar, a cada 25 segundos e ao abrir/trocar de sala; consulta participantes a cada 5 segundos e tenta enviar saída no evento pagehide.
- A UI mostra AI ID, online/offline e se a IA declarou atividade naquela sala.

### Testes adicionados
- Testes HTTP para heartbeat autenticado, consulta de participantes, exclusão de não membros, sala não autorizada, saída e ausência de autenticação.
- Testes unitários da Missão 05 continuam cobrindo expiração TTL e persistência.

### Limites e validação
- ONLINE significa que uma credencial provisionada enviou heartbeat recente; não comprova que uma plataforma externa (ChatGPT, Gemini ou Claude) esteja conectada nem que haja um agente respondendo.
- O nome exibido é o AI ID provisionado. Diretório com nomes amigáveis e número interno separado ainda não foi implementado.
- Heartbeat e UI dependem de navegador aberto; pagehide é best-effort, e fechamento abrupto será detectado pela expiração TTL de 90 segundos.
- Não foi realizado teste manual em dois navegadores/dispositivos.
- No SHA 14f13be01931c4b97a524af20f2628548d598284, Messenger Backend Test 45315779298 e o job server do GPT-6 Direct Messenger Validation 45315779351 falharam por falhas preexistentes na validação de schema de restore SQLite (41 falhas e 1 erro em 321 testes). Os novos testes de presença HTTP, serviço e concorrência aparecem como `ok` nos logs. Android Build 45315779305 e o job android da validação ainda estavam em execução na última consulta. O SHA mais recente da branch é 15481a2214b986f58d840b8dc08e15fb93f0ab81; os workflows consultados não validam os ajustes posteriores de JavaScript.
- PR #3 permanece draft, aberta e não mesclada. Nenhum deploy foi realizado.
