# M243 — Diagnóstico seguro do certificado instalado

## Objetivo

Identificar o certificado SHA-256 do APK que já está instalado no Android, sem desinstalar, atualizar, sobrescrever ou modificar o aplicativo e sem acessar dados privados do app.

## Estado inicial auditado

- Branch padrão: `v2-saas-alpha`.
- SHA da branch padrão auditado: `183a478681a3607f8e6612e4d68ab37583a6a5f3`.
- PR #234: aberta, Draft, mergeable, não mergeada.
- Head da PR #234 auditado: `0e43bc1b0b8b2c79139b6dfb4b128682edfbcb30`.
- CI do head: Android Build run `45798921672`, sucesso; `debug-build` passou e `release-final` foi ignorado.
- Releases oficiais no repositório: nenhuma (`[]`).
- Versão declarada na branch padrão: pacote `com.vidiftmax.aibridgebrowser`, versionCode 1, versionName 0.1.0. Isso descreve o código da branch, não prova qual versão está instalada no dispositivo.

## Método de diagnóstico recomendado (somente leitura)

Este procedimento requer um computador com Android Platform Tools (ADB) e Android SDK Build Tools. Não requer root, desinstalação, instalação, alteração de dados do app ou leitura de Secrets.

1. Conecte o aparelho por USB ao computador. Se a depuração USB ainda não estiver habilitada, só habilite se o usuário compreender e autorizar essa conexão; depois de concluir, pode revogar a autorização do computador e desativar a depuração USB.
2. Confirme que o ADB reconhece o aparelho:
   `adb devices`
3. Consulte o caminho do APK instalado:
   `adb shell pm path com.vidiftmax.aibridgebrowser`
4. Use o caminho retornado que termina em `/base.apk` e copie somente esse APK para o computador. Exemplo (substitua pelo caminho real retornado):
   `adb pull "/data/app/.../base.apk" .\installed-ai-bridge.apk`
5. Consulte a versão instalada:
   `adb shell dumpsys package com.vidiftmax.aibridgebrowser`
   Procure `versionCode` e `versionName`. Não compartilhe a saída completa se ela contiver outros dados do dispositivo.
6. Extraia o fingerprint do certificado do APK copiado:
   `apksigner verify --verbose --print-certs .\installed-ai-bridge.apk`
7. Registre somente o valor de `certificate SHA-256 digest` (removendo dois-pontos e normalizando para letras minúsculas, se necessário). Não é necessário enviar o APK, dados do aplicativo, senhas ou tokens.

A documentação oficial do Android confirma que `pm path <package>` consulta o caminho do APK instalado e que `apksigner verify --print-certs` imprime os certificados de assinatura. O método é de leitura; não executar `adb install`, `adb uninstall`, `pm clear` ou qualquer comando de escrita nesta etapa.

## Gate de compatibilidade

- O fingerprint deve vir do APK efetivamente instalado no aparelho que receberá a atualização.
- Não inferir o certificado instalado a partir de um APK Debug de CI, do keystore novo, do nome do arquivo, da versão declarada no código ou do histórico Git.
- Comparar o fingerprint obtido com o certificado do APK Release que será gerado.
- Se o valor não puder ser obtido, estiver incompleto, for de outro dispositivo ou divergir: **BLOCKED**. Não preencher `AI_PHONE_EXPECTED_SIGNING_CERT_SHA256` com um palpite e não disparar o workflow de Release.
- A verificação interna do atualizador continua obrigatória: pacote correto, versão superior, SHA-256 do APK e certificado compatível com a instalação.
- Uma chave nova criada por `create_ai_phone_release_keystore.ps1` não será presumida compatível com a instalação antiga.

## Preservação de dados e recuperação

- Não desinstalar o app, limpar armazenamento, apagar dados, redefinir o aparelho ou reinstalar para tentar resolver divergência de assinatura.
- Não usar downgrade nem ignorar avisos do Android.
- Se a chave original não existir ou for incompatível, parar e planejar uma estratégia de backup/migração separada. Qualquer operação de backup, migração ou alteração de instalação exige avaliação e autorização explícitas.
- O APK copiado para diagnóstico deve permanecer local e pode ser apagado depois de registrar o fingerprint.

## Estado e limites desta missão

Este documento prepara o procedimento; não significa que o aparelho foi conectado, que o APK foi extraído ou que o fingerprint foi descoberto. Nenhum Secret foi consultado ou alterado, nenhuma Release foi criada e nenhuma instalação foi executada. A confirmação física permanece pendente até haver resultado do dispositivo.

## Referências oficiais

- Android Debug Bridge: https://developer.android.com/tools/adb
- apksigner: https://developer.android.com/tools/apksigner
