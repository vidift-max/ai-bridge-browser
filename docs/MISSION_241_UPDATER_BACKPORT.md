# M241 — Backport seletivo do atualizador

## Objetivo
Integrar o atualizador da M226 à branch atual sem substituir a HomeActivity, o manifesto Android ou o workflow atual por versões históricas.

## Decisões
- Preservar a HomeActivity atual e acrescentar somente o botão de atualização.
- Mesclar somente UpdateCenterActivity, FileProvider, permissão e paths necessários no manifesto.
- Preservar dependências existentes; adicionar AndroidX Core e JSON de teste.
- Manter AI-01 e AI-02; AI-03 permanece desativada.
- CI executa testes Android e Python. Publicação apenas por dispatch manual na branch padrão.
- Exigir `AI_PHONE_EXPECTED_SIGNING_CERT_SHA256` para confirmar continuidade do certificado instalado antes de publicar.

## Limites
Nenhum Secret foi lido ou alterado. Nenhuma Release foi publicada. Nenhum APK foi instalado. O teste físico AI-01 ↔ AI-02 continua pendente.
