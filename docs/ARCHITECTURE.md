# Arquitetura inicial

## Objetivo

Aplicativo Android nativo que hospeda páginas em WebViews independentes por aba e, em etapa posterior, uma central de áudio experimental.

## Base técnica

- Android nativo com Java.
- Android Gradle Plugin 9.5.0; Gradle 9.6.0; JDK 17.
- compileSdk 37, targetSdk 35, minSdk 29.
- WebView do sistema Android.
- Sem servidor próprio, sem coleta de credenciais e sem automação de publicação.

## Abas e sessões

Cada aba criada possui uma instância WebView e mantém seu próprio histórico e estado de navegação enquanto o processo permanece ativo. **Isso não equivale a isolamento de conta.** WebViews no mesmo processo compartilham o perfil de cookies padrão; portanto, duas abas podem compartilhar a mesma sessão autenticada. O requisito de duas contas independentes continua BLOCKED até implementar e testar isolamento real de perfis/processos, sem quebrar o login.

## Segurança inicial

- Apenas navegação HTTP/HTTPS.
- JavaScript e DOM storage habilitados para compatibilidade com aplicações web.
- Acesso a arquivos locais e conteúdo local desabilitado.
- Conteúdo misto bloqueado.
- Permissões de microfone/câmera negadas no protótipo.
- Nenhum JavaScript bridge nativo exposto às páginas.
- Limite inicial de cinco abas.

## Limitações conhecidas

- Não há build APK validado nesta etapa.
- Não há teste no Galaxy Tab A7.
- Não há isolamento autenticado entre contas.
- Não há captura, mistura, encaminhamento ou injeção de áudio implementados.
- A barra de áudio é apenas um indicador visual de estado pendente.
