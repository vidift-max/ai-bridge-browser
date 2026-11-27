# M261 — PROCESS-SHARED RATE LIMIT, SQLITE V4 E TRANSPORT GUARD

Data: 2026-11-26/27
Branch: `feat/mission-241-updater-backport-v2-saas-alpha`
Código validado: `c5f82ea17562aa8a1c4781c1584f907a0fbda403`
Escopo: AI-01 e AI-02
AI-03: desativada
WebRTC e Termux: fora do escopo

## Rodadas — 10/10

### 01/10 — Reabertura das pendências
Revisado o relatório M260 e o código corrente.
Foram confirmadas duas lacunas técnicas:
- o rate limiter em memória não compartilhava estado entre processos;
- o servidor aceitava bind em endereço público sem uma barreira explícita que exigisse TLS terminado em proxy confiável.

Também foi mantida a distinção entre teste local/CI e implantação pública.

**PASS** — lacunas localizadas no código.

### 02/10 — Migração SQLite schema v4
Evoluído schema v3 para v4 com tabela `rate_limit_events` e índice `idx_rate_limit_principal_time`.
A migração é transacional e os bancos históricos v1, v2 e v3 percorrem as migrações sequenciais até v4.
Testes cobrem v1→v4, v2→v4 e v3→v4, preservação de convites e classificação PRIVATE/GROUP.

**PASS** — migração v4 implementada e coberta.

### 03/10 — Rate limiter transacional compartilhado
Adicionado `SQLiteMessengerStore.consume_rate_limit`.
Cada operação em arquivo SQLite abre uma conexão independente, usa `BEGIN IMMEDIATE`, remove eventos expirados, conta eventos do principal e registra o evento dentro da mesma transação.
O lock de escrita SQLite serializa os processos concorrentes que usam o mesmo arquivo.

**PASS** — atomicidade implementada para processos que compartilham o mesmo arquivo SQLite.

### 04/10 — Integração HTTP
O servidor passou a configurar `SQLiteSlidingWindowRateLimiter` ligado ao banco persistente do Messenger.
Os endpoints HTTP passam a compartilhar o orçamento de requisições por AI_ID, em vez de manter contadores isolados na memória de cada processo.

**PASS** — integração implementada; teste HTTP confirma limite compartilhado entre endpoints.

### 05/10 — Concorrência entre processos do sistema operacional
Criado `server/test_rate_limit.py` com oito processos independentes, cada um abrindo sua própria conexão SQLite.
Com limite 3, oito tentativas simultâneas resultam em exatamente 3 aceitações e 5 rejeições.

**PASS** — teste multiprocessos aprovado no CI.

Limite: prova compartilhamento de processos que acessam o mesmo arquivo SQLite no mesmo ambiente de armazenamento. Não prova coordenação entre hosts com discos independentes, nem recomenda SQLite em filesystem de rede multi-host.

### 06/10 — Isolamento por identidade e janela
Adicionados testes de isolamento entre AI_IDs e expiração da janela deslizante.
Também foi acrescentado teste HTTP para garantir que rotas distintas consumam o mesmo limite do principal autenticado.

**PASS** — testes automatizados aprovados.

### 07/10 — Recovery e restore schema v4
A validação read-only agora aceita schema v4 somente quando a tabela e o índice do rate limit estão presentes.
A verificação de dados continua cobrindo conversas PRIVATE/GROUP e convites para schema v4.
Bancos v1/v2/v3 continuam reconhecidos sob seus contratos históricos, sem migração durante validação read-only.

**PASS** — compatibilidade de recovery v4 adicionada; cobertura existente de restore executada no CI.

### 08/10 — Barreira de transporte público
Adicionado `RuntimeConfig.validate_transport_contract`.
O bind local em loopback continua permitido por HTTP. Bind em endereço não-loopback falha fechado, a menos que:
- `MESSENGER_TLS_TERMINATED=true`;
- `MESSENGER_PUBLIC_BASE_URL` seja uma URL HTTPS válida, sem userinfo ou fragmento.

`serve()` valida o contrato antes de abrir o socket.

**PASS** — guard implementado e testes de configuração aprovados.
**LIMITAÇÃO** — a declaração de TLS no proxy é configuração/atestado do operador; não é prova criptográfica de certificado, handshake, domínio ou headers de um serviço implantado.

### 09/10 — Correções pós-CI
Os primeiros testes apontaram que os fixtures históricos v1/v2 ainda continham a tabela v4 e que o teste HTTP comparava identidades diferentes no rate limit. Os fixtures foram corrigidos para representar bancos históricos reais e o teste passou a reutilizar o mesmo principal autenticado.

**PASS** — regressões corrigidas; nova execução completa aprovada.

### 10/10 — CI final e relatório
No commit exato `c5f82ea17562aa8a1c4781c1584f907a0fbda403`:
- Messenger Backend Test #772, run `45920527415`: **SUCCESS**; log confirma **207 testes executados, OK**.
- Android Build #1368, run `45920527390`: **SUCCESS**; testes Android, gerador de manifest e build APK Debug concluídos.

**PASS** — código, migração, testes multiprocessos, HTTP e build Android no mesmo SHA.

## Arquivos principais
- `server/sqlite_store.py` — schema v4 e operação atômica do ledger.
- `server/rate_limit.py` — `SQLiteSlidingWindowRateLimiter`.
- `server/http_server.py` — integração e bloqueio de bind público sem contrato TLS.
- `server/runtime_config.py` — validação do contrato de transporte.
- `server/recovery.py` — validação read-only do schema v4.
- `server/test_rate_limit.py` — concorrência com processos independentes.
- `server/test_http_e2e.py` — limite compartilhado entre endpoints.
- `server/test_messenger_invitation_schema.py` — migrações v1/v2/v3 para v4.
- `server/test_runtime_config.py` — testes do contrato TLS.

## Veredito

**PASS — engenharia local/CI:** limite compartilhado entre processos no mesmo arquivo SQLite; migração v4; validação read-only v4; barreira fail-closed para bind público; 207 testes backend e build Android aprovados.

**BLOCKED — infraestrutura multi-host:** rate limit ainda não é distribuído entre hosts com bancos/discos independentes. Para isso, será necessário um armazenamento compartilhado apropriado (por exemplo, PostgreSQL ou Valkey/Redis), com transações/atomicidade e infraestrutura autorizada.

**BLOCKED — HTTPS público real:** não houve deploy, certificado, domínio, handshake TLS ou teste externo. A configuração `MESSENGER_TLS_TERMINATED` é uma declaração operacional, não prova de que o proxy realmente está protegendo o tráfego.

**BLOCKED — persistência hospedada:** `render.yaml` continua deliberadamente em modo ephemeral e readiness permanece fail-closed. Exige disco persistente e configuração real do ambiente.

**NO-GO:** merge, deploy, criação de infraestrutura, Secrets/Variables, Release, instalação Android e ativação da comunicação AI-01↔AI-02 em produção.

Nenhum merge, deploy, Release, instalação, alteração de Secrets/Variables ou `workflow_dispatch` foi realizado. AI-03 permanece desativada.
