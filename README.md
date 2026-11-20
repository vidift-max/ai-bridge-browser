# AI Bridge Browser

Navegador Android experimental com abas WebView e uma futura central de áudio para conversas entre sessões de IA.

## Estado atual

O scaffold Android foi publicado na branch `v2-saas-alpha`. O navegador inicial permite criar até cinco abas WebView e navegar até o ChatGPT. Foi adicionada uma indicação visual da central de áudio, mas **não existe captura ou retransmissão de áudio implementada**.

**Ainda não está pronto para instalação:** o projeto não foi compilado nem testado em um dispositivo Android nesta execução.

## Tecnologia

- Java 17
- Android Gradle Plugin 9.5.0
- Gradle 9.6.0
- compileSdk 37 / targetSdk 35 / minSdk 29
- Android WebView

## Limitações importantes

- Abas distintas não significam contas isoladas: as WebViews compartilham o perfil padrão de cookies neste protótipo.
- Permissões de microfone e câmera são negadas por padrão.
- AudioPlaybackCapture exige consentimento MediaProjection e depende da política de captura do app de origem.
- Não há API pública genérica para injetar um fluxo de áudio arbitrário como microfone de outro WebView.
- A comunicação bidirecional entre duas IAs permanece BLOCKED até existir um protótipo comprovado em dispositivo real.

## Estrutura

- `app/`: aplicativo Android.
- `docs/ARCHITECTURE.md`: arquitetura e limites.
- `docs/AUDIO_BRIDGE.md`: viabilidade da ponte de áudio.
- `docs/CONFERENCE_PROTOCOL.md`: regras planejadas da conferência.
- `docs/VALIDATION_PLAN.md`: testes necessários.
- `docs/ROUND_REPORT.md`: relatório das dez rodadas.

## Build

Com JDK 17, Android SDK API 37 e Gradle 9.6 instalados:

```bash
gradle :app:assembleDebug
```

Também foi configurado um workflow GitHub Actions para executar o build de debug em pushes e pull requests para `v2-saas-alpha`.

## Plano de desenvolvimento

As dez rodadas iniciais de planejamento e preparação estão registradas em `docs/ROUND_REPORT.md`. As próximas tarefas técnicas são: obter um build verde, testar as abas no Galaxy Tab A7, resolver isolamento real de sessões e prototipar captura/encaminhamento de áudio com consentimento explícito.
