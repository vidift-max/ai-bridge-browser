# Convites web do AI Bridge Browser — contrato e plano de implementação

## Estado verificado

A implementação de convites já existente no repositório é voltada ao Android/AI-PHONE e ao Firebase Realtime Database. O fluxo usa deep link `aibridge://invite/<conversationId>/<token>`, valida a identidade provisionada e permite a entrada no grupo. A documentação também descreve um futuro link HTTPS via Firebase Hosting, condicionado à criação de um projeto real e à associação Android por Digital Asset Links.

A Central de Salas web (`/` e `/rooms`) ainda não possui endpoints próprios para criar, visualizar, aprovar, revogar ou resgatar convites. Não se deve confundir a implementação Android/Firebase com um fluxo web já funcional.

## Objetivo

Permitir que um administrador de sala gere um link simples que abra uma página web de convite. O link apresenta o nome e as regras da sala; o convidado solicita acesso; um administrador aprova ou recusa. A entrada efetiva exige uma identidade autenticada e provisionada pelo backend.

## Fluxo pretendido

1. Um membro com permissão administrativa abre a sala e seleciona **Convidar IA**.
2. O servidor cria um token aleatório de alta entropia, guarda somente seu hash e vincula o convite a uma sala específica.
3. O convite tem validade curta configurável, limite de resgates e estado revogável.
4. O link HTTPS usa um fragmento, por exemplo `https://<host>/i#<token>`, para que o segredo não seja enviado automaticamente em requisições HTTP nem apareça como parâmetro de consulta nos logs do servidor.
5. A página de entrada lê o fragmento e envia o token no corpo de uma requisição HTTPS autenticada; nunca o coloca em logs, analytics ou armazenamento persistente.
6. O convidado vê o resumo da sala e solicita entrada. O token, sozinho, não cria identidade, não autentica uma conta ChatGPT/Gemini/Claude e não concede privilégios administrativos.
7. O administrador aprova ou recusa a solicitação.
8. Após aprovação e autenticação válida, o backend adiciona a identidade à sala, registra auditoria e atualiza a lista de participantes.
9. O link mostra confirmação clara: solicitado, aguardando aprovação, aprovado, expirado, revogado ou inválido.

## Contratos de API propostos

- `POST /v1/conversations/{conversationId}/invites`: criar convite. Requer autenticação e permissão administrativa. Entrada: validade e limite de usos dentro dos limites do servidor. Saída: URL completa exibida uma única vez e metadados não secretos.
- `GET /v1/invites/{inviteId}`: consultar informações públicas mínimas do convite, sem revelar membros, tokens ou dados privados da sala.
- `POST /v1/invites/redeem`: enviar token no corpo, com identidade autenticada, para registrar pedido de entrada. Não adiciona membro antes da aprovação.
- `GET /v1/conversations/{conversationId}/join-requests`: listar solicitações somente para administradores da sala.
- `POST /v1/conversations/{conversationId}/join-requests/{requestId}/decision`: aprovar ou recusar, somente por administrador autorizado.
- `DELETE /v1/conversations/{conversationId}/invites/{inviteId}`: revogar convite, somente por administrador autorizado.

Esses contratos são uma proposta de implementação, não endpoints atualmente disponíveis.

## Regras de segurança obrigatórias

- Token aleatório com pelo menos 192 bits de entropia; persistir somente hash criptográfico.
- Token vinculado a uma sala e a uma finalidade; não é token de sessão nem credencial de API.
- Expiração, limite de usos, revogação e proteção contra repetição.
- Aprovação humana antes de adicionar um novo participante, salvo uma política automática futura explicitamente autorizada e limitada.
- Verificação de identidade e permissão no servidor em toda operação; nunca confiar em `AI_ID` informado pelo navegador.
- Limite de participantes aplicado no backend e dentro de transação atômica.
- Rate limit por identidade e por origem; respostas de erro sem revelar se um convite privado existe.
- Auditoria de criação, consulta administrativa, pedido, aprovação, recusa, revogação e resgate.
- Tokens e credenciais nunca em query strings, logs, analytics, HTML público ou `localStorage`.
- O convite não contorna o isolamento entre salas nem a autenticação das plataformas externas.

## Compatibilidade com o AI-PHONE/Firebase

O fluxo Android existente pode continuar como caminho separado. A futura página web não deve assumir que o Firebase já está provisionado: o projeto Firebase real, domínio Hosting, regras publicadas, identidade autorizada e associação Android ainda precisam ser comprovados. Não criar dependência paga para habilitar a experiência web.

## Critérios de aceite

1. Membro sem permissão administrativa não consegue criar nem revogar convites.
2. Convite expirado, revogado, esgotado ou adulterado é recusado.
3. Token nunca aparece em logs, query string ou resposta de listagem.
4. Abrir o link sem autenticação não adiciona ninguém à sala.
5. Conta externa sem integração autorizada não é mostrada como IA conectada.
6. Pedido de entrada fica pendente até decisão administrativa.
7. Aprovação adiciona somente a identidade autenticada e respeita o limite da sala, inclusive com pedidos concorrentes.
8. Recusa não altera a lista de membros.
9. Auditoria registra as decisões sem armazenar o token em claro.
10. Fluxo é coberto por testes unitários e HTTP; teste em navegador Android e desktop é feito separadamente antes de declarar disponibilidade.

## Próxima implementação recomendada

Implementar primeiro o armazenamento durável de convites e solicitações no backend SQLite, com transações e testes de concorrência. Depois adicionar endpoints autenticados, página web de convite e integração à Central de Salas. Até essa implementação e validação, convites web permanecem **NÃO IMPLEMENTADOS**.

Nenhum deploy, merge, provisionamento Firebase, gasto pago ou integração externa é autorizado por este documento.
