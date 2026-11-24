# Contrato proposto: AI Messenger ↔ Blogger SEO Intelligence

## Situação verificada

Repositório de destino: `vidift-max/blogger-cannibalization-mcp`, branch `v2-saas-alpha`.

O README e `src/routes.js` confirmam que o Blogger SEO Intelligence já possui:
- OAuth Google/Blogger e tokens OAuth cifrados no banco.
- Sessão de usuário em cookie e proteção CSRF para operações de escrita.
- `GET /blogs` para listar blogs autorizados.
- `GET /blogs/:blogId/share-feed` para obter posts e páginas.
- `POST /blogs/:blogId/sync` para sincronizar artigos.
- `POST /blogs/:blogId/analyze` para análise heurística.
- `POST /posts/:postId/proposals` para salvar proposta de HTML sem publicar.
- `GET /proposals` para listar propostas.
- `POST /proposals/:id/approve` para aplicar proposta após ação explícita do usuário.
- `POST /proposals/:id/restore` para restauração.

O fluxo atual é orientado à sessão web do usuário. Não foi encontrada, nesta inspeção, uma API de serviço-a-serviço para o AI Messenger. As rotas existentes não devem ser chamadas por uma IA fingindo ser o usuário ou reutilizando cookie/CSRF pessoal.

O README do Blogger SEO Intelligence também declara limitações: editor visual de propostas incompleto, aprovação/restauração sem transação distribuída com Blogger, limite de requisições em memória e necessidade de testes de integração reais. Portanto, não tratar o projeto como pronto para clientes ou automação irrestrita.

## Princípio de integração

O AI Messenger coordena as IAs; o Blogger SEO Intelligence continua sendo a autoridade sobre os blogs, os tokens OAuth do usuário, as propostas e as operações no Blogger.

A integração deve usar uma identidade de serviço própria, autenticada e autorizada pelo usuário. Não compartilhar cookies de sessão, CSRF, refresh tokens ou credenciais Google com IAs.

## API de serviço proposta (a implementar)

Prefixo sugerido: `/api/integrations/ai-messenger/v1`.

### 1. Registrar uma tarefa editorial

`POST /jobs`

Entrada:
- `externalMissionId`: ID da missão no AI Messenger.
- `blogId`: ID interno do blog no Blogger SEO Intelligence.
- `taskType`: `ANALYZE`, `DRAFT`, `REVISE` ou `INTERNAL_LINK_REVIEW`.
- `objective`: objetivo editorial.
- `constraints`: limites, público, idioma, palavras-chave e instruções aprovadas.
- `inputReferences`: IDs de posts sincronizados, nunca URLs arbitrárias para acesso irrestrito.
- `idempotencyKey`: chave única para evitar tarefas duplicadas.

Resposta: `202 Accepted` com `jobId`, estado `QUEUED` e timestamp.

### 2. Consultar tarefa

`GET /jobs/{jobId}`

Resposta:
- estado `QUEUED`, `RUNNING`, `BLOCKED`, `REVIEW`, `DONE` ou `FAILED`;
- timestamps e último checkpoint;
- entregáveis disponíveis;
- erros resumidos sem segredos.

### 3. Enviar entregável

`POST /jobs/{jobId}/deliverables`

Tipos permitidos:
- análise SEO estruturada;
- proposta de título e metadados;
- texto do artigo;
- HTML candidato;
- sugestões de links internos;
- relatório de revisão e fontes.

Cada entregável deve incluir `agentId`, `contentHash`, versão, referências de origem, limitações e data. O servidor valida tamanho, formato e permissão.

### 4. Preparar proposta para revisão humana

`POST /jobs/{jobId}/proposals`

Cria uma proposta/backup no Blogger SEO Intelligence. A resposta deve deixar explícito:
- proposta pendente;
- conteúdo/hash exato;
- post de destino, se houver;
- diff/resumo;
- aviso de que nada foi publicado.

### 5. Consultar aprovação

`GET /jobs/{jobId}/approval`

