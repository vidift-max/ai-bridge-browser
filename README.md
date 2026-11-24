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
- `docs/AI_CHAT_BROWSER_IMPLEMENTATION_AUDIT.md`: auditoria do backend e lacunas para a Central de Salas, convites e voz.
- `docs/AI_CHAT_BROWSER_WEB_INVITES.md`: implementação atual dos convites web, endpoints, segurança e limitações.
- `docs/AI_CHAT_BROWSER_VOICE_CONTROLS.md`: ditado local condicionado ao suporte explícito do navegador, leitura em voz alta e limites de privacidade.
- `docs/AI_CHAT_BROWSER_WEBRTC_PRIVATE_CALLS.md`: chamadas WebRTC privadas 1:1, fluxo de sinalização, permissões e limitações de rede.
- `docs/AI_CHAT_BROWSER_WEBRTC_RELIABILITY.md`: diagnóstico ICE, configuração RTC, tolerância a desconexões e critérios de validação física.
- `docs/AI_CHAT_BROWSER_REMOTE_CONTROL_CONTINUITY.md`: permissões temporárias, controle remoto limitado, heartbeat, recuperação supervisionada e auditoria.
- `docs/AI_CHAT_BROWSER_SESSION_ADAPTER.md`: contrato de adaptadores de sessão, consentimento explícito, allowlist de origem HTTPS e limites de integração com abas de IA.
- `docs/AI_MESSENGER_GROUP_INVITES.md`: fluxo existente de convite Android/Firebase e limites de provisionamento.
- `docs/AI_BLOGGER_COLLABORATION_DIRECTION.md`: direção de colaboração multi-IA e integração editorial.
- `docs/LEGACY_BLOGGER_CHAT_REUSE.md`: elementos do chat legado que podem ser reaproveitados e limites de segurança.
- `docs/ARCHITECTURE.md`: arquitetura técnica anterior e limitações conhecidas.
- `docs/BROWSER_TEST_MATRIX.md`: matriz de testes do navegador.
- `docs/SESSION_ISOLATION.md`: requisitos de isolamento de sessão.
- `docs/WEBVIEW_SECURITY.md`: baseline de segurança WebView.

## Estado de implementação

A especificação de produto registra a direção desejada; não significa que toda a experiência esteja implementada. O backend possui partes de identidade, conversas, mensagens e anexos de áudio, além de controle de chamadas 1:1 e sinalização WebRTC. A sinalização não transporta mídia: a chamada web ao vivo ainda não está comprovada. A Central de Salas e a listagem autenticada de conversas já têm uma primeira implementação no branch de trabalho. Convites web, presença/diretório de identidades, controles de voz e integração WebRTC 1:1 em conversas privadas estão em branches de trabalho. A Missão 10 passou pelo CI; o teste real entre dispositivos permanece pendente. A Missão 11 adiciona diagnóstico ICE e tolerância a desconexões, ainda sujeita ao CI e à validação física. A Missão 12 adiciona um núcleo de controle remoto limitado por permissões e supervisor de continuidade; os testes automatizados passaram, mas a integração com adaptador real ainda não foi feita. Chamadas em grupo e conectividade entre redes distintas não estão comprovadas.

Não confundir build/CI com funcionamento entre IAs reais. Nenhum merge, deploy, gasto pago ou publicação no Blogger é autorizado por esta documentação.
