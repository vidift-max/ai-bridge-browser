# Isolamento de sessões

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
- Criar duas abas com nomes de perfil diferentes e entrar em duas contas de teste.
- Confirmar que cada aba mantém sua própria sessão após alternância e reinício do app.
- Sair de uma conta e confirmar que a outra permanece autenticada.
- Apagar dados de um perfil e confirmar que os demais não são afetados.
- Repetir com seis perfis, medir memória, estabilidade e tempo de inicialização.
- Testar atualização do Android System WebView e indisponibilidade da feature.

## Referências oficiais

- AndroidX WebKit API: https://developer.android.com/reference/androidx/webkit/WebViewCompat
- WebKit release notes: https://developer.android.com/jetpack/androidx/releases/webkit

## Regra de segurança

Nunca tratar `tabId` ou `profileId` como prova de isolamento. O estado exibido por aba deriva do sucesso da atribuição real do perfil. Se o provider não oferecer `MULTI_PROFILE`, a interface deve deixar claro que a sessão é compartilhada.
