# Missão 11 — Confiabilidade e diagnóstico WebRTC 1:1

## Objetivo
Melhorar a observabilidade e a recuperação de chamadas privadas 1:1 sem declarar conectividade real que ainda não foi testada. Não inclui chamadas em grupo, relay de mídia próprio ou ativação de serviços pagos.

## Rodadas executadas
1. Reauditado o fluxo WebRTC da Missão 10, os pontos de criação de RTCPeerConnection, os eventos ICE e a UI de salas.
2. Criado branch isolado a partir do HEAD validado da Missão 10.
3. Confirmado e exposto o ponto de configuração RTC por `rtcConfiguration`, mantendo compatibilidade com a configuração vazia atual.
4. Adicionado callback estruturado `onDiagnostic` para estados de ICE, gathering e peer connection.
5. Adicionado diagnóstico de erros de coleta ICE sem registrar SDP, credenciais ou candidatos completos.
6. Implementada tolerância temporária a estado ICE `disconnected`, com janela configurável de recuperação (padrão: 8 segundos).
7. Implementado tratamento explícito de ICE `failed` e `closed`, com limpeza do timer de recuperação.
8. Protegido o registro de conexão no backend contra chamadas duplicadas do evento `connectionstatechange`.
9. Acrescentados testes simulados para passagem de configuração RTC, diagnóstico sem SDP e período de recuperação ICE.
10. Ligada a configuração RTC e mensagens diagnósticas à UI, documentadas as limitações e aberta validação CI pelo PR da missão.

## Configuração ICE
A página aceita uma configuração fornecida pelo bootstrap confiável como `window.AIBridgeRtcConfiguration`; a UI a encaminha ao cliente WebRTC. Sem essa configuração, o navegador usa a configuração vazia atual e conexões podem falhar em NATs/rede restritiva.

Exemplo ilustrativo de configuração pública:
```js
window.AIBridgeRtcConfiguration = {
  iceServers: [{ urls: ["stun:stun.example.net:3478"] }]
};
```

Não inserir credenciais TURN permanentes no repositório, HTML estático, logs ou histórico. TURN exige credenciais temporárias emitidas por serviço autorizado e aprovado. Esta missão não cria conta, servidor, chave, gasto ou infraestrutura TURN/STUN gerenciada.

## Privacidade e segurança
- Diagnósticos registram apenas nomes de eventos e estados e código de erro ICE; não incluem SDP, texto livre de erro nem objeto de candidato.
- A configuração ICE é fornecida ao navegador e, por definição, pode ser inspecionada pelo cliente. Credenciais TURN, quando adotadas, devem ter curta validade e escopo restrito.
- Microfone continua dependendo de ação explícita e contexto seguro.
- A mídia continua peer-to-peer; o backend transporta apenas sinalização.
- Nenhum merge, deploy, publicação ou serviço pago foi realizado.

## Critérios de validação e limites
- CI automatizado deve validar o controlador WebRTC, backend e builds Android.
- Testes simulados não comprovam microfone, alto-falante, qualidade, NAT traversal ou conectividade entre dispositivos.
- Ainda é obrigatório testar dois dispositivos reais em uma mesma rede e em redes diferentes, com permissões de microfone explícitas.
- Sem STUN/TURN efetivamente provisionado e testado, conectividade entre redes diferentes não pode ser prometida.
- Chamadas em grupo permanecem fora do escopo.

## Estado
Implementação e testes automatizados sujeitos ao resultado do CI do PR #9. Validação física permanece PENDENTE até evidência de chamada real entre dois dispositivos.
