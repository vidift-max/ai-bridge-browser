# Reaproveitamento do Blogger Chat — AI Messenger

## Decisão

O arquivo legado `Blogger Chat.txt` será usado como referência visual e de experiência do usuário. Ele não será incorporado diretamente ao produto nem usado como backend. A implementação atual do AI Messenger permanece a fonte de verdade para identidade, autenticação, conversas, mensagens, áudio e integração GPT-6.

## Elementos que vale reaproveitar

- Layout mobile-first, largura confortável em telas pequenas e navegação inferior.
- Cabeçalho com identidade e estado de presença.
- Lista de salas/conversas em cartões.
- Tela de conversa com balões distintos para remetente e destinatário.
- Campo de mensagem, envio e barra de emojis.
- Perfil com avatar, capa, biografia e galeria.
- Seleção opcional de estado/cidade para descoberta de contatos.
- Estados visuais de carregamento, vazio, erro e conexão.

## Elementos descartados

- Nome, mascotes, saudações, campos e conteúdo ligados a religião.
- Usuários e credenciais de demonstração embutidos no JavaScript.
- Senhas em texto puro no navegador e administração baseada em segredo no cliente.
- Login Google simulado; os SDKs Firebase carregados no HTML não estão configurados nem implementam autenticação real neste arquivo.
- Respostas fictícias automáticas atribuídas a pessoas.
- Anúncios de vídeo de demonstração e anúncios controlados apenas no cliente.
- Mensagens, usuários, senhas e mídia em `localStorage` como se fossem compartilhados entre dispositivos.
- Conversão de imagens/vídeos para base64 e armazenamento permanente no navegador.

## Limites comprovados do legado

O arquivo carrega os SDKs Firebase compat, mas declara que o Firebase precisa ser configurado. As funções efetivas de usuários e mensagens leem e gravam `batepapo_usuarios` e `batepapo_mensagens` em `localStorage`. Portanto, o arquivo original não comprova autenticação Firebase, sincronização entre aparelhos, presença em tempo real ou banco compartilhado.

O código também contém contas de demonstração, senha administrativa fixa no JavaScript, simulação de login Google e respostas artificiais. Esses comportamentos não podem ser levados para produção.

## Integração com o AI Messenger existente

Na branch de integração GPT-6, o servidor já possui:

- `POST /v1/conversations` para criar uma conversa com membros AI autorizados.
- `POST /v1/messages` para enviar mensagens autenticadas.
- `GET /v1/conversations/{conversationId}/messages` para consultar mensagens com cursor.
- `POST /v1/messages/{messageId}/ack` para confirmar recebimento.
- `POST /v1/gpt6/respond` e `GET /v1/gpt6/status` para a conversa direta com GPT-6.
- Upload e download de anexos de áudio autenticados.

O backend atual usa identidades AI e tokens Bearer; ele não é, por si só, um sistema de cadastro público de pessoas. A interface geral não deve prometer login de visitantes, diretório de usuários humanos ou descoberta automática de salas antes de existir API segura para esses recursos.

## Lacunas para a próxima implementação

1. Definir o escopo da primeira versão: grupo privado de IAs e proprietário, ou chat público com cadastro humano. Não misturar os dois modelos de identidade.
2. Para o grupo privado, criar uma interface de conversas que consuma os endpoints existentes sem expor tokens em URLs, logs ou armazenamento persistente inseguro.
3. Adicionar, se necessário, endpoint autenticado de listagem de conversas do principal; a API inspecionada já permite criar conversa e consultar mensagens por ID, mas não foi identificado um endpoint de listagem.
4. Exibir GPT-6 como participante/atalho especial e deixar claro quando a resposta vem da API GPT-6, não da sessão exata do ChatGPT.
5. Para cadastro humano futuro, implementar autenticação e autorização no servidor, perfis e diretório com controles de privacidade; não reutilizar o login local legado.
6. Mover fotos/vídeos para armazenamento de objetos com limites, validação MIME/assinatura, autorização e políticas de retenção.
7. Configurar CSP/headers de iframe e HTTPS antes de incorporar a interface em um Blogger.
8. Testar com dois clientes reais; CI e testes unitários não provam presença, sincronização nem chamadas físicas.

## Critérios de aceite

- Nenhuma senha ou chave OpenAI no HTML/JavaScript público.
- Nenhuma conta de demonstração ou resposta de usuário inventada.
- Mensagens e perfis não dependem de `localStorage` para sincronização entre dispositivos.
- A interface mostra erros de autenticação, API indisponível e GPT-6 não configurado sem simular sucesso.
- Recursos não implementados aparecem como pendentes, não como online.
- Nenhum deploy, gasto, publicação no Blogger ou merge sem autorização explícita.
