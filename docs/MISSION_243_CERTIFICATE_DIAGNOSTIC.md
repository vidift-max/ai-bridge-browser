# M243 — Diagnóstico seguro do certificado instalado

## 1. Objetivo

Identificar o certificado de assinatura SHA-256 do APK do AI Bridge Browser instalado no dispositivo Android que receberá a atualização.

O procedimento deve priorizar o diagnóstico diretamente pelo tablet Android, sem exigir computador.

O objetivo é permitir a validação da compatibilidade da assinatura antes de qualquer atualização, preservando o aplicativo instalado e seus dados.

Pacote Android:

`com.vidiftmax.aibridgebrowser`

## 2. Estado inicial auditado

Último estado documentado nesta missão:

- Branch padrão: `v2-saas-alpha`.
- SHA anteriormente auditado da branch padrão: `183a478681a3607f8e6612e4d68ab37583a6a5f3`.
- PR #234: aberta, Draft, mergeable e não mergeada no último registro disponível.
- Releases oficiais: nenhuma no último registro disponível.
- O procedimento ADB foi documentado anteriormente.
- O certificado do aplicativo instalado ainda não foi comprovado.

ATENÇÃO:

Essas informações são uma referência histórica. Antes de qualquer alteração no repositório, consultar o estado atual da branch, da PR e das Releases.

A versão declarada no código não comprova a versão instalada no tablet.

## 3. Método principal: diagnóstico pelo tablet Android

O usuário dispõe somente de um tablet Android e não possui computador Windows disponível.

Portanto, o método principal deve ser executável no próprio tablet.

Ferramenta candidata:

App Manager, projeto oficial:

https://github.com/MuntashirAkon/AppManager

Releases oficiais:

https://github.com/MuntashirAkon/AppManager/releases

Documentação:

https://github.com/MuntashirAkon/AppManager/wiki

O App Manager deve ser tratado como uma ferramenta candidata, não como uma solução já comprovada no dispositivo do usuário.

Antes de considerar o método aprovado, verificar:

1. Se a versão atual do App Manager é compatível com a versão Android do tablet.
2. Se o aplicativo consegue listar o pacote `com.vidiftmax.aibridgebrowser`.
3. Se consegue consultar os certificados de assinatura de outro aplicativo instalado.
4. Se apresenta o SHA-256 do certificado.
5. Se o resultado corresponde aos certificados de assinatura reportados pelo Android Package Manager.

Não presumir que permissões disponíveis em versões antigas do Android continuam disponíveis nas versões atuais.

Não solicitar root.

Não instalar módulos, complementos ou ferramentas desconhecidas para contornar restrições do Android.

## 4. Instalação e utilização do App Manager

Se a compatibilidade da versão atual estiver confirmada:

1. Abrir o endereço oficial de Releases do App Manager.
2. Selecionar uma versão estável compatível com o tablet.
3. Conferir a origem do arquivo antes de instalar.
4. Instalar o App Manager, se o usuário autorizar.
5. Abrir o aplicativo.
6. Localizar o AI Bridge Browser na lista de aplicativos instalados.
7. Conferir o nome e o pacote:

`com.vidiftmax.aibridgebrowser`

8. Abrir os detalhes do aplicativo.
9. Procurar a seção de assinaturas, identificada como `Signatures`, `Signing certificates` ou nome equivalente na versão utilizada.

A instalação do App Manager não autoriza nenhuma alteração no AI Bridge Browser.

Se o App Manager não conseguir listar ou consultar o aplicativo, interromper o procedimento e registrar BLOCKED.

## 5. Como localizar o certificado SHA-256

Na seção de assinaturas do AI Bridge Browser:

1. Identificar o certificado de assinatura apresentado.
2. Localizar o campo SHA-256 ou fingerprint SHA-256.
3. Copiar o valor completo.
4. Não confundir SHA-256 do certificado com SHA-256 do APK.
5. Não confundir o fingerprint do certificado com o hash de outro arquivo.

Formato esperado:

`AA:BB:CC:DD:...`

