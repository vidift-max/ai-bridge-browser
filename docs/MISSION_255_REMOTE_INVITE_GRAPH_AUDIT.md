# M255 — AUDITORIA DO GRAFO DE CONVITE REMOTO E PORT SELETIVO

Data: 2026-11-27
Branch: feat/mission-241-updater-backport-v2-saas-alpha
PR: #234
Escopo: AI-01 / AI-02
AI-03: desativada

## Objetivo

Continuar a recuperação Android pelo grafo de convite remoto sem copiar Activities históricas isoladamente e sem puxar WebRTC para este lote.

## 10 rodadas

### 01/10 — Estado do parser recuperado
O componente `InviteLinkParser` já está presente na branch atual e permanece autocontido.

SHA do arquivo:
`ec141e2d86fbd111486a0c08d76175a5df7298aa`

Ele não exige Activity, Manifest, transporte remoto ou dependência externa.

**PASS**

### 02/10 — Contrato remoto existente
A API atual possui:
- `POST /v1/conversations`;
- `POST /v1/messages`;
- `GET /v1/conversations/{conversationId}/messages`;
- `POST /v1/messages/{messageId}/ack`;
- `GET /v1/me/phone`.

A criação de conversa exige identidades já provisionadas.

**PASS**

### 03/10 — Ausência de redeem/invite remoto
A implementação atual de `server/http_server.py` não expõe endpoint de criação, redeem, aceite ou ativação de convite.

Também não existe rota `redeem` ou `invite_token` no contrato atual recuperado.

**NO-GO — não inventar endpoint.**

### 04/10 — Semântica de identidade
O servidor aceita apenas identidades presentes no mapa de credenciais configurado. Criar uma conversa não provisiona nem convida uma nova IA.

Portanto, um link local contendo conversation ID/token não pode ser tratado como autorização de acesso ao servidor.

**PASS — fronteira de autorização preservada.**

### 05/10 — Compatibilidade com a Activity histórica
`MessengerInviteActivity` histórica depende de `CollectiveRoomActivityV2` e do grafo remoto correspondente.

A branch atual não possui um contrato de redeem/aceitação compatível para completar essa Activity.

**NO-GO — não adicionar a Activity ao Manifest.**

### 06/10 — Testes do parser
Foi adicionado:

`app/src/test/java/com/vidiftmax/aibridgebrowser/InviteLinkParserTest.java`

Commit:
`e2bcde10496db06499dba07270208aeb95b1cb6e`

O teste cobre:
- esquema `aibridge://invite`;
- HTTPS `*.web.app/i`;
- subdomínio;
- query/fragment/userinfo;
- token/conversation inválidos;
- porta e espaços externos;
- esquema/host incorretos;
- null/vazio e segmentos extras.

SHA final do arquivo:
`a172ddf4baabb5ed2674465e70a238eedb69d422`

**PASS — cobertura de fronteiras adicionada.**

### 07/10 — Verificação de CI
O commit do teste foi consultado no GitHub Actions.

Resultado:
`fetch_commit_workflow_runs = []`

Não há execução de CI associada a esse commit neste momento.

**BLOCKED — teste de CI ainda não comprovado.**

### 08/10 — Limite de participantes
O contrato remoto atual aceita grupos de 2 a 20 identidades provisionadas e exige que o criador autenticado esteja incluído.

Isso é compatível com o limite arquitetural, mas não cria automaticamente 20 contas nem resolve o onboarding de novos participantes.

**PASS — limite mantido sem ampliar escopo.**

### 09/10 — WebRTC e integrações externas
Nenhuma classe WebRTC, Firebase ou adapter de provedor foi adicionada nesta missão.

Nenhuma chamada a serviço externo, Secret, OAuth, workflow manual ou instalação foi executada.

**PASS — isolamento preservado.**

### 10/10 — Veredito
**PASS:** contrato de conversa remota existente foi confirmado.

**PASS:** ausência de endpoint de convite/redeem foi confirmada, evitando API fictícia.

**PASS:** parser de convite recebeu testes JVM de fronteira.

**NO-GO:** `MessengerInviteActivity` não deve ser portada isoladamente.

**BLOCKED:** o fluxo real de convite exige um contrato server-side de convite/aceitação/ativação que ainda não existe na implementação atual.

## Estado operacional

- Nenhum merge.
- Nenhum Release.
- Nenhuma instalação.
- Nenhum Secret/Variable alterado.
- Nenhum workflow_dispatch.
- AI-03 continua desativada.
- WebRTC permanece fora deste lote.

## Próxima missão — M256

Antes de portar novas Activities, definir ou recuperar, a partir de código existente e verificável, o contrato server-side de convite/aceitação/ativação. Somente depois disso avaliar o menor conjunto de classes Android necessário.
