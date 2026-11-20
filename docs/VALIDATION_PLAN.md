# Plano de validação e critérios de aceite

## Ambiente alvo

Galaxy Tab A7 com Android 12 (API 31). A validação final exige dispositivo físico.

## Testes necessários

1. Importar o projeto no Android Studio compatível com AGP 9.5.
2. Sincronizar Gradle usando JDK 17 e Gradle 9.6.
3. Compilar variante debug.
4. Instalar apenas após autorização do usuário.
5. Abrir ChatGPT e concluir login manual.
6. Criar duas abas e confirmar navegação/histórico independente.
7. Verificar comportamento de cookies: as abas compartilham o perfil padrão neste protótipo.
8. Confirmar que solicitações de microfone/câmera são negadas.
9. Prototipar AudioPlaybackCapture em app de teste com consentimento MediaProjection.
10. Validar elegibilidade de captura do áudio do ChatGPT Web.
11. Validar uma rota de entrada de áudio autorizada para a segunda sessão.
12. Testar latência, eco, interrupção, reconexão, consumo de memória e bateria.

## Resultado até o momento

- Arquivos-base do projeto: criados no GitHub.
- Navegador com abas: código inicial criado, ainda não compilado.
- Sessões independentes de conta: BLOCKED; cookies são compartilhados no perfil padrão.
- Central de áudio: somente indicador visual.
- Captura e retransmissão: BLOCKED.
- Conferência bidirecional: BLOCKED.
- Teste no tablet: não realizado.