O valor deve conter 32 bytes, representados por 64 caracteres hexadecimais, desconsiderando separadores.

Normalização para comparação:

- Remover os dois-pontos.
- Remover espaços.
- Converter letras para minúsculas.
- Confirmar que restam exatamente 64 caracteres hexadecimais.

Não inventar, completar ou corrigir manualmente caracteres ausentes.

O usuário deve compartilhar somente o fingerprint SHA-256, sem enviar dados privados do dispositivo.

## 6. Validação da confiabilidade do resultado

Um resultado só poderá ser considerado evidência válida se:

- O aplicativo consultado for exatamente `com.vidiftmax.aibridgebrowser`.
- O certificado estiver identificado como certificado de assinatura do pacote.
- O SHA-256 estiver completo.
- A ferramenta e sua versão forem identificadas.
- O Android não tiver apresentado erro ou limitação na consulta.
- A informação não for confundida com o hash do APK.

Se houver múltiplos certificados ou signatários, registrar todos os fingerprints apresentados e a informação de qual conjunto de signatários foi reportado.

Não selecionar arbitrariamente um certificado.

Se a ferramenta apresentar apenas um valor parcial, resultado ambíguo ou informação não verificável, classificar BLOCKED.

Uma captura de tela pode ajudar na revisão, mas não substitui a validação do valor completo.

## 7. Método alternativo: ADB em computador

Este método permanece disponível para usuários que tenham computador.

Requisitos:

- Android Platform Tools (ADB).
- Android SDK Build Tools.
- Conexão USB autorizada pelo usuário.

Comandos:

Consultar o dispositivo:

`adb devices`

Consultar o caminho do APK:

`adb shell pm path com.vidiftmax.aibridgebrowser`

Copiar o APK base:

`adb pull "/data/app/.../base.apk" installed-ai-bridge.apk`

Consultar a versão instalada:

`adb shell dumpsys package com.vidiftmax.aibridgebrowser`

Consultar o certificado:

`apksigner verify --verbose --print-certs installed-ai-bridge.apk`

Registrar somente o valor de:

`Signer certificate SHA-256 digest`

A documentação oficial:

https://developer.android.com/tools/adb

https://developer.android.com/tools/apksigner

O ADB deve ser utilizado somente para leitura nesta missão.

Depois de concluir, o usuário pode revogar a autorização USB do computador e desativar a depuração USB.

## 8. Gate de compatibilidade da assinatura

O fingerprint obtido deve vir do aplicativo efetivamente instalado no tablet que receberá a atualização.

A validação precisa comparar:

1. Certificado do aplicativo instalado.
2. Certificado do APK Release que será publicado.
3. Conjunto de signatários, quando aplicável.
4. Compatibilidade do pacote e da versão.

O certificado do APK Release precisa ser obtido do artefato Release efetivamente assinado.

Não utilizar como substituto:

- Certificado de APK Debug.
- Certificado de um APK de outro dispositivo.
- Certificado de um keystore recém-criado sem comprovação de continuidade.
- Fingerprint presumido.
- Histórico Git.
- Nome do arquivo.
- Versão declarada no código.

A variável:

`AI_PHONE_EXPECTED_SIGNING_CERT_SHA256`

não poderá ser preenchida com um valor presumido.

Se a assinatura instalada e a assinatura Release forem diferentes, não publicar a atualização.

Se a chave original não estiver disponível, interromper e planejar uma estratégia separada de recuperação ou migração, com autorização explícita.

## 9. Preservação dos dados e recuperação

Durante esta missão, é proibido:

- Desinstalar o AI Bridge Browser.
- Reinstalar o AI Bridge Browser.
- Atualizar o AI Bridge Browser.
- Limpar dados ou armazenamento.
- Executar `pm clear`.
- Executar `adb uninstall`.
- Executar `adb install`.
- Redefinir o tablet.
- Tentar downgrade.
- Ignorar avisos de assinatura do Android.
- Alterar a chave de assinatura.
- Fazer backup ou migração sem autorização explícita.

