# M259 — CICLO TRANSACIONAL DE CONVITES

Data: 2026-11-26
Branch: feat/mission-241-updater-backport-v2-saas-alpha
Escopo: AI-01 / AI-02
AI-03: desativada
WebRTC e Termux: fora do escopo

## Execução — 10 rodadas

### 01/10 — Revisão do estado M258
Inspecionados o SQLite store, backend Messenger, HTTP handler, autenticação e testes existentes. Foi identificado que o tipo PRIVATE/GROUP não era persistido no schema v2.

**PASS** — lacuna confirmada e tratada antes do ciclo de convites.

### 02/10 — Schema v3
Adicionada migração transacional v2→v3 com coluna `conversations.conversation_kind`, default GROUP para conversas históricas, preservando membership. Schema v1→v2→v3 segue em uma única transação ao abrir bancos antigos.

**PASS** — tipo da conversa persistido.

### 03/10 — Emissão de convite
Adicionado método transacional `create_invitation`: exige conversa existente, emissor membro, sala não privada e destinatário fora da membership. Backend exige AI_ID provisionado.

**PASS** — convite pendente criado em transação SQLite.

### 04/10 — Token de uso único
Backend gera 32 bytes aleatórios com `secrets.token_urlsafe(32)`; persiste somente SHA-256 hexadecimal. O token em claro retorna uma única vez na resposta da criação. Auditoria não recebe token.

**PASS** — armazenamento não persiste token em claro.
**Limite** — token continua sendo segredo bearer; cliente deve protegê-lo e transportá-lo somente por HTTPS.

### 05/10 — Aceite autenticado e atômico
Aceite autentica o bearer, calcula hash e abre `BEGIN IMMEDIATE`. Dentro da mesma transação verifica hash, target AI_ID, status PENDING, expiração, tipo/limite da conversa; marca ACCEPTED e adiciona o membro. Cache de membership atualiza somente após commit.

**PASS** — consumo e membership são atômicos no SQLite.

### 06/10 — Replay, expiração e revogação
Aceite repetido, token errado ou target diferente é rejeitado. Convite expirado é marcado EXPIRED. Revogação só é permitida ao AI_ID que criou o convite e só enquanto PENDING.

**PASS** — single-use, expiração e revogação implementados.

### 07/10 — Limites PRIVATE/GROUP
PRIVATE não aceita convite nem expansão. GROUP aceita até 20 membros; o limite é revalidado dentro da transação de aceite. AI_ID alvo precisa estar provisionado.

**PASS** — limites aplicados no backend e no banco.
**Nota** — salas históricas v1/v2 são migradas como GROUP, pois o tipo não existia no schema antigo.

### 08/10 — HTTP autenticado
Adicionadas rotas:
- POST `/v1/conversations/{conversationId}/invitations`
- POST `/v1/invitations/accept`
- POST `/v1/invitations/{invitationId}/revoke`

Rotas verificam principal autenticado, rate limit, JSON e respostas sem cache. Auditoria registra IDs/estado, nunca o token.

**PASS** — handlers adicionados.
**BLOCKED** — não há teste HTTP de integração executado nem confirmação de serviço implantado.

### 09/10 — Testes de regressão
Adicionados testes para hash sem token em claro, aceite pelo destinatário correto, target incorreto, PRIVATE, revogação, target não provisionado, concorrência single-use, persistência após restart, expiração, permissão de revogação, limite de 20, e rotas HTTP. Atualizados testes de schema para v3.

**PASS** — cobertura automatizada adicionada.
**BLOCKED** — execução local/CI não foi confirmada nesta missão.

### 10/10 — Veredito
**PASS (implementação):** migração v3, criação/aceite/revogação, token 256-bit, hash SHA-256, transações SQLite, autenticação, limites e rotas HTTP adicionados.
**PASS (evidência de repositório):** arquivos e commits conferidos no branch.
**BLOCKED:** testes e CI sem resultado confirmado; nenhum runtime/deploy foi testado.
**NO-GO:** não declarar serviço de convites em produção, comunicação AI-01↔AI-02 funcional ou instalação Android validada.

## Arquivos alterados

- `server/sqlite_store.py` — migração v3 e operações transacionais.
- `server/messenger_backend.py` — emissão, aceite e revogação autenticados.
- `server/http_server.py` — três endpoints e auditoria sem token.
- `server/recovery.py` — validação restore v1/v2/v3 e tipo/limites v3.
- `server/test_messenger_backend.py` — ciclo, replay, concorrência, restart, expiração e limites.
- `server/test_messenger_invitation_schema.py` — expectativa de schema v3.
- `server/test_http_server.py` — contrato de rotas.

## Próxima missão M260

Executar testes e corrigir falhas, adicionar testes HTTP reais com servidor local/cliente, testar concorrência multi-processo e restore v1/v2/v3, validar configuração HTTPS e políticas de rate limit, e revisar auditoria/retention. Não iniciar instalação Android nem ativar comunicação de produção antes de CI verde e revisão de segurança.

## Estado operacional

Nenhum merge, deploy, Release, instalação, workflow_dispatch ou alteração de Secrets/Variables foi realizado. Nenhum banco de produção foi acessado.
