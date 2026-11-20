# Protocolo planejado da conferência

Este documento define regras de produto; não representa uma implementação de áudio.

## Participantes iniciais

- Host humano: controla a sessão.
- AI-01: primeira sessão de IA.
- AI-02: segunda sessão de IA.

## Estados previstos

- DISCONNECTED
- CONNECTING
- LISTENING
- SPEAKING
- MUTED
- ERROR

## Regras

- Microfone e transmissão devem começar desligados.
- O host autoriza explicitamente a entrada de cada participante.
- Cada participante pode ser silenciado individualmente.
- Um único participante fala por vez no modo inicial, para reduzir eco e sobreposição.
- O host pode interromper a fala e encerrar a conferência.
- Mudanças de estado devem ser registradas localmente para diagnóstico.
- Nenhuma IA pode conceder permissões a si própria ou iniciar captura sem consentimento do usuário.

## Não implementado

Não existe ainda transporte de áudio, detecção de fala, mixer, supressão de eco, sinalização WebRTC ou serviço de conferência.
