# Extração do legado Blogger Chat para o AI Messenger

## Objetivo

Reaproveitar a interface e os fluxos genéricos do arquivo legado `Blogger Chat.txt`, sem transportar regras religiosas, credenciais inseguras, dados fictícios ou armazenamento local para a nova aplicação.

Este documento registra uma auditoria estática do arquivo de 2.314 linhas e o mapeamento para o AI Bridge Browser. Não afirma que o aplicativo legado esteja pronto para produção.

## Rodadas de trabalho

### 01/10 — Inventário do arquivo

O arquivo é uma aplicação HTML única, com CSS e JavaScript embutidos. A interface é mobile-first, limitada a 500 px, com cabeçalho, conteúdo principal, navegação inferior e telas de login, salas, conversa e perfil.

### 02/10 — Interface que vale preservar

- Layout responsivo e foco em celular.
- Cabeçalho com identidade do usuário.
- Cartões de salas e indicação de tipo de conversa.
- Tela de conversa com balões, remetente, horário e rolagem automática.
- Barra de emojis e campo de composição.
- Navegação inferior.
- Estrutura visual de perfil com avatar, capa e biografia.

Preservar a ideia e a hierarquia visual; não copiar literalmente o tema antigo.

### 03/10 — Funcionalidades que podem ser reaproveitadas

- Separação entre lista de salas e conversa aberta.
- Mensagens de texto com remetente, conteúdo e horário.
- Seleção de mídia como conceito de interface.
- Perfil básico.
- Indicador de presença, desde que calculado pelo servidor.
- Separação entre sala somente texto e sala com mídia, se essa política continuar necessária.

### 04/10 — Conteúdo a remover

Remover integralmente:
- Umbanda, Quimbanda, Candomblé e qualquer seletor/campo de religião.
- Orixás, cargos religiosos, mascotes, saudações e emojis temáticos.
- Nomes, e-mails, senhas e conversas de demonstração ligados ao app antigo.
- Eventos fictícios e locais religiosos de exemplo.
- Anúncios de vídeo e fluxo obrigatório de publicidade do app antigo.
- Identidade visual, título e textos que contenham “BATE-PAPO AXÉ”.

Estado e cidade podem ser opcionais no perfil no futuro, mas não devem filtrar nem limitar o acesso às salas por padrão.

### 05/10 — Bloqueios críticos de autenticação

O legado contém senha de administrador fixa no JavaScript, credenciais de demonstração visíveis na tela e autenticação feita comparando senha em um objeto JavaScript. Isso não é autenticação segura.

A nova aplicação deve:
- Nunca embutir senhas administrativas ou credenciais padrão no HTML/JavaScript.
- Não armazenar senhas em `localStorage`.
- Validar identidade, sessão, permissões e administração no servidor.
- Não confiar em `isAdmin` ou em qualquer papel enviado pelo navegador.
- Usar HTTPS e tokens de curta duração quando aplicável.

Os scripts Firebase carregados no HTML não comprovam uma integração Firebase ativa: o próprio código diz que é necessário configurar o Firebase e usa `localStorage` como caminho de teste.

### 06/10 — Bloqueios de armazenamento e mídia

O legado persiste usuários e mensagens em `localStorage`, e converte imagens/vídeos em Base64 antes de guardá-los no navegador. Isso cria dados isolados por navegador, limita armazenamento e não sincroniza celulares diferentes.

Na nova aplicação:
- Mensagens devem ser persistidas pelo servidor.
- Anexos devem ir para armazenamento de objetos, com metadados e autorização no servidor.
- O navegador não deve guardar cópias Base64 de mídia como banco de dados.
- Limites de tamanho, MIME real, expiração, acesso e remoção devem ser aplicados no servidor.
- A interface deve mostrar falhas de envio e estados de entrega sem simular sucesso.

### 07/10 — Dados fictícios e comportamento que não pode migrar

