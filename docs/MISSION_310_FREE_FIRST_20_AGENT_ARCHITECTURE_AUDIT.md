# M310 — arquitetura gratuita e central de 20 agentes
Data: 2026-11-27
Branch: `feat/mission-295-m241-ai-first-contact-integration`
PR #242: OPEN / Draft; não mesclado.

## Dez rodadas

### 01/10 — identidade independente: PASS (auditoria do código)
Package/namespace `com.vidiftmax.aibridgebrowser`, label `AI Bridge Browser` e launcher `.MainActivity`. O workflow contém verificações para rejeitar launcher AI-PHONE/Messenger. Instalação física ainda não comprovada.

### 02/10 — infraestrutura paga: PASS (contenção)
M309 Render exige compute + disco persistente, estimativa registrada de US$ 7,25/mês, e o planejamento retornou `need_payment_info`. Nada foi provisionado. Render pago está excluído; não adicionar cartão nem sincronizar o Blueprint.

### 03/10 — política de 20 agentes: PASS (código adicionado)
`AgentRosterPolicy.java` valida IDs canônicos AI-01…AI-20 e separa 20 identidades lógicas de no máximo duas sessões de provedor. Escopo externo atual continua AI-01/AI-02. Testes adicionados, ainda sem resultado CI confirmado.

### 04/10 — registro lógico: PASS (código adicionado)
`AgentRoster.java` registra, consulta, altera status e remove agentes sem criar WebViews, contas externas, credenciais ou rede. Testes adicionados, ainda sem resultado CI confirmado.

### 05/10 — arquitetura gratuita: PASS (decisão documentada)
`docs/FREE_FIRST_AGENT_ROOM_ARCHITECTURE.md` estabelece local-first e Firebase Spark como candidato remoto opcional, nunca dependência obrigatória. A documentação oficial descreve Spark sem necessidade de método de pagamento; Realtime Database tem quota de 100 conexões simultâneas, 1 GB armazenado e 10 GB/mês de downloads. Exceder quota pode interromper o serviço até o próximo ciclo. Nenhum projeto Firebase foi criado/alterado; confirmar plano e quotas reais antes de integrar.

### 06/10 — codec local versionado: PASS (código adicionado)
`AgentRosterCodec.java` serializa o roster em JSON schemaVersion 1 e rejeita esquema desconhecido, registros inválidos, duplicatas e status inválidos. Testes adicionados. Ainda não está ligado ao armazenamento Android nem validado após reinício.

### 07/10 — contrato da sala: PASS (documentação)
Contrato define eventId idempotente, roomId, sequência, remetente, visibilidade ROOM/PRIVATE, destinatário, tipo, data, payload, ACK após persistência, paginação, replay e autorização. Transporte remoto não implementado.

### 08/10 — fila e escalonamento: PASS (código adicionado)
`AgentMissionQueue.java` implementa fila FIFO, IDs únicos e estados QUEUED/RUNNING/COMPLETED/CANCELLED; limita execução ativa a duas sessões. Não abre contas ou WebViews automaticamente. Testes adicionados, CI ainda não confirmado.

### 09/10 — testes: PARTIAL / BLOCKED
Suítes adicionadas para política, roster, codec e fila. Não foi possível recuperar run de Actions para os commits desta sequência; nenhum desses testes é declarado como executado/aprovado. CI precisa ser executado e qualquer falha corrigida.

### 10/10 — APK: BLOCKED
Workflow existente prepara APK debug e artefato temporário quando executado. Release oficial depende de keystore/certificado confirmado; os secrets atuais usam nomes legados AI_PHONE e não foram alterados. Não houve build de release, publicação, instalação ou entrega de APK.

## Arquivos adicionados
- `docs/FREE_FIRST_AGENT_ROOM_ARCHITECTURE.md`
- `app/src/main/java/com/vidiftmax/aibridgebrowser/AgentRosterPolicy.java`
- `app/src/main/java/com/vidiftmax/aibridgebrowser/AgentRoster.java`
- `app/src/main/java/com/vidiftmax/aibridgebrowser/AgentRosterCodec.java`
- `app/src/main/java/com/vidiftmax/aibridgebrowser/AgentMissionQueue.java`
- Testes correspondentes em `app/src/test/java/com/vidiftmax/aibridgebrowser/`.

## Commits
- `2ea5404c03e5a056a123827528b138062df43ad3` auditoria inicial.
- `58e22e355abb07c95f8341abaf7c849a71a96247` política roster.
- `282fbbfcccbd9abb3cc8972c2747218fe1f430cd` testes política.
- `0ed34bd4d40b900fa881067c4a4ad10bbad99ee8` registro.
- `24c9f83c274a2883876c5543119858e032b8d502` testes registro.
- `f4298a82cc9feac260fe5fa956ae39a927e96fc2` fila.
- `a9d91a42e7a1fab862bf7bd51370ff4828eec99f` testes fila.
- `44c47db0755f3c90dde8cfbefc51bafe9a321b66` codec.
- `a41b13810ec6880ecbf4cde7027df202468df8f7` testes codec.
- `1c4147e55baa3d16c06b2cd18632447dd1f8c251` arquitetura gratuita.

## Regras permanentes
1. AI Bridge Browser é separado do AI Phone em package, ícone, nome, instalação e atualizações.
2. Recursos essenciais gratuitos; sem cobrança ou cartão obrigatório.
3. Não provisionar Render pago nem sincronizar Blueprint M309.
4. Vinte agentes lógicos não significam 20 contas ou 20 WebViews.
5. Sessões externas continuam limitadas a AI-01/AI-02, no máximo duas simultâneas até teste de desempenho.
6. Não confundir código adicionado com teste executado, CI com teste físico ou APK debug com release assinado.
7. Sem merge, Release, instalação, deploy ou alteração de Secrets/Variables sem autorização.

## Estado final
Dez rodadas executadas e registradas. Implementados em código: política de IDs, roster lógico em memória, codec JSON e scheduler FIFO, com suítes de teste adicionadas. Documentados: arquitetura local-first, candidato Firebase Spark e contrato de sala. Bloqueios restantes: persistência real no Android, provisionamento/verificação de Firebase Spark sem billing, transporte remoto, integração de interface, execução CI, build APK, assinatura e teste físico no tablet. Nenhum serviço pago, cartão, secret, merge, deploy ou APK final foi alterado/entregue.
