# Isolamento de sessões

## Escopo de contas: teto 20, operação atual 2

O produto pode evoluir para suportar até **20 contas de IA** (`AiAccountCapacityPolicy.MAX_SUPPORTED_ACCOUNTS`). Isso é apenas o teto arquitetural. A missão atual ativa e exibe somente **AI-01 e AI-02** (`CURRENT_MISSION_LIMIT = 2`). Abas extras do navegador não recebem automaticamente uma identidade de IA ativa. Não provisionar, autenticar nem testar AI-03 a AI-20 nesta etapa.

O registro interno comporta até 20 identidades para permitir evolução futura, mas a interface e o fluxo atual limitam o trabalho a duas. A capacidade futura não é evidência de que 20 sessões estejam testadas ou prontas.

## Baseline e correção implementada

O baseline usava o perfil padrão em todas as WebViews. Identificadores `profileId` separados, sozinhos, não isolavam cookies, armazenamento local ou autenticação.

A implementação atual adiciona AndroidX WebKit `1.18.0` e, durante a criação de cada WebView:

1. Gera ou restaura um `profileId` estável.
2. Verifica `WebViewFeature.MULTI_PROFILE`.
3. Quando disponível, chama `WebViewCompat.setProfile(webView, profileId)` antes de acessar settings, clientes ou navegar.
4. Se a feature não estiver disponível ou a atribuição falhar, mantém o navegador utilizável, mas marca aquela aba como perfil compartilhado e informa o usuário.

A API oficial declara que perfis múltiplos permitem sessões de navegação separadas, com dados próprios como cookies. `setProfile` precisa ocorrer antes de qualquer outra operação sobre a WebView, exceto anexá-la à hierarquia de views.

## Limite da evidência

**Estado: IMPLEMENTADO COM FEATURE GATE; ISOLAMENTO REAL AINDA NÃO VALIDADO EM DISPOSITIVO.**

O build de CI pode confirmar compilação, não a versão do Android System WebView instalada no Galaxy Tab A7, nem a separação efetiva dos dados. Até o teste físico, não cadastrar contas distintas em abas marcadas como compartilhadas e não anunciar seis sessões independentes como comprovadas.

## Testes obrigatórios no dispositivo

- Consultar a disponibilidade de `MULTI_PROFILE` no WebView instalado.
- Criar exatamente duas abas de IA: AI-01 e AI-02, com nomes de perfil diferentes, e entrar manualmente em duas contas ChatGPT distintas.
- Confirmar que cada aba mantém sua própria sessão após alternância e reinício do app.
- Sair de uma conta e confirmar que a outra permanece autenticada.
- Apagar dados de um perfil e confirmar que os demais não são afetados.
- Nesta missão, não expandir além de AI-01 e AI-02. Testes de escala até 20 ficam para uma missão futura, após aprovação.
- Testar atualização do Android System WebView e indisponibilidade da feature.

## Referências oficiais

- AndroidX WebKit API: https://developer.android.com/reference/androidx/webkit/WebViewCompat
- WebKit release notes: https://developer.android.com/jetpack/androidx/releases/webkit

## Regra de segurança

Nunca tratar `tabId` ou `profileId` como prova de isolamento. O estado exibido por aba deriva do sucesso da atribuição real do perfil. Se o provider não oferecer `MULTI_PROFILE`, a interface deve deixar claro que a sessão é compartilhada.


## Evidências da Missão 193 — limite de duas contas ativas

- `AiAccountCapacityPolicy.java` define teto futuro 20 e limite operacional atual 2.
- `AIControlCenter.java` mantém capacidade de registro até 20, separada do gate de ativação na `MainActivity`.
- `MainActivity` cria no máximo dois painéis ativos e restaura no máximo dois painéis nesta fase.
- Testes adicionados para teto 20, gate de ativação em 2 e rejeição de cruzamento entre `tabId/profileId` de AI-01 e AI-02.
- Atribuição de `WebViewCompat.setProfile` continua condicionada a `MULTI_PROFILE` e ocorre antes de settings/clientes/navegação.
- O teste físico em dispositivo continua obrigatório. IDs diferentes e testes JVM não provam cookies isolados nem login independente.