O legado cria usuários padrão, contagens de membros aproximadas, usuários online calculados sobre dados locais e respostas automáticas fictícias como “Pai Roberto” e “Maria de Iemanjá”. Também contém eventos e anúncios de exemplo.

Esses elementos devem ser removidos. A nova interface só pode exibir presença, membros, mensagens, eventos ou anúncios quando vierem de fonte real e autorizada. Não apresentar respostas simuladas como se fossem outros usuários.

### 08/10 — Integração com o AI Bridge existente

O branch `feat/gpt6-messenger-direct-connection` já possui:
- Página web `/gpt6`.
- Endpoint autenticado `GET /v1/gpt6/status`.
- Endpoint autenticado `POST /v1/gpt6/respond`.
- Endpoint de preparação de segredo efêmero para Realtime.
- API de conversas `POST /v1/conversations`.
- API de envio `POST /v1/messages`.
- Leitura paginada de mensagens `GET /v1/conversations/{conversationId}/messages?after={sequence}&limit={n}`.

A interface web atual usa a conversa direta com GPT-6. O envio/recebimento de mensagens de grupo usa a API de conversas e mensagens, mas a experiência de grupo exige seleção/gestão de membros e consumidores ativos para os participantes de IA. Não presumir que um GPT-6 worker já consome automaticamente mensagens enfileiradas de grupos.

O backend atual configura duas identidades/tokens de IA. Isso é um ambiente controlado de protótipo, não um sistema público de cadastro multiusuário. Não compartilhar um token comum entre usuários finais como se fosse autenticação individual.

### 09/10 — Blogger: forma de incorporação

A forma mais segura de começar é hospedar a aplicação no servidor HTTPS do AI Bridge e incorporar a página por iframe no Blogger. A chave da OpenAI permanece no servidor e nunca aparece no HTML do Blogger.

Antes de habilitar o iframe:
- Definir o domínio Blogger exato que poderá incorporar a aplicação.
- Configurar CSP `frame-ancestors` com a origem autorizada, em vez de liberar qualquer site.
- Garantir que tokens de sessão não sejam publicados em posts, gadgets, tema ou código-fonte.
- Testar login, renovação/expiração de sessão e logout em celular.
- Considerar que o plano gratuito do host pode suspender/hibernar o serviço.

### 10/10 — Sequência de migração e critérios de aceite

1. Criar uma nova interface genérica, mantendo a composição visual mobile-first.
2. Implementar primeiro a conversa direta autenticada com GPT-6, sem chave no cliente.
3. Ligar a tela de conversas humanas/IA às APIs reais do AI Bridge, após definir identidades e permissões.
4. Implementar autenticação individual de pessoas antes de abrir cadastro público.
5. Implementar upload de mídia com armazenamento remoto seguro.
6. Adicionar perfis e presença somente quando houver API real.
7. Incorporar no Blogger após definir origem permitida no CSP.
8. Validar em dois navegadores/dispositivos distintos que mensagens realmente sincronizam.
9. Testar autorização negativa, token expirado, membro não autorizado e limite de requisição.
10. Só então considerar a versão pronta para usuários externos.

## Decisão técnica

**Reaproveitar o design e os padrões de interação; não reaproveitar o mecanismo de autenticação, armazenamento, mídia, administração ou dados de demonstração.**

O arquivo legado é uma referência de interface. O AI Bridge deve continuar sendo a autoridade de autenticação, autorização, persistência e comunicação entre IAs.

## Estado desta entrega

- Auditoria estática do arquivo legado: concluída.
- Extração dos componentes úteis e itens a descartar: documentada.
- Alteração do HTML legado original: não realizada.
- Nova interface geral integrada a salas compartilhadas: ainda não implementada.
- Autenticação individual pública: não implementada.
- Publicação no Render ou incorporação no Blogger: não realizada.
- Teste ponta a ponta entre dois dispositivos: não realizado.
- Nenhum segredo/API key foi configurado e nenhuma ativação paga foi executada.
