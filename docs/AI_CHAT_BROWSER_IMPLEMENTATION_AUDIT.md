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
| Presença/diretório | Sem heartbeat confiável | Pendente |
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
- HEAD observado: `dc60e936a837f9c12c28239124fd4a773cfa9266`.
- Para esse SHA, a consulta de status combinado retornou lista vazia de checks e a consulta de workflows associados retornou lista vazia.
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
