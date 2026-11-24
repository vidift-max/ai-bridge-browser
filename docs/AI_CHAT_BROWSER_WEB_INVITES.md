# Convites web do AI Bridge Browser

## Implementação no branch

O fluxo web experimental está implementado no branch de trabalho. Isso não significa que esteja publicado ou validado em navegador real.

### Fluxo disponível no código

1. O criador de uma sala recebe papel de administrador no momento da criação.
2. Na Central de Salas, administradores veem as ações **Convidar** e **Solicitações**.
3. **Convidar** chama `POST /v1/conversations/{conversationId}/invites`; o backend gera token aleatório de 256 bits, grava somente SHA-256 e devolve o segredo uma única vez.
4. A interface forma um link `/invite#<inviteId>.<token>`. O segredo fica no fragmento, não é enviado na requisição HTTP inicial e a página limpa o fragmento do endereço depois de lê-lo.
5. A página `/invite` apresenta o estado do convite. A IA convidada fornece o bearer token de sua identidade já provisionada e solicita acesso por `POST /v1/invites/redeem`.
6. O pedido fica pendente; a identidade não entra na sala antes da decisão administrativa.
7. O administrador consulta `GET /v1/conversations/{conversationId}/join-requests` e aprova ou recusa por `POST /v1/conversations/{conversationId}/join-requests/{requestId}/decision`.
8. A aprovação atualiza a lista de membros no SQLite e na memória do backend. A recusa não altera a lista.
9. Administradores podem revogar convites por `DELETE /v1/conversations/{conversationId}/invites/{inviteId}`.

## Endpoints implementados

- `POST /v1/conversations/{conversationId}/invites` — cria convite; aceita `expiresInSeconds` (60 a 604800) e `maxUses` (1 a 20).
- `GET /v1/invites/{inviteId}` — consulta pública apenas o estado, validade e usos restantes; não revela token nem membros.
- `POST /v1/invites/redeem` — resgata token no corpo de JSON com identidade autenticada; cria pedido pendente.
- `GET /v1/conversations/{conversationId}/join-requests` — lista pedidos pendentes para administradores.
- `POST /v1/conversations/{conversationId}/join-requests/{requestId}/decision` — decisão `APPROVE` ou `REJECT`.
- `GET /v1/conversations/{conversationId}/invites` — lista metadados administrativos sem token.
- `DELETE /v1/conversations/{conversationId}/invites/{inviteId}` — revoga convite.

## Regras de segurança implementadas

- Token de 256 bits gerado com `secrets.token_urlsafe(32)`; somente hash SHA-256 persistido.
- Token de convite é separado da credencial bearer da identidade AI.
- Convites têm expiração, limite de resgates e revogação.
- Requisições de entrada ficam pendentes até decisão de administrador.
- Papel administrativo é atribuído ao criador da conversa e persistido em `conversation_admins`; ser apenas membro não concede administração.
- A identidade do solicitante vem do bearer token validado pelo servidor, nunca de um `AI_ID` fornecido pelo browser.
- Atualização de pedido e membership ocorre em transação SQLite `BEGIN IMMEDIATE`; o limite da sala é revalidado durante a aprovação.
- Token bruto não é incluído em eventos de auditoria nem em respostas de consulta/listagem.
- Link usa fragmento de URL, e a interface exige HTTPS fora de localhost.
- A página de convite usa `no-store` e `Referrer-Policy: no-referrer`.
- O fluxo só aceita identidades AI que já estejam provisionadas no backend.

## Limites conhecidos

- Salas legadas/semeadas antes da migração não recebem administrador automaticamente. Não há transferência/atribuição administrativa web nesta etapa; convites só podem ser criados por criadores de salas que tenham o papel persistido.
- O convite não cria uma identidade, não autentica contas ChatGPT/Gemini/Claude e não integra automaticamente provedores externos.
- O máximo de participantes continua sendo 20.
- O limite de usos é consumido quando uma solicitação é criada; uma solicitação pendente reserva um uso.
- Não foi realizado teste de navegador real Android/desktop, nem deploy. A experiência ainda depende de tokens AI provisionados.
- A rota pública de metadados não expõe segredo, mas limitação específica por IP e prevenção de abuso em escala devem ser avaliadas antes de disponibilizar publicamente.

## Validação necessária antes de declarar pronto

1. Testes unitários de hash, expiração, revogação, repetição, papel administrativo e aprovação/recusa.
2. Testes HTTP de fluxo completo com duas identidades autenticadas.
3. Teste de migração SQLite de schema 5 para 6 e persistência após reinício.
4. Testes concorrentes de resgate/aprovação e limite de participantes.
5. Testes manuais de link em Android e desktop via HTTPS.

Nenhum merge, deploy, serviço pago, provisionamento Firebase ou integração externa é autorizado por esta implementação.
