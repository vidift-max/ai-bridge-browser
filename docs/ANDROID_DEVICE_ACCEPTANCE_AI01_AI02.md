# Checklist físico — isolamento de sessões AI-01 / AI-02

Este roteiro só pode ser executado após autorização explícita para instalar/testar no dispositivo. Não usar contas reais em perfis marcados como compartilhados.

## Pré-condições
- [ ] APK instalado de uma origem/artefato aprovado.
- [ ] Registrar modelo do dispositivo, versão Android e versão do Android System WebView.
- [ ] Confirmar `WebViewFeature.MULTI_PROFILE` disponível no WebView instalado.
- [ ] Se a feature não estiver disponível ou `setProfile` falhar: PARAR; nenhuma conta AI deve ser associada.
- [ ] Confirmar que a UI mostra perfil compartilhado e alerta quando a atribuição falha.

## Teste AI-01 / AI-02
- [ ] Criar exatamente duas abas de IA, sem ativar AI-03 ou além.
- [ ] Confirmar `profileId` diferentes e atribuição MULTI_PROFILE bem-sucedida em ambas.
- [ ] Entrar manualmente na conta ChatGPT designada para AI-01.
- [ ] Entrar manualmente em uma conta ChatGPT diferente para AI-02.
- [ ] Alternar entre abas e confirmar que cada uma mantém sua própria conta.
- [ ] Fechar e reabrir o app; confirmar persistência independente das sessões.
- [ ] Sair da conta AI-01 e confirmar que AI-02 continua autenticada.
- [ ] Não executar limpeza individual de perfil até existir um fluxo explícito, testado e auditável no aplicativo. A interface atual ainda não oferece limpeza por perfil.
- [ ] Não substituir limpeza individual por `CookieManager.getInstance()` ou limpeza global; as APIs globais operam no perfil padrão e podem não representar o perfil selecionado.
- [ ] Testar uma aba com MULTI_PROFILE indisponível; confirmar que ela não recebe painel AI.
- [ ] Confirmar que fila pendente vinculada a tabId/profileId antigo não é enviada a outra aba.
- [ ] Confirmar que nenhuma mensagem é injetada no DOM nem enviada automaticamente.

## Evidência a registrar
- [ ] Captura da versão Android e Android System WebView.
- [ ] Resultado de disponibilidade MULTI_PROFILE.
- [ ] IDs não sensíveis dos perfis/abas (não registrar cookies, tokens ou conteúdo privado).
- [ ] Resultado de alternância, reinício, logout e limpeza individual.
- [ ] Logs sem segredos demonstrando atribuição ou falha.
- [ ] PASS/FAIL por item, data e responsável pelo teste.

## Limitação conhecida — limpeza de dados
O aplicativo atualmente não implementa uma ação de limpeza individual por perfil nem usa `ProfileStore.deleteProfile`. A validação de logout/limpeza independente permanece BLOCKED até implementação dedicada e teste físico. Não executar limpeza global como substituto.

## Critério final
Só declarar isolamento físico PASS quando AI-01 e AI-02 mantiverem sessões diferentes após alternância e reinício e quando logout/limpeza de um perfil não afetar o outro. Build, testes JVM e IDs distintos não substituem essa prova.
