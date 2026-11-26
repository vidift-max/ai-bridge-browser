# Missão 215 — vínculo entre Release estável, tag e assets do atualizador

## Objetivo
Evitar que o atualizador combine manifesto e APK de publicações diferentes, aceite assets ambíguos/duplicados ou interprete metadados coercivamente.

## Dez rodadas
1. Confirmar PASS dos workflows push e pull_request da Missão 214 no SHA `c536e8c2ec5cadbbfeffc6f54e5e30174b6977dd`.
2. Auditar o consumo da resposta `releases/latest` e identificar ausência de vínculo explícito entre `tag_name` e as URLs dos assets.
3. Identificar que a busca de assets retornava o primeiro nome correspondente, sem rejeitar duplicatas.
4. Criar `UpdateReleasePolicy` para exigir Release estável com `draft=false`, `prerelease=false` e tag em formato restrito.
5. Exigir metadados tipados, sem coerção de strings/números/booleanos.
6. Exigir exatamente um asset com o nome esperado, estado `uploaded`, tamanho numérico positivo e URL de download.
7. Vincular cada URL ao caminho exato `/releases/download/<tag>/<asset>` do repositório oficial.
8. Integrar a validação do manifesto e do APK antes de permitir que a versão seja candidata a atualização.
9. Adicionar testes para Release draft/prerelease, tag inválida, assets ausentes/duplicados, estado incorreto, tamanho inválido, tipos coercivos e tag divergente.
10. Registrar limites de segurança, ativar CI para M215 e manter PR Draft sem merge ou publicação.

## Controles
- A API consultada continua sendo a URL fixa de `releases/latest`.
- O tag retornado pela API é validado e passa a fazer parte da URL esperada de cada asset.
- Manifesto e APK devem existir uma única vez, estar carregados (`uploaded`) e ter tamanho positivo.
- URLs de assets devem corresponder exatamente ao repositório, à tag e ao nome de asset esperados.
- As validações de SHA-256, package/version e certificado permanecem controles independentes.

## Limites
Nenhum Secret foi acessado ou alterado. Nenhuma assinatura, Release, publicação, instalação ou ativação foi executada. AI-03 permanece desativada. Nenhuma comunicação real AI-01 ↔ AI-02 foi alegada.

## Critério de aprovação
PASS técnico somente após testes Android, testes Python, build Debug e Release Preparation passarem nos workflows do SHA final. O resultado não comprova assinatura de produção nem instalação física.
