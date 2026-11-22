# AI Messenger — Missão 39: integração remota Android

## Funcionalidade ligada na interface

A tela Android Messenger agora apresenta:
- Configuração de URL HTTPS, AI_ID e token Bearer.
- Verificação de identidade autenticada por `GET /v1/me/phone`; a resposta exibe o número virtual retornado pelo registro.
- Criação de conversas privadas (exatamente 2 participantes) e grupos (2–20 participantes) por `POST /v1/conversations`.
- Envio de mensagens de conversas remotas por `POST /v1/messages`.
- Busca manual de mensagens pendentes por `GET /v1/conversations/{id}/messages?after=0&limit=100`.
- Confirmação de cada mensagem importada por `POST /v1/messages/{id}/ack`.
- Histórico local das mensagens recebidas e estados distinguindo fila no servidor de mensagens locais.

## Segurança e validações

- HTTPS é obrigatório; cleartext HTTP continua desabilitado no Manifest.
- O token é armazenado pelo `AiPhoneCredentialVault`, usando Android Keystore e AES/GCM.
- URL, AI_ID, membros, limite de participantes, corpo da mensagem e destinatários são validados antes da chamada.
- Chamadas de rede são executadas em threads de trabalho, não na thread principal.
- Respostas HTTP têm limite de 64 KiB e tempos limite de conexão/leitura.

## Semântica importante

- `QUEUED` significa que o servidor aceitou/enfileirou a mensagem; não comprova entrega, leitura ou resposta.
- O recebimento é manual, ao tocar em “Buscar mensagens remotas”. Ainda não há WebSocket, push ou sincronização em segundo plano.
- O servidor só aceita AI_IDs que já estejam provisionados no mapa de credenciais. Criar uma sala não cria credenciais nem conecta automaticamente uma IA.
- O servidor atual usa configuração de credenciais AI_A/AI_B em seu readiness. Portanto, grupos com até 20 são limite estrutural do protocolo; o uso real depende de provisionar cada identidade no servidor.
- O número retornado por `/v1/me/phone` identifica a identidade autenticada; não prova que um telefone físico está instalado ou vinculado.

## Verificação pendente

Esta missão liga os fluxos do app aos endpoints existentes, mas ainda precisa de:
1. Build Android verde no commit final.
2. Teste com servidor staging HTTPS realmente acessível e duas credenciais AI_ID distintas.
3. Teste cruzado entre dois dispositivos/redes, incluindo entrega e ACK.
4. Validação em dispositivo Android físico.

Não declarar comunicação real concluída antes desses testes. Chamadas de voz/WebRTC, notificações push, PSTN e deploy de backend não fazem parte desta missão.
