# Central de áudio — estudo de viabilidade

## Estado atual: BLOCKED para áudio bidirecional automático

A interface visual de status foi adicionada ao navegador. Ela não captura nem transmite áudio.

## Captura de áudio de reprodução

Android oferece AudioPlaybackCapture a partir do Android 10 (API 29). O fluxo exige permissão RECORD_AUDIO e consentimento explícito do usuário via MediaProjection. A captura depende também do uso de áudio e da política de captura definida pelo aplicativo de origem. Áudio classificado como comunicação por voz pode estar sujeito a restrições e não deve ser presumido capturável.

## Encaminhamento para o microfone de outra aba

Capturar áudio de saída e alimentar esse áudio como entrada de microfone de outro WebView são capacidades distintas. O Android não oferece uma API pública genérica para substituir o microfone de uma página por um fluxo PCM arbitrário. A permissão de microfone concedida ao WebView não resolve essa injeção.

## Estratégia de prototipagem

1. Criar um protótipo separado de AudioPlaybackCapture com consentimento MediaProjection.
2. Testar captura de áudio de um app de origem controlado e registrar formato, taxa de amostragem e interrupções.
3. Verificar se o áudio real do ChatGPT Web é elegível à captura; resultado desconhecido até teste físico.
4. Investigar uma ponte de áudio por WebRTC/servidor ou entrada de áudio suportada oficialmente pelo cliente, sem contornar controles do Android.
5. Só depois desenhar roteamento entre participantes e prevenção de eco/realimentação.

## Critério de aprovação

Só marcar PASS quando duas sessões reais conseguirem ouvir e responder uma à outra em teste reproduzível, com autorização explícita, sem depender de suposições sobre o áudio interno do sistema.