A consulta do certificado deve ser somente de leitura.

O usuário não deve fornecer:

- Senhas.
- Cookies.
- Tokens.
- Chaves privadas.
- Keystore.
- Dados privados do aplicativo.

## 10. Alternativas quando o Android bloquear a leitura

Se o App Manager não conseguir consultar a assinatura, avaliar alternativas na seguinte ordem:

1. Verificar se existe uma versão compatível do App Manager com suporte à versão Android do tablet.
2. Verificar se o Android permite consultar as informações de assinatura por outra ferramenta confiável e sem root.
3. Avaliar uma solução Android local que utilize APIs públicas do PackageManager, incluindo `GET_SIGNING_CERTIFICATES`, quando disponível.
4. Se nenhuma alternativa conseguir obter uma evidência confiável, manter BLOCKED.

Não desenvolver uma solução que alegue conseguir acessar arquivos privados de `/data/app` sem permissões apropriadas.

Não prometer que Termux ou outro aplicativo comum conseguirá acessar diretamente arquivos privados de outro pacote.

Não solicitar root como solução padrão.

Não contornar as proteções de segurança do Android.

## 11. Evidências exigidas

Registrar:

- Identificação do dispositivo como tablet Android, sem armazenar identificadores pessoais desnecessários.
- Versão Android, se disponível.
- Nome e versão da ferramenta de diagnóstico.
- Pacote consultado.
- Quantidade de certificados/signatários apresentados.
- Fingerprint SHA-256 completo.
- Método utilizado.
- Resultado da validação.
- Data da consulta.

O fingerprint pode ser registrado como evidência técnica do certificado público.

Não armazenar o conteúdo completo de respostas de outras IAs como evidência.

Não declarar que o diagnóstico ocorreu no dispositivo enquanto não houver resultado fornecido pelo próprio dispositivo.

## 12. Critérios PASS / NO-GO / BLOCKED

### PASS

Somente quando:

- O certificado do aplicativo instalado foi obtido.
- O fingerprint está completo.
- A origem da evidência está identificada.
- A consulta corresponde ao pacote correto.
- O resultado é tecnicamente verificável.

PASS nesta missão significa somente diagnóstico concluído.

Não significa autorização para atualizar ou publicar.

### NO-GO

Quando:

- O certificado instalado divergir do certificado do APK Release.
- Houver incompatibilidade de assinatura.
- O conjunto de signatários não corresponder.
- O procedimento apresentar risco de perda de dados.

NO-GO impede a atualização até existir uma estratégia segura e aprovada.

### BLOCKED

Quando:

- O tablet não permitir consultar o certificado.
- O App Manager não conseguir acessar as informações necessárias.
- O fingerprint estiver incompleto.
- A ferramenta apresentar resultado ambíguo.
- Não existir evidência suficiente para validar a assinatura.

BLOCKED não deve ser convertido em PASS por suposição.

## 13. Estado final da missão

Estado inicial:

BLOCKED — certificado do aplicativo instalado ainda não comprovado.

O documento atualizado oferece um procedimento prioritário pelo tablet e mantém o método ADB como alternativa.

A documentação não comprova que o procedimento já foi executado no tablet.

Nenhum certificado deve ser considerado encontrado até que exista evidência verificável.

Nenhuma Release deve ser publicada enquanto o gate de assinatura não estiver aprovado.

Nenhum merge, deploy, instalação ou alteração de Secrets está autorizado por esta missão.

## 14. Referências oficiais

App Manager:

https://github.com/MuntashirAkon/AppManager

Releases:

https://github.com/MuntashirAkon/AppManager/releases

Documentação App Manager:

https://github.com/MuntashirAkon/AppManager/wiki

Android PackageManager:

https://developer.android.com/reference/android/content/pm/PackageManager

Android SigningInfo:

https://developer.android.com/reference/android/content/pm/SigningInfo

Android Debug Bridge:

https://developer.android.com/tools/adb

Android apksigner:

https://developer.android.com/tools/apksigner
