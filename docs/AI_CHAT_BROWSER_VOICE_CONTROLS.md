# Missão 09 — Controles de voz na sala

## Objetivo
Adicionar ditado com garantia explícita de processamento local quando o navegador oferecer esse contrato, e leitura em voz alta acionada pelo usuário. O chat por texto permanece independente dos recursos de voz.

## Implementação
- `web/voice-capabilities.js` detecta reconhecimento de voz e síntese disponíveis no navegador.
- Ditado só fica habilitado quando `SpeechRecognition.available({ langs: ["pt-BR"], processLocally: true })` confirma `available` (ou `true`) e a instância aceita `processLocally = true`.
- Não chama `install()`, não baixa pacotes, não faz fallback para reconhecimento remoto e não ativa microfone automaticamente.
- O navegador só inicia reconhecimento após clique explícito em **Ditado local**; o usuário pode parar.
- A transcrição final é inserida no campo de mensagem, mas não é enviada automaticamente.
- Leitura usa `speechSynthesis` / `SpeechSynthesisUtterance` do navegador e só começa após clique em **Ouvir mensagem** ou **Ler última mensagem**. Não há reprodução automática.
- Botão de parar interrompe leitura; mudança de página encerra recursos de voz.
- A página de salas recebe `/voice-capabilities.js` com `Cache-Control: no-store` e `X-Content-Type-Options: nosniff`.
- A lista de participantes foi materializada na tela para que a consulta de identidades tenha um destino DOM real.

## Segurança e privacidade
- Ditado exige confirmação de processamento local; se o navegador não fornecer o contrato, o recurso fica desabilitado e a mensagem explica por quê.
- Não há download ou instalação de pacote de idioma, nem reconhecimento remoto alternativo.
- O texto reconhecido permanece no campo de composição até o usuário decidir enviar.
- Síntese de voz depende do navegador/sistema operacional e das vozes disponíveis; o app não pode garantir que toda voz instalada seja offline. O usuário inicia a reprodução manualmente.
- O código não captura nem transmite áudio por endpoint do AI Bridge.
- Os controles de ditado não representam chamada ao vivo. WebRTC de grupo permanece fora do escopo.

## Testes automatizados
- `web/voice-capabilities.test.mjs`: detecção estrita de localidade, bloqueio quando pacote local não está disponível, configuração `processLocally`, transcrição final, parada, síntese e rejeição de entrada vazia.
- `server/test_http_e2e.py`: rota de entrega do módulo com cabeçalhos de cache e MIME.
- Workflow `AI Bridge Browser Voice UI Tests`: executa `node --test web/voice-capabilities.test.mjs`.

## Critérios de aceite
1. Texto continua funcional sem suporte de voz.
2. Ditado só é habilitado se o navegador confirmar processamento local em pt-BR.
3. Nenhum pacote é instalado/baixado automaticamente.
4. Microfone só é acionado por clique explícito.
5. Transcrição não é enviada sem ação do usuário.
6. Leitura não começa automaticamente e pode ser interrompida.
7. Falta de suporte é apresentada como limitação, não como falha do chat.
8. Não se declara chamada de voz ao vivo como implementada.

## Limitações não resolvidas
- Compatibilidade real varia por navegador e versão; a matriz precisa ser executada em Android Chrome e desktop.
- Não foi possível comprovar fisicamente que uma voz de síntese específica opera offline; a UI descreve dependência do navegador/sistema.
- Não houve teste com microfone físico ou permissão real neste ciclo.
- Não há conferência de áudio em tempo real entre duas IAs nem chamada em grupo.
- CI não substitui teste manual de navegador/dispositivo.
