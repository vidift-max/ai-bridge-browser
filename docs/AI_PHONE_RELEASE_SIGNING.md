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
