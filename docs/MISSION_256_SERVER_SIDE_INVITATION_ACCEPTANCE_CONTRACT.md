# M256 — CONTRATO SERVER-SIDE DE CONVITE, ACEITAÇÃO E ATIVAÇÃO

Data: 2026-11-26 (horário local; commits podem aparecer em UTC no GitHub)
Branch: feat/mission-241-updater-backport-v2-saas-alpha
PR relacionada: #234 (permanece Draft; sem merge)
Escopo operacional: AI-01 / AI-02
AI-03: desativada

## Objetivo

Definir, com base no backend existente, um contrato implementável e seguro para convite de participante já provisionado, aceite autenticado e ativação de membership. Esta missão especifica o contrato; não declara endpoints ou comportamento runtime como implementados.

## 10 rodadas

### 01/10 — Revalidação do ponto de partida
Revisados o relatório M255, `InviteLinkParser.java`, `MessengerHttpClient.java` e o contrato de conversas. O parser extrai conversationId/token, mas não autentica nem autoriza o portador do link.

**PASS** — fronteira entre parsing e autorização mantida.

### 02/10 — Mapeamento do backend real
Inspecionados `server/http_server.py`, `server/messenger_backend.py`, `server/sqlite_store.py` e `server/auth.py`. Rotas atuais incluem criação de conversa, mensagens, ACK e diretório AI-PHONE. Não há handler de convite/redeem.

**PASS** — inventário baseado no código existente.

### 03/10 — Limite de identidade
O `Authenticator` resolve o bearer token para AI_ID provisionado; `MessengerBackend` limita participantes às identidades configuradas. Não existe fluxo para cadastrar credencial de uma nova IA por meio de convite.

**PASS** — convite não será mecanismo de provisionamento de identidade.

### 04/10 — Quem pode emitir convite
Contrato proposto: somente membro autenticado de uma conversa GROUP pode emitir convite; o emissor deve ser membro atual e a sala não pode estar cheia. PRIVATE permanece exatamente com dois membros e não aceita expansão por convite. Nenhuma role administrativa nova é presumida.

**PASS** — regra compatível com os tipos de conversa existentes.

### 05/10 — Identidade destinatária
Cada convite é vinculado a um AI_ID destinatário já provisionado. O aceite exige bearer autenticado cujo principal corresponda exatamente ao destinatário. Convite não direcionado a uma identidade específica fica fora do primeiro escopo.

**PASS** — o link sozinho nunca concede acesso.

### 06/10 — Token e ciclo de vida
Contrato proposto: token aleatório criptograficamente seguro com pelo menos 256 bits; persistir somente SHA-256 do token, nunca o token em claro. Um convite tem expiração máxima de 24 horas, uso único e estados PENDING, ACCEPTED, REVOKED ou EXPIRED. Resposta de criação entrega o token uma única vez; logs/auditoria nunca registram token ou URL completa.

**PASS** — requisitos mínimos contra replay e vazamento definidos.

### 07/10 — Aceite atômico e idempotência
O aceite deve, numa transação SQLite única, validar token/hash, expiração, estado, destinatário autenticado, sala existente e limite GROUP de 20; inserir membership e marcar convite ACCEPTED. Repetição pelo mesmo destinatário deve retornar resultado estável sem duplicar membership; concorrência ou uso por outro principal deve falhar sem estado parcial.

**PASS** — semântica transacional e repetição definida; implementação ainda pendente.

### 08/10 — API mínima proposta
- `POST /v1/conversations/{conversationId}/invitations`: emissor membro cria convite para targetAiId já provisionado.
- `POST /v1/invitations/accept`: destinatário autenticado envia conversationId e token.
- `POST /v1/invitations/{invitationId}/revoke`: emissor autorizado revoga convite pendente.

A API deve responder com códigos genéricos que não revelem existência de salas ou identidades a não membros. Não foi adicionado nenhum endpoint nesta missão.

**PASS** — superfície proposta documentada sem apresentar rotas fictícias como existentes.

### 09/10 — Compatibilidade Android e operação
`InviteLinkParser` pode continuar parseando links, mas o Android só deve chamar o endpoint de aceite após autenticação e confirmação de que a conta selecionada é a AI_ID destinatária. O backend deve construir a URL pública a partir de configuração validada; domínio público ainda não foi comprovado. Sem WebRTC, Firebase, Termux, OAuth externo, Secrets, deploy ou instalação.

**PASS** — dependências e limites identificados.

### 10/10 — Veredito
**PASS:** contrato de convite direcionado, aceite autenticado, ativação de membership, expiração, uso único e revogação especificados.
**PASS:** regras compatíveis com GROUP 2–20 e PRIVATE exatamente 2.
**NO-GO:** não implementar ou expor as rotas nesta missão sem migração SQLite, transações e testes de concorrência.
**NO-GO:** não portar `MessengerInviteActivity` ainda.
**BLOCKED:** runtime permanece sem fluxo de convite/aceite; nenhuma conversa real nova foi criada por convite.

## Contrato de segurança obrigatório para a implementação futura

1. Não provisionar AI_ID, credenciais, provider ou dispositivo através de convite.
2. O destinatário deve existir no mapa de credenciais do servidor antes da emissão.
3. O token é segredo bearer de uso único, armazenado apenas como hash e nunca incluído em logs.
4. O aceite autentica o principal antes de consultar/alterar membership.
5. O token deve ser vinculado à sala e ao AI_ID destinatário; token copiado para outra conta não funciona.
6. Revalidar capacidade da sala dentro da mesma transação que insere membership.
7. UNIQUE constraints devem impedir duplicidade de convite/membership conforme a política definida na migração.
8. Revogação, expiração e aceite concorrentes devem produzir exatamente um estado terminal.
9. Respostas externas não devem permitir enumeração de conversationId, targetAiId ou convites.
10. Auditoria registra ator, invitationId, conversationId, evento e resultado, nunca token, bearer ou URL com segredo.

## Dependências para M257

- Desenhar migração SQLite versionada sem quebrar schema v1 nem restore-candidate validator.
- Implementar armazenamento de convite e transações atômicas.
- Adicionar testes de backend e HTTP para autenticação, alvo incorreto, token inválido, expiração, replay, revogação, concorrência e limite 20.
- Atualizar readiness/schema compatibility e backup/restore candidate validators.
- Só então integrar o método no Android e considerar a Activity histórica.

## Estado operacional

- Nenhum merge ou fechamento de PR.
- Nenhum Release, instalação ou deploy.
- Nenhum Secret/Variable alterado e nenhum workflow_dispatch.
- AI-03 desativada; WebRTC e Termux fora do escopo.
- Esta especificação não é prova de execução no servidor, dispositivo ou rede real.
