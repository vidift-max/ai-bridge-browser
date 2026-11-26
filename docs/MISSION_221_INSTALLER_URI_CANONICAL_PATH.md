# M221 — Canonicalização e vínculo do URI do instalador

## Objetivo
Impedir que um URI content:// com autoridade correta, mas caminho alternativo, traversal ou flags extras, seja entregue ao instalador Android.

## Dez rodadas
1. Releitura da política e do URI efetivamente gerado pelo FileProvider.
2. Confirmação do caminho autorizado configurado em file_paths.xml: app_update_apk/app-release.apk.
3. Identificação do risco de aceitar qualquer sufixo após a autoridade do provider.
4. Troca da validação por parsing estrito com java.net.URI.
5. Exigência de esquema content e autoridade exata, sem userinfo ou porta.
6. Vinculação ao caminho bruto exato /app_update_apk/app-release.apk.
7. Rejeição de query, fragmentos, caracteres não ASCII e URI malformado.
8. Allowlist de flags: leitura e NEW_TASK; rejeição de escrita e flags não previstas.
9. Ampliação dos testes para traversal literal/codificado, autoridade parecida, porta, userinfo, caminho alternativo e flags.
10. Documentação e integração contínua da nova branch para validação independente por push e PR.

## Limites
A validação limita o URI e as permissões entregues pelo aplicativo; não substitui a segurança do Android, a assinatura do APK nem teste físico. O Android continua responsável pela confirmação e instalação. Sem merge, Release, assinatura, alteração de Secrets, instalação física ou ativação de AI-03.
