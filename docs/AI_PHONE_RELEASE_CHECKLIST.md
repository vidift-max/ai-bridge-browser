# AI-PHONE — Release Checklist

## Antes da assinatura
- [ ] Chave definitiva criada pelo responsável.
- [ ] Keystore original guardado fora do repositório.
- [ ] `AI_PHONE_RELEASE_KEYSTORE_B64` cadastrado como Secret.
- [ ] `AI_PHONE_RELEASE_STORE_PASSWORD` cadastrado como Secret.
- [ ] `AI_PHONE_RELEASE_KEY_ALIAS` cadastrado como Secret.
- [ ] `AI_PHONE_RELEASE_KEY_PASSWORD` cadastrado como Secret.
- [ ] Nenhum keystore/JKS/Base64 está versionado.

## CI
- [ ] Android Build passa.
- [ ] Messenger Backend Test passa.
- [ ] `release-final` executado por workflow manual.
- [ ] `apksigner verify --verbose --print-certs` passa.
- [ ] SHA-256 do APK é registrado.
- [ ] Certificado/fingerprint é registrado.
- [ ] Artefato `ai-phone-release-apk` existe.

## Dispositivo
- [ ] Instalação inicial Release concluída.
- [ ] Play Protect analisado sem desativar a proteção.
- [ ] AI-PHONE abre.
- [ ] AI Messenger abre.
- [ ] Funções já validadas continuam funcionando.
- [ ] APK baixado tem o mesmo SHA-256 registrado pelo CI.

## Regra de atualização
A chave Release é parte da identidade do aplicativo. Futuras versões devem usar a mesma chave para permitir atualização normal.
