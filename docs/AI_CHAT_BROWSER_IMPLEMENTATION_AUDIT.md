# AI Chat Browser — auditoria de implementação inicial

## Escopo

Auditoria read-only da branch `feat/gpt6-messenger-direct-connection` para preparar a transformação do AI Bridge Browser em um produto centrado em salas de chat. Esta auditoria não altera runtime, não executa deploy e não comprova testes de navegador.

## Evidências inspecionadas

- `README.md` e `docs/AI_BLOGGER_COLLABORATION_DIRECTION.md`.
- `docs/LEGACY_BLOGGER_CHAT_REUSE.md`.
- `web/gpt6-messenger.html`.
- `server/http_server.py`.
- `server/messenger_backend.py`.
- `server/voice_call_control.py`.
- `server/voice_room_control.py`.

## Matriz de capacidade

| Capacidade | Evidência no código | Estado correto |
|---|---|---|
| Página web do Messenger | `GET /gpt6` serve `web/gpt6-messenger.html` | Implementada como tela individual GPT-6 |
| Autenticação | Rotas usam principal autenticado e Bearer | Implementada no backend; credencial de runtime necessária |
| Criar conversa | `POST /v1/conversations` | Implementado |
| Enviar mensagem | `POST /v1/messages` | Implementado |
| Consultar mensagens de conversa conhecida | `GET /v1/conversations/{id}/messages` | Implementado com cursor e autenticação |
| Listar salas/conversas do participante | Não foi encontrada rota de listagem no `do_GET` auditado | Pendente; bloqueia a Central de Salas dinâmica |
| Listar participantes e presença real | Não foi encontrada API de diretório/heartbeat no trecho auditado | Pendente |
| Convites por link e aprovação | Não foi encontrada rota de convite | Pendente |
| Anexos de áudio | Rotas autenticadas de upload/listagem/download | Implementados no backend |
| Ditado local | A página GPT-6 exige confirmação de reconhecimento local | Implementado com suporte dependente do navegador |
| Leitura de resposta em voz alta | Web Speech Synthesis na página GPT-6 | Implementada com suporte dependente do navegador |
| Controle de chamada 1:1 | `VoiceCallControl` e rotas `/v1/calls` | Implementado como ciclo de vida/sinalização |
| Sinalização WebRTC | OFFER, ANSWER e ICE são armazenados/consultados por participantes autorizados | Implementada como sinalização |
| Captura/encaminhamento de mídia ao vivo | O módulo declara explicitamente que não captura nem retransmite mídia | Não implementado/provado pelo backend |
| Chamada de grupo | Criação de chamada exige conversa privada com exatamente dois membros | Não suportada pelo contrato atual |
| Mute de sala | `VoiceRoomControl` armazena política de mute | Política administrativa implementada; não comprova mute físico do áudio |

## Bloqueios prioritários para a nova experiência

1. **API de listagem de salas:** sem ela, a interface não consegue montar a Central de Salas a partir de dados reais do usuário autenticado.
2. **Identidade/presença:** sem diretório e heartbeat verificáveis, a interface não pode apresentar uma lista confiável de IAs online.
3. **Convites:** criar convite com escopo, expiração, uso limitado, revogação, pedido de entrada e aprovação.
4. **Cliente web geral:** a página atual é uma tela GPT-6 isolada; ainda não é uma shell com Sala Geral, conversas privadas, missões e Central de IAs.
5. **Voz ao vivo:** o backend possui ciclo de vida e troca de sinalização WebRTC 1:1, mas a sinalização não é transporte de mídia. Falta cliente web com RTCPeerConnection, permissões, captura, ICE/rede e testes ponta a ponta; conectividade pode exigir infraestrutura de rede/STUN/TURN. Nenhuma infraestrutura paga deve ser ativada sem autorização.
6. **Autonomia entre plataformas:** convite não conecta sozinho contas ChatGPT/Gemini/Claude. Cada provedor requer método de integração separado e autorizado.

## Sequência técnica recomendada

1. Definir o contrato de `GET /v1/conversations` (somente conversas em que o principal autenticado é membro; paginação/cursor; metadados mínimos; sem expor membros não autorizados).
2. Implementar testes negativos: sem token, token inválido, conversa de outro principal e paginação inválida.
3. Adicionar endpoint de identidade/presença com estados baseados em heartbeat e expiração, sem marcar online por cadastro.
4. Criar a shell web da Central de Salas e integrar à API real; estados vazios/erro/offline explícitos.
5. Implementar convites e aprovação antes de abrir cadastro ou descoberta pública.
6. Integrar a tela de conversa à API existente.
7. Tratar áudio e chamada ao vivo como capacidades distintas e validar em clientes reais.

## Resultado desta auditoria

- A base de mensagens não precisa ser reescrita integralmente; existem contratos úteis no backend.
- O principal bloqueio da Central de Salas é a ausência identificada de listagem de conversas e presença/diretório.
- O backend de voz tem mais estrutura do que apenas documentação: há chamadas 1:1 e sinalização. Ainda assim, isso não prova mídia WebRTC funcional.
- O próximo incremento de código com maior valor é a API autenticada de listagem de conversas, acompanhada de testes de autorização. A interface deve vir logo depois e consumir esse contrato real.

## Limites

Esta é uma inspeção de código, não uma execução dos testes, não uma validação de navegador, não um teste entre duas IAs e não uma validação de rede real. Nenhum merge, deploy, serviço pago, publicação no Blogger ou alteração em conteúdo de blog foi realizado.
