# M257 — AUDITORIA DE MIGRAÇÃO SQLITE E SEGURANÇA DO FLUXO DE CONVITES

Data: 2026-11-26
Branch: feat/mission-241-updater-backport-v2-saas-alpha
PR #234: permanece aberta/Draft; nenhum merge
Escopo: AI-01 / AI-02
AI-03: desativada

## Objetivo

Avançar a implementação do convite/aceitação sem quebrar o armazenamento Messenger, a compatibilidade de backups nem os validadores de restore. Esta missão faz a auditoria de implementação e determina o gate seguro para a migração.

## 10 rodadas verificáveis

### 01/10 — Releitura do estado M256
O contrato M256 especifica convite direcionado a AI_ID já provisionado, token de alta entropia, hash persistido, expiração, uso único, aceite autenticado e ativação de membership após aceite.

**PASS** — requisitos de produto e segurança recuperados do relatório versionado.

### 02/10 — Estado real do schema
Inspecionado `server/sqlite_store.py`: `SCHEMA_VERSION = 1`; tabelas atuais: schema_meta, conversations, messages, idempotency e acknowledgements. Não existe tabela de convites.

**PASS** — ausência confirmada no código da branch.

### 03/10 — Migração e abertura do banco
O `SQLiteMessengerStore._migrate()` cria schema v1 quando não há versão e rejeita versões maiores que a versão suportada. A inicialização do backend usa este store e persiste conversas.

**PASS** — ponto de migração identificado.
**BLOCKED** — nenhuma alteração de schema feita nesta missão.

### 04/10 — Validador de schema de restore
Inspecionado `server/recovery.py`: `_verify_messenger_schema_connection` exige versão exatamente "1", conjunto de tabelas/colunas v1 e índice UNIQUE conversation/sequence. Apenas adicionar tabela/alterar versão sem atualizar o contrato de validação causaria incompatibilidade.

**PASS** — gate de compatibilidade identificado.

### 05/10 — Validação relacional de restore
O validador de dados percorre conversas, mensagens, idempotência e acknowledgements. Não verifica convites, hashes, estados terminais, destinatários nem vínculo de convite com conversa.

**PASS** — cobertura faltante identificada.
**BLOCKED** — restore validator não deve aprovar schema futuro sem validar as relações de convite.

### 06/10 — Atomicidade do aceite
O backend atual mantém membership em memória e usa `save_conversation`, que faz INSERT OR REPLACE e commit próprio. Não há operação única que consuma convite, confira limite de membros e altere membership de forma atômica.

**NO-GO** — não implementar aceite usando chamadas separadas nem atualizar apenas o cache em memória.

### 07/10 — Concorrência e uso único
Não há constraint/tabela de convite nem transação de consumo de token. Duas requisições concorrentes poderiam aceitar o mesmo convite ou ultrapassar o limite se a implementação fosse ingênua.

**PASS** — risco identificado.
**NO-GO** — não alegar uso único antes de constraint e transação no banco.

### 08/10 — HTTP e auditoria
Inspecionado `server/http_server.py`: rotas atuais cobrem criação de conversa, mensagens, ACK e telefone. Não existem handlers de emissão, aceite ou revogação. O handler já dispõe de principal autenticado, rate limiter e trilha de auditoria, que devem ser reutilizados sem registrar token.

**PASS** — pontos de integração identificados; nenhuma rota fictícia foi adicionada.

### 09/10 — Compatibilidade e testes existentes
Inspecionados `server/test_messenger_schema_version.py`, `server/test_restore_candidate.py` e `server/test_restore_candidate_data_consistency.py`. Há testes explícitos para schema futuro, índice e consistência do candidato de restore. Não existe teste de migração v1→v2 ou dados de convite.

**PASS** — matriz de regressão existente identificada.
**BLOCKED** — sem execução de testes locais/CI nesta missão.

### 10/10 — Veredito e plano seguro
**PASS:** mapa completo dos pontos de mudança: store, backend, HTTP, schema validator, data validator e testes de backup/restore.
**PASS:** nenhuma alteração arriscada foi feita no banco nem no runtime.
**NO-GO:** não adicionar tabela de convites isoladamente, não mudar `SCHEMA_VERSION` sem migrar os validadores, não aceitar convite via cache em memória.
**BLOCKED:** implementação funcional permanece pendente; o backend ainda não oferece emissão/aceite/revogação.

## Plano obrigatório da M258

1. Definir schema v2 com tabela de invitations: invitation_id, conversation_id, target_ai_id, token_hash, status, created_by_ai_id, created_at, expires_at, accepted_at, revoked_at.
2. Índices/constraints para token_hash único, invitation_id único e estados/relacionamentos válidos.
3. Migração transacional v1→v2, idempotente e sem alterar conteúdo de conversas/mensagens existentes.
4. Política de restore explícita: validar schema v1 legado e schema v2; para v2, validar todas as relações e constraints de convites. Nunca migrar candidato durante validação read-only.
5. Implementar no store operação transacional de emissão/aceite/revogação. Aceite deve consumir convite e inserir membro em uma transação, com revalidação do limite GROUP 20 e rejeição de PRIVATE.
6. Usar comparação constante de hash quando aplicável; token aleatório de 256 bits, persistindo apenas SHA-256; nunca registrar token.
7. Recarregar/atualizar membership em memória somente após commit bem-sucedido.
8. Endpoints HTTP com principal autenticado, rate limit, respostas genéricas e auditoria redigida.
9. Testes para migração v1→v2, restart, replay, token errado, AI_ID errado, expiração, revogação, concorrência, sala cheia, PRIVATE, restore v1/v2 e candidato não mutado.
10. Exigir Backend Test e Android Build no mesmo HEAD antes de declarar PASS. Sem deploy ou instalação sem autorização.

## Estado operacional

- Nenhum código de runtime, migração, rota ou teste foi alterado nesta missão.
- Nenhum banco ativo ou backup foi aberto para escrita.
- Nenhum merge, Release, deploy, instalação, Secret/Variable ou workflow_dispatch.
- AI-03 desativada; WebRTC e Termux fora do escopo.
- Esta missão não prova comunicação real AI-01↔AI-02.
