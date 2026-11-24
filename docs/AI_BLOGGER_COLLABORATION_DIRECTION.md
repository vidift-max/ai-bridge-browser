# Direção do projeto: colaboração entre IAs e trabalho com Blogger

## Decisão de prioridade

A prioridade do AI Bridge / AI Messenger é **coordenação de IAs e execução de trabalho no Blogger**. Celulares físicos, Android, chamadas telefônicas e hardware não são requisitos para essa etapa. Clientes móveis ou WebViews poderão existir apenas como interfaces opcionais; o sistema deve funcionar na nuvem por navegador e APIs.

O objetivo não é criar apenas uma sala de bate-papo. É criar um ambiente em que GPT-6 e outras IAs autorizadas possam receber tarefas, conversar entre si, produzir entregáveis, revisar trabalho e colaborar nos blogs do usuário.

## Relação entre os projetos

- **Blogger SEO Intelligence**: ferramenta de trabalho editorial e SEO, conectada aos blogs do usuário. É responsável por leitura dos dados do Blogger, análise, criação/revisão de artigos, pré-visualização e publicação aprovada.
- **AI Messenger / AI Bridge**: camada de coordenação multi-IA. Distribui missões, mantém conversas, recebe relatórios e entregáveis, registra decisões e encaminha trabalho ao Blogger SEO Intelligence.
- **Blogger**: plataforma de publicação e origem dos blogs/artigos. Não deve receber chaves de IA nem credenciais administrativas expostas no navegador.

Os projetos permanecem modularizados. O AI Messenger não deve duplicar o editor/SEO do Blogger SEO Intelligence; deve coordenar e chamar suas capacidades por uma integração autenticada.

## Fluxo de trabalho pretendido

1. O usuário conecta e autoriza os blogs por OAuth oficial do Google/Blogger, com o menor escopo necessário.
2. O AI Messenger apresenta as IAs autorizadas e seus estados reais de disponibilidade.
3. O usuário ou GPT-6 cria uma missão editorial e seleciona blog, objetivo e limites.
4. GPT-6 divide o trabalho em tarefas pequenas e atribui tarefas às IAs disponíveis.
5. As IAs pesquisam/analisam apenas fontes e dados aos quais receberam acesso; cada uma entrega resultado identificado, fontes, limitações e estado.
6. GPT-6 consolida os resultados e envia o pacote editorial ao Blogger SEO Intelligence.
7. O Blogger SEO Intelligence executa estrutura, HTML/CSS, templates, links internos aprovados, validações e pré-visualização. Modelos externos devem receber somente o texto/dados e a inteligência necessária, evitando gastar tokens com tarefas determinísticas.
8. O usuário revisa a prévia e aprova ou solicita correções.
9. Publicação no Blogger somente após aprovação explícita do usuário. Nenhuma IA pode publicar automaticamente por conta própria.
10. O sistema registra o resultado, URL do post quando publicado, versão, autor/agente responsável e trilha de auditoria.

## Capacidades do AI Messenger

### Conversas e coordenação
- Sala geral de colaboração entre IAs autorizadas e usuário.
- Conversas privadas e conversas por missão.
- Identidade persistente por IA, sem depender de aparelho ou número telefônico.
- Mensagens com remetente autenticado, data, sequência e estado de entrega.
- Menções, atribuição de tarefas, handoff e retorno de resultados.
- Histórico de decisões e contexto de missão acessível aos participantes autorizados.

### Missões
- Criar, pausar, retomar e concluir missões.
- Estados explícitos: PENDING, ASSIGNED, RUNNING, BLOCKED, REVIEW, APPROVED, REJECTED, DONE.
- Tarefas com responsável, objetivo, entradas, prazo/checkpoint e entregável esperado.
- Relatórios de cada IA e consolidação por GPT-6.
- Rodadas de trabalho reais, sem contar commits ou mensagens triviais como rodadas.
- Checkpoints periódicos e indicação de bloqueios; nenhuma tarefa deve parecer ativa sem evidência de execução.

### Integração editorial com Blogger
- Selecionar entre blogs autorizados.
- Ler lista de posts, páginas, rótulos e metadados permitidos pelo escopo concedido.
- Solicitar análise SEO, risco de canibalização e oportunidades de links internos.
- Criar e revisar rascunhos sem publicar.
- Pré-visualizar conteúdo e metadados.
- Solicitar aprovação explícita antes de publicar ou atualizar conteúdo existente.
- Registrar o ID/URL do post e o resultado da operação após confirmação da API.

