# AI-PHONE — Release Signing

## Objetivo

O AI-PHONE não deve ser distribuído como `app-debug.apk` quando a intenção for entrega a participantes. O fluxo de entrega deve usar uma variante Release assinada por uma chave própria do projeto.

## Estado atual

O projeto agora possui:
- variante Android Release;
- configuração de assinatura condicional;
- workflow que prepara o Release;
- suporte a keystore protegido por GitHub Actions Secrets;
- manutenção do APK Debug para desenvolvimento/testes.

Sem os quatro segredos de assinatura, o workflow gera apenas um APK Release de preparação **não assinado**. Esse artefato não deve ser apresentado como APK final de distribuição.

## Segredos necessários

Configurar no repositório, como GitHub Actions Secrets:

- `AI_PHONE_RELEASE_KEYSTORE_B64` — keystore em Base64;
- `AI_PHONE_RELEASE_STORE_PASSWORD` — senha do keystore;
- `AI_PHONE_RELEASE_KEY_ALIAS` — alias da chave;
- `AI_PHONE_RELEASE_KEY_PASSWORD` — senha da chave.

A chave privada não deve ser commitada no repositório.

## Regra de segurança

A mesma chave de assinatura deve ser preservada para futuras atualizações do AI-PHONE. Perder ou substituir a chave pode impedir atualizações normais do mesmo aplicativo instalado.

## Verificação

O workflow deve distinguir explicitamente:
- Release assinado e pronto para distribuição;
- Release de preparação sem assinatura.

Assinatura Release melhora a identidade e a cadeia de distribuição, mas não garante que o Google Play Protect nunca apresente aviso quando o APK é instalado fora da Google Play.


## Como preparar a chave no Windows

1. Tenha um JDK 17+ instalado.
2. Execute `scripts/create_ai_phone_release_keystore.ps1`.
3. O script cria localmente:
   - `ai-phone-release.keystore`;
   - `ai-phone-release-keystore.b64`.
4. Cadastre os quatro valores como **GitHub Actions Secrets** do repositório.
5. Não faça commit do keystore nem do arquivo Base64.
6. Depois, execute manualmente o workflow **Android Build** para produzir o artefato `ai-phone-release-apk`.

A ferramenta disponível para esta sessão não possui permissão para criar/alterar Secrets do GitHub. Portanto, a etapa de cadastro dos quatro Secrets precisa ser feita pelo responsável do repositório.

## Gate de entrega

O artefato `ai-phone-release-apk` só é produzido pelo job `release-final` quando os quatro Secrets existem e a assinatura é validada pelo `apksigner verify --verbose`.

O artefato `ai-phone-release-preparation` continua sendo apenas de preparação e não deve ser tratado como versão final.


## Verificação adicional do Release

Quando os Secrets estiverem configurados, o job final deve:
- construir `app-release.apk`;
- executar `apksigner verify --verbose`;
- imprimir os certificados da assinatura;
- gerar um arquivo SHA-256 do APK;
- publicar o APK e o registro de checksum como artefatos separados.

O checksum serve para comparar o arquivo baixado com o arquivo efetivamente produzido pelo CI. Ele não substitui a verificação criptográfica da assinatura.


## Critério de segurança do repositório

O CI também verifica que nenhum arquivo de keystore, JKS ou Base64 do keystore está versionado. Se material de assinatura for encontrado no índice Git, o job final falha.


## Instalação no tablet de desenvolvimento

O APK Release será assinado com uma chave diferente da chave de debug usada pelos APKs de desenvolvimento. Portanto, uma instalação Release pode exigir a remoção do APK Debug anterior antes da primeira instalação Release. Depois disso, futuras versões Release devem manter a mesma chave para atualização normal.

A assinatura Release não desativa o Play Protect e não deve ser usada para contornar os mecanismos de segurança do Android.
