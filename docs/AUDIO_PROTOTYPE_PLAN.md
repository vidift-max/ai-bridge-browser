# Plano de protótipo de áudio — etapa seguinte

## Objetivo

Descobrir por experimento se o áudio de reprodução de uma página ChatGPT Web pode ser capturado com APIs públicas do Android 12 e qual alternativa autorizada existe para fornecer áudio ao segundo participante.

## Fase A — captura de reprodução

1. Criar aplicativo/probe de diagnóstico separado do navegador.
2. Solicitar RECORD_AUDIO em contexto claro.
3. Solicitar MediaProjection com confirmação explícita do usuário.
4. Criar AudioPlaybackCaptureConfiguration apenas para usos elegíveis (MEDIA/GAME/UNKNOWN).
5. Registrar somente metadados de teste: sucesso, formato, taxa, tamanho do buffer e erros.
6. Testar primeiro com app de áudio de demonstração controlado.
7. Testar ChatGPT Web somente se o sistema indicar que a fonte é elegível.

## Fase B — entrada de áudio

Não presumir que o áudio capturado pode ser injetado no microfone de um WebView. Investigar apenas interfaces documentadas e consentidas, incluindo uma aplicação de conferência própria com WebRTC ou entrada de áudio oficialmente suportada pelo cliente.

## Segurança

- Sem captura silenciosa.
- Sem contornar proteções de áudio do Android ou do site.
- Sem iniciar projeção automaticamente.
- Encerrar captura quando o usuário parar ou o sistema revogar a projeção.
- Sem gravação permanente no protótipo.

## Critério de PASS

Uma sessão envia áudio autorizado e a outra recebe e responde, com teste repetível, baixa realimentação e botão de interrupção. Até lá, áudio bidirecional permanece BLOCKED.
