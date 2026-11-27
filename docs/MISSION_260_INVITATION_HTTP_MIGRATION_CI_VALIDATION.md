# M260 — VALIDAÇÃO HTTP, MIGRAÇÃO SQLITE E CI DO CICLO DE CONVITES

Data: 2026-11-26/27 (UTC dos workflows: 2026-11-27)
Branch: `feat/mission-241-updater-backport-v2-saas-alpha`
Escopo: AI-01 / AI-02
AI-03: desativada
WebRTC e Termux: fora do escopo

## Rodadas — 10/10

### 01/10 — Estado dos workflows M259
Consultados os workflows do commit `aaf6caaa01533832bf22c5d3447b7cfc5cfc284f`.
- Messenger Backend Test #752: FAILURE.
- Android Build #1348: FAILURE.

**PASS** — estado final e jobs identificados por API do GitHub.

### 02/10 — Diagnóstico backend
Logs do job `140244737725`: 196 testes passaram e um teste falhou.
Causa: `server/test_http_e2e.py` chamava `sqlite3.connect` sem importar o módulo, gerando `NameError: name 'sqlite3' is not defined`.

**PASS** — falha localizada na linha do teste; sem indício de falha do runtime do servidor.

### 03/10 — Diagnóstico Android
Logs do job `140244737954`: compilação Java falhou em `InviteLinkParser.java:41`, porque a expressão regular continha escapes inválidos para string Java. A etapa de build APK foi corretamente ignorada após falha nos testes/compilação.

**PASS** — erro de compilação reproduzido nos logs do CI.

### 04/10 — Correção do teste backend
Adicionado `import sqlite3` a `server/test_http_e2e.py`.
Commit: `cc090d77ca4b3b021b5c8cd335091750cd4db5fb`.

**PASS** — correção mínima, sem mudança no código de produção.

### 05/10 — Correção do parser Android
Expressão regular reescrita usando classes de ponto `[.]`, evitando escapes ilegais na string Java e mantendo a restrição ao domínio HTTPS `*.web.app`.
Commit: `acd5a09b472c254391efa2e101c58f704b3d494b`.

**PASS** — Android Build #1350 e Messenger Backend Test #754 concluíram SUCCESS nesse commit.

### 06/10 — Integração HTTP real de convites
Adicionados testes com `ThreadingHTTPServer` e cliente HTTP local:
- emissão autenticada de convite;
- hash persistido de 64 caracteres diferente do token em claro;
- rejeição de destinatário incorreto;
- aceite pelo AI_ID de destino;
- rejeição de replay;
- revogação somente pelo criador;
- convite revogado não pode ser aceito.

Arquivo: `server/test_http_e2e.py`.

**PASS** — cobertura de fluxo HTTP ponta a ponta adicionada ao CI.

### 07/10 — Migração v2 → v3
Adicionado teste que constrói estado equivalente ao schema v2, remove a coluna `conversation_kind`, preserva a tabela de convites e reabre o banco.
Verifica:
- versão final 3;
- conversas antigas classificadas GROUP;
- convite PENDING preservado;
- hash preservado.

Arquivo: `server/test_messenger_invitation_schema.py`.

**PASS** — migração v2→v3 coberta por teste automatizado. Os testes existentes também cobrem v1→v3 e validação read-only de restore v1/v2/v3.

### 08/10 — Concorrência, replay e limites
Revisados os testes de single-use com duas instâncias SQLite independentes, replay, expiração, revogação, PRIVATE e limite GROUP de 20 membros.
O aceite usa `BEGIN IMMEDIATE`, valida novamente status/expiração e atualiza convite + membership na mesma transação.

**PASS (cobertura de repositório/CI)** — concorrência entre instâncias e invariantes transacionais cobertos.
**LIMITAÇÃO** — não foi executado teste dedicado com processos de sistema operacional distintos.

### 09/10 — Revisão de segurança e operação
Confirmado no código:
- respostas HTTP incluem `Cache-Control: no-store`;
- rotas de convite exigem principal autenticado e rate limiter;
- auditoria registra IDs/estado, não o token;
- respostas de falha de convite são genéricas;
- o servidor experimental usa HTTP local e não comprova terminação TLS/HTTPS em proxy público;
- não há prova de serviço implantado, rede entre dispositivos ou comunicação real AI-01↔AI-02.

**PASS (revisão estática)** — controles locais identificados.
**BLOCKED (produção)** — HTTPS público, rate limit distribuído e operação multi-instância implantada não foram demonstrados.

### 10/10 — CI final e veredito
Validação do commit de código `0d4565ea46b0f248efc41b4167ca47c1c863f7b0`:
- Messenger Backend Test #756, run `45919580328`: **SUCCESS**; log confirma **200 testes executados, OK**.
- Android Build #1352, run `45919580314`: **SUCCESS**; testes Android, gerador de manifest e build do APK Debug concluídos com sucesso.
- O workflow não publicou artefato APK nesse run (lista de artifacts vazia).

**PASS:** correções backend/Android, 200 testes backend, testes Android, build Debug e migração v2→v3 coberta.
**BLOCKED:** teste dedicado multi-processo OS, TLS público, rate limit distribuído, deploy e comunicação real entre dispositivos.
**NO-GO:** merge, Release, instalação Android, ativação de comunicação de produção e declaração de serviço público funcional.

## Commits relevantes
- `cc090d77ca4b3b021b5c8cd335091750cd4db5fb` — import ausente no teste HTTP.
- `acd5a09b472c254391efa2e101c58f704b3d494b` — regex Java corrigida.
- `6c8d4ce066973917b6b0a0905a3ceb775d7e0cbd` — testes HTTP de convite.
- `0d4565ea46b0f248efc41b4167ca47c1c863f7b0` — migração v2→v3 testada e CI final verde.

## Estado operacional
Nenhum merge, deploy, Release, instalação, workflow_dispatch, alteração de Secrets/Variables ou acesso a banco de produção foi realizado. AI-03 continua desativada; WebRTC e Termux continuam fora do escopo.