## Regras de segurança e confiança

- OAuth do Google/Blogger deve ser feito por fluxo oficial; nunca pedir ou guardar senha Google.
- Tokens OAuth e chaves de provedores de IA ficam no servidor, cifrados e fora do HTML, logs e repositório.
- Permissões por usuário, IA, missão, blog e operação.
- Separar leitura, criação de rascunho, atualização e publicação como permissões distintas.
- Publicação e atualização de posts exigem aprovação humana explícita, vinculada ao conteúdo/versão aprovada.
- Validar autorização no servidor; nunca confiar em `isAdmin`, papel ou identidade enviados pelo cliente.
- Registrar auditoria sem gravar segredos ou conteúdo sensível desnecessário.
- Limitar custos, requisições e tamanho de contexto por tarefa.
- Não afirmar que uma IA está online, conectada ou trabalhando sem heartbeat/resultado verificável.
- Não compartilhar um único token de serviço entre usuários como se fosse identidade individual.

## Estratégia de integração entre serviços

O AI Messenger deve expor uma API autenticada de missões, conversas, tarefas e entregáveis. O Blogger SEO Intelligence deve expor uma API de integração com operações explícitas e escopadas. A comunicação entre serviços usa identidades de serviço e permissões mínimas.

A primeira integração deve ser simples:
- criar/listar missão;
- enviar tarefa ao Blogger SEO Intelligence;
- receber status e entregável;
- devolver relatório à conversa da missão;
- preparar rascunho e prévia;
- exigir aprovação humana para publicar.

Não acoplar diretamente o AI Messenger ao banco interno do Blogger SEO Intelligence. Usar contratos de API versionados.

## Interface e legado Blogger Chat

Do arquivo legado `Blogger Chat.txt`, reaproveitar apenas padrões visuais úteis: layout mobile-first, lista de salas, cartões, balões, emojis, composição de mensagem, perfis e navegação. Remover o tema religioso e não reutilizar autenticação em JavaScript, senhas embutidas, dados fictícios, `localStorage` como banco compartilhado ou mídia Base64 local.

A interface deve priorizar:
1. painel de missões e estado;
2. sala de colaboração entre IAs;
3. conversa privada por IA;
4. painel de tarefas/entregáveis;
5. seleção do blog e status de integração;
6. revisão e aprovação editorial.

## Plano de implementação por fases

### Fase 1 — Base de coordenação
- Revisar contratos atuais de autenticação, conversas e mensagens.
- Definir identidade de IA independente de dispositivo.
- Definir modelo de missão, tarefa, checkpoint, relatório e entregável.
- Fazer a interface web ser a experiência principal.
- Testar troca real de mensagens entre dois agentes autenticados.

### Fase 2 — Adaptador do Blogger SEO Intelligence
- Definir contrato de API entre os dois projetos.
- Implementar autenticação serviço-a-serviço.
- Testar criação e consulta de missão editorial.
- Testar entrega de rascunho/prévia sem publicação.

### Fase 3 — Fluxo editorial seguro
- Conectar OAuth Blogger com escopos mínimos.
- Importar apenas os dados autorizados.
- Implementar revisão, versões e aprovação humana.
- Publicar somente após autorização explícita e verificar retorno da API.

### Fase 4 — Expansão multi-IA
- Adicionar provedores/adaptadores conforme disponibilidade e autorização.
- Implementar handoffs, presença, limites e relatórios.
- Executar missões multi-IA com evidência e checkpoints.
- Otimizar custo e retenção de contexto.

## Critérios de aceite

- O fluxo principal funciona sem celular físico e sem APK.
- Duas IAs autenticadas conseguem trocar mensagens em nuvem e produzir um entregável rastreável.
- Uma missão pode ser atribuída, acompanhada, bloqueada, retomada e concluída.
- O AI Messenger consegue enviar uma tarefa ao Blogger SEO Intelligence e receber status/resultado.
- Um artigo pode ser criado como rascunho e pré-visualizado.
- Nenhuma publicação ocorre sem aprovação humana explícita.
- Tokens e chaves não aparecem no navegador, no Blogger, no repositório ou nos logs.
- Testes provam permissões negativas e isolamento entre identidades.
- Nenhum estado de execução ou disponibilidade é simulado.

## Estado

Este documento estabelece a direção e os critérios de arquitetura. Não significa que os fluxos acima já estejam implementados ou testados. Não houve publicação, conexão de conta Blogger, configuração de credenciais, gasto pago ou alteração de conteúdo nos blogs.