Retorna `PENDING`, `APPROVED`, `REJECTED` ou `CHANGES_REQUESTED`, com usuário aprovador e versão/hash aprovado quando aplicável.

A aprovação deve ocorrer na interface do usuário do Blogger SEO Intelligence ou numa interface humana confiável integrada. Uma IA, inclusive GPT-6, não pode aprovar a própria proposta.

### 6. Notificar conclusão

Webhook assinado do Blogger SEO Intelligence para o AI Messenger:
- `jobId`;
- `externalMissionId`;
- estado;
- ID da proposta;
- versão/hash;
- link para revisão;
- timestamp e identificador do evento.

Validar assinatura HMAC, timestamp, nonce/idempotência e origem. Webhook não deve conter token OAuth ou conteúdo completo se um ID autenticado for suficiente.

## Modelo de autorização

- Serviço AI Messenger: identidade própria e segredo rotacionável.
- Usuário: concede explicitamente acesso do AI Messenger ao blog selecionado.
- Blog: autorização vinculada ao usuário dono e ao ID interno do blog.
- Escopos independentes: `blog.read`, `analysis.run`, `draft.create`, `proposal.create`, `proposal.read`.
- Ação `blog.publish` não é concedida ao agente. A publicação continua protegida por aprovação humana no sistema Blogger SEO Intelligence.
- Revogação de acesso deve invalidar chamadas futuras e impedir jobs pendentes de executar novas operações.

## Regras de execução

1. Nunca aceitar `blogId` sem confirmar que pertence ao usuário que concedeu a integração.
2. Nunca aceitar `userId` ou papel administrativo confiado apenas ao payload.
3. Limitar tamanho do prompt, HTML, anexos, frequência e custo por missão.
4. Sanitizar HTML e validar links antes de salvar proposta.
5. Usar idempotência em criação de jobs/propostas e webhooks.
6. Preservar snapshot do post original e comparar versão atual do Blogger antes de qualquer aplicação.
7. Se o post mudou depois da sincronização, bloquear e pedir nova sincronização/revisão.
8. Manter auditoria de ator humano, agente, missão, blog, post, hash, operação e resultado.
9. Não publicar nem atualizar post por execução autônoma de IA.
10. Nunca registrar tokens, cookies, CSRF, API keys ou refresh tokens nos logs.

## Fluxo de ponta a ponta esperado

```
Usuário
  |
  v
AI Messenger (GPT-6 coordena)
  | cria missão e atribui subtarefas
  v
Agentes IA autorizados
  | análise, redação, revisão
  v
AI Messenger (consolida entregáveis)
  |
  v
Blogger SEO Intelligence (API serviço autenticada)
  | cria proposta pendente + diff + prévia
  v
Usuário revisa e aprova
  |
  v
Blogger SEO Intelligence aplica a proposta ao Blogger
  |
  v
Webhook/consulta de status
  |
  v
AI Messenger registra resultado e encerra missão
```

## Critérios de aceite da integração

- Chamadas sem autenticação de serviço recebem 401.
- Serviço sem concessão ao blog recebe 403.
- Uma identidade não consegue ler ou alterar blogs de outro usuário.
- Repetir uma requisição com a mesma chave de idempotência não duplica job/proposta.
- A IA consegue criar apenas proposta pendente.
- A IA não consegue aprovar nem publicar.
- Usuário consegue revisar o conteúdo exato associado ao hash aprovado.
- Mudança concorrente do post bloqueia aplicação e exige nova sincronização.
- AI Messenger recebe estado final verificável.
- Testes usam mocks primeiro e depois uma conta Blogger de teste explicitamente autorizada.

## Estado

- Inspeção estática de README, rotas e adaptador Blogger: concluída.
- Rotas atuais identificadas: documentadas acima.
- API de serviço-a-serviço: proposta, ainda não implementada.
- Identidade de serviço e autorização por blog: não implementadas.
- Webhooks: não implementados.
- Execução real de missão integrada: não testada.
- Nenhum blog foi alterado, nenhuma publicação foi feita e nenhuma credencial nova foi configurada.
