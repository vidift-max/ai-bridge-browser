# M258 — MIGRAÇÃO SQLITE V1→V2 E COMPATIBILIDADE DE RESTAURAÇÃO

Data: 2026-11-26
Branch: feat/mission-241-updater-backport-v2-saas-alpha
Escopo: AI-01 / AI-02
AI-03: desativada
PR #234: sem merge; Release/deploy não autorizados nem executados

## Resultado em 10 rodadas

### 01/10 — Baseline
Revalidado o estado M257: schema v1, armazenamento SQLite, validação de restore read-only e ausência de tabela de convites.

**PASS** — baseline conhecido antes da migração.

### 02/10 — Migração transacional
Atualizado `server/sqlite_store.py` para schema v2. A migração usa `BEGIN IMMEDIATE`, cria o schema v1 em banco novo e, em seguida, cria a tabela de convites e altera a versão para 2 dentro da mesma transação. Exceções fazem rollback; falha de migração fecha a conexão.

**PASS** — caminho de migração implementado no código.

### 03/10 — Estrutura de convites
A tabela `invitations` contém invitation_id, conversation_id, target_ai_id, token_hash, status, created_by_ai_id, created_at, expires_at, accepted_at e revoked_at. Há PK, UNIQUE para token_hash, checks de estados/timestamps e índices para consulta por conversa/estado e destinatário/estado.

**PASS** — armazenamento persistente mínimo criado.
**BLOCKED** — ainda não existem operações de emissão/aceite/revogação no store.

### 04/10 — Preservação v1→v2
A migração v1→v2 não reescreve conversas, mensagens, idempotência ou acknowledgements. Os testes novos incluem uma base v1 com mensagem/idempotência, migração ao reabrir e verificação de preservação.

**PASS** — teste de regressão adicionado; não é declaração de teste executado.

### 05/10 — Banco novo
Banco sem versão cria as tabelas base e segue para v2 na mesma transação de migração.

**PASS** — caminho de inicialização implementado.
**BLOCKED** — execução local não foi demonstrada nesta sessão.

### 06/10 — Compatibilidade de schema no restore
`server/recovery.py` agora reconhece schema v1 legado e schema v2. Para v2, exige colunas da tabela invitations e índices esperados. O validador continua read-only; não executa migrações em candidatos.

**PASS** — compatibilidade v1/v2 implementada no validador.

### 07/10 — Consistência relacional dos convites
O validador v2 verifica conversa existente, emissor membro, hash hexadecimal SHA-256 em lowercase, estado permitido, timestamps coerentes e associação do destinatário como membro quando status ACCEPTED.

**PASS** — validação de dados v2 adicionada.

### 08/10 — Testes de migração e restore
Criado `server/test_messenger_invitation_schema.py` cobrindo banco novo v2, migração v1 preservando mensagem/idempotência, rejeição de schema futuro sem downgrade, candidato v2 com convite pendente válido, rejeição de emissor inexistente e compatibilidade de restore v1.

**PASS** — seis cenários automatizados adicionados.
**BLOCKED** — não foi possível confirmar execução local nem CI nesta verificação.

### 09/10 — Limites e segurança
A tabela persiste somente token_hash; não há endpoint, token em claro, emissão ou aceite implementados. A restrição de sala GROUP/PRIVATE ainda precisa ser aplicada na operação transacional de aceite. A migração não cria credenciais nem provisiona AI_ID.

**PASS** — escopo de migração separado de autorização/runtime.
**NO-GO** — não usar esta tabela como fluxo de convite pronto.

### 10/10 — Veredito
**PASS:** schema v2 e migração transacional v1→v2 implementados.
**PASS:** validadores read-only reconhecem v1 e v2 e verificam a tabela/relacionamentos de convite em v2.
**PASS:** testes de migração/restore adicionados.
**BLOCKED:** testes ainda sem execução confirmada; CI sem run associado ao HEAD final consultado.
**NO-GO:** API, emissão, aceite, revogação, ativação de membership e integração Android continuam pendentes.
**NO-GO:** não declarar convite funcional ou comunicação real AI-01↔AI-02.

## Arquivos alterados

- `server/sqlite_store.py` — schema v2 e migração transacional.
- `server/recovery.py` — validação de schema/data v1 e v2.
- `server/test_messenger_invitation_schema.py` — regressões de migração e restore.

## Próxima missão M259

Implementar métodos de store com transações atômicas para criar, aceitar e revogar convites; token aleatório de 256 bits gerado na camada de serviço e somente hash persistido; consumo single-use vinculado ao AI_ID autenticado; limites GROUP 20 / PRIVATE 2; idempotência/replay/concorrência; testes de corrida e restart. Em seguida integrar os handlers HTTP sem registrar tokens. Não portar Activity Android até a API estar testada.

## Estado operacional

- Nenhum deploy, Release, instalação, merge ou workflow_dispatch.
- Nenhum Secret/Variable alterado.
- Nenhum banco de usuário/produção foi acessado; testes são fixtures de repositório.
- WebRTC, Termux e AI-03 fora do escopo.
