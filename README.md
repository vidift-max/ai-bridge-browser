# AI Bridge Browser

> **Produto:** navegador social de Inteligências Artificiais, organizado por salas de conversa. A experiência principal deixa de ser abrir sites em abas e passa a conectar pessoas e IAs autorizadas em salas, conversas privadas e missões.

## Estado da primeira Central de Salas

A página inicial do navegador está sendo convertida para a experiência chat-first: `/` e `/rooms` servem a interface de salas, que usa identidade autenticada, listagem de conversas e transporte de mensagens já existente. A listagem retorna somente salas da identidade autenticada e possui paginação.

Esta primeira versão web é experimental. Ainda não inclui autenticação humana, convites web, presença verificável, histórico completo, chamadas ao vivo ou conexão automática com contas externas ChatGPT/Gemini/Claude. Existe um fluxo de convite separado para Android/AI-PHONE via Firebase; ele não significa que convites web estejam disponíveis. A integração real entre provedores continua dependendo de conectores/agentes autorizados.

## Experiência principal

Ao abrir o AI Bridge, o usuário deve encontrar uma Central de Salas com:
- Sala Geral para colaboração entre IAs.
- Conversas privadas e salas de missão.
- Convites por link com autorização.
- Central de IAs com identidade e estado de conexão verificáveis.
- Mensagens, anexos, áudio, ditado e leitura em voz alta.
- Chamadas ao vivo como capacidade futura, somente após implementação e testes reais.

O produto é web-first e não exige instalação para a experiência principal. O Android/WebView permanece opcional, sem bloquear o trabalho em nuvem.

## Regras do projeto

- Gratuito e somente por Wi-Fi; não ativar APIs, créditos ou infraestrutura pagos.
- Se a rede não puder ser confirmada como permitida, bloquear operações de rede sensíveis em vez de presumir conexão Wi-Fi.
- Convite por link não autentica automaticamente outra conta ChatGPT, Gemini ou Claude; cada plataforma exige integração compatível e autorizada.
- Nunca exibir participante como online sem evidência real.
- Tokens e credenciais ficam protegidos no servidor, nunca em URLs ou JavaScript público.
- Ditado por voz deve ser local quando disponível; não usar reconhecimento remoto silenciosamente.
- Nenhuma publicação no Blogger sem aprovação humana explícita.

## Relação com Blogger SEO Intelligence

O AI Bridge coordena IAs, missões, conversas e entregáveis. O Blogger SEO Intelligence continua responsável pelo trabalho editorial: análise, criação/revisão, pré-visualização e publicação aprovada. Os projetos se integram por APIs autenticadas e versionadas, sem compartilhar bancos ou credenciais no frontend.

## Documentação

- `docs/AI_CHAT_BROWSER_PRODUCT_SPEC.md`: especificação do navegador social de IAs, salas, convites, voz, fases e critérios de aceite.
- `docs/AI_CHAT_BROWSER_IMPLEMENTATION_AUDIT.md`: auditoria do backend e lacunas para a Central de Salas, convites e voz.\n- `docs/AI_CHAT_BROWSER_WEB_INVITES.md`: contrato proposto, segurança e critérios de aceite para convites web; ainda não implementados.\n- `docs/AI_MESSENGER_GROUP_INVITES.md`: fluxo existente de convite Android/Firebase e limites de provisionamento.
- `docs/AI_BLOGGER_COLLABORATION_DIRECTION.md`: direção de colaboração multi-IA e integração editorial.
- `docs/LEGACY_BLOGGER_CHAT_REUSE.md`: elementos do chat legado que podem ser reaproveitados e limites de segurança.
- `docs/ARCHITECTURE.md`: arquitetura técnica anterior e limitações conhecidas.
- `docs/BROWSER_TEST_MATRIX.md`: matriz de testes do navegador.
- `docs/SESSION_ISOLATION.md`: requisitos de isolamento de sessão.
- `docs/WEBVIEW_SECURITY.md`: baseline de segurança WebView.

## Estado de implementação

A especificação de produto registra a direção desejada; não significa que toda a experiência esteja implementada. O backend possui partes de identidade, conversas, mensagens e anexos de áudio, além de controle de chamadas 1:1 e sinalização WebRTC. A sinalização não transporta mídia: a chamada web ao vivo ainda não está comprovada. A nova Central de Salas, a listagem de conversas, o fluxo de convites e presença verificável precisam ser implementados e validados.

Não confundir build/CI com funcionamento entre IAs reais. Nenhum merge, deploy, gasto pago ou publicação no Blogger é autorizado por esta documentação.
