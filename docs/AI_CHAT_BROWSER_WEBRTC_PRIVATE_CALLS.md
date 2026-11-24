# Missão 10 — Chamadas WebRTC privadas 1:1

## Objetivo
Conectar a sinalização de chamadas 1:1 já existente ao navegador, com captura de microfone iniciada somente por ação explícita do usuário. Esta missão não implementa chamadas em grupo.

## Escopo implementado
- Chamadas disponíveis apenas em conversas `PRIVATE` com exatamente duas identidades autorizadas.
- A interface de salas exibe **Ligar** e **Encerrar chamada** somente em conversas privadas elegíveis.
- O participante chamado recebe uma confirmação antes de aceitar; aceitar solicita permissão de microfone.
- O módulo `web/webrtc-call.js` cria `RTCPeerConnection`, obtém áudio via `getUserMedia({audio:true, video:false})`, envia tracks locais e recebe tracks remotas.
- O fluxo de sinalização respeita o ciclo: `RINGING` → `ACCEPTED` → `CONNECTING` → `CONNECTED` (quando o navegador reportar conexão).
- O chamador só cria/envia SDP OFFER depois de o backend confirmar `ACCEPTED`; o chamado processa OFFER e responde com ANSWER.
- Candidatos ICE são enviados pela API autenticada e consumidos pelo outro participante com cursor incremental.
- Encerrar, cancelar, rejeitar, timeout ou término remoto fecham a conexão local e param as tracks de microfone.
- Falha ao obter microfone ou preparar a conexão fecha tracks e, no lado chamado, tenta rejeitar a chamada.
- A UI permite ouvir o áudio remoto por elemento `<audio>`.

## Privacidade e segurança
- Requer contexto seguro do navegador (HTTPS/localhost); caso contrário, o navegador bloqueia a preparação da chamada.
- O microfone só é solicitado depois do clique em **Ligar** ou da confirmação explícita de aceitar uma chamada.
- O backend transporta somente metadados de sinalização (SDP/ICE); não recebe nem armazena o fluxo de áudio.
- Os sinais SDP/ICE são removidos do SQLite quando a chamada termina, é rejeitada, cancelada ou expira.
- Endpoints permanecem autenticados e restritos aos participantes da chamada.
- Nenhuma chamada telefônica, número de operadora ou infraestrutura paga foi adicionada.

## Limitações conhecidas
- **Não há TURN nem configuração STUN nesta versão.** A conexão direta pode funcionar em redes locais ou rotas que permitam ICE host candidates, mas conexões entre redes distintas/NATs não são garantidas. Não afirmar comunicação pela internet até teste real e infraestrutura ICE apropriada.
- Ainda não houve teste de microfone físico, alto-falante, dois dispositivos ou navegadores Android/desktop.
- Testes automatizados usam objetos simulados; não provam mídia real, conectividade ICE ou qualidade de áudio.
- Chamadas em grupo não estão implementadas. O backend atual limita chamadas a dois membros de conversa privada.
- A chamada não é uma conexão automática com contas externas ChatGPT/Gemini/Claude; depende de identidades provisionadas e autenticadas no AI Bridge.

## Testes
- `web/webrtc-call.test.mjs`: permissão sob ação explícita, cancelamento, lookup de chamada recebida, oferta após aceite, troca OFFER/ANSWER e encerramento.
- `server/test_voice_call_control.py`: política de participantes, transições, sinalização e remoção de metadados no encerramento.
- Workflows backend, validação direta, Android e WebRTC UI executam no branch da missão.
