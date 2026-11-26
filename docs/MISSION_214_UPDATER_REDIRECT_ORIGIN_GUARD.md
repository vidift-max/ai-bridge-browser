# Missão 214 — proteção de origem e redirecionamento do atualizador

## Objetivo
Garantir que URLs de manifesto e APK partam do caminho exato de GitHub Releases deste repositório e que qualquer redirecionamento HTTP termine somente em HTTPS nos hosts oficiais esperados do GitHub/CDN.

## Dez rodadas de engenharia
1. Confirmar PASS da Missão 213 nos workflows push e pull_request do SHA `bcb5f8e6886e5ba76f34c34dcb107f9c30e9c3ae`.
2. Auditar os pontos de entrada de URL: API de Releases, asset do manifesto e asset do APK.
3. Identificar que a validação anterior usava prefixo textual para URL inicial e verificava somente HTTPS/host permitido após redirecionamento.
4. Definir uma política centralizada baseada em URI, sem aceitar userinfo, portas alternativas, fragmentos ou query na URL inicial de asset.
5. Restringir URL inicial a `https://github.com/vidift-max/ai-bridge-browser/releases/download/<tag>/<asset>`.
6. Restringir destino final de redirecionamento a HTTPS nos hosts exatos `github.com`, `api.github.com`, `objects.githubusercontent.com` e `release-assets.githubusercontent.com`, em porta padrão.
7. Integrar a política à validação do manifesto e ao controle do destino final de `readUrl` e `download`.
8. Adicionar testes positivos e negativos para hosts parecidos, repositórios diferentes, esquema HTTP, porta alternativa, credenciais embutidas, query, fragmento e redirecionamento externo.
9. Incluir branch e base M213 nos gatilhos do CI para validar a alteração antes de qualquer integração.
10. Registrar limites de Release e manter PR Draft, sem merge, assinatura, publicação ou instalação.

## Política aplicada
- URL inicial de asset deve pertencer exatamente ao repositório oficial e ao caminho de download de Releases.
- Não são aceitos hosts parecidos, outros repositórios, HTTP, userinfo, portas não padrão, query ou fragmento na URL inicial.
- Após redirecionamento, só HTTPS e os quatro hosts exatos listados acima são aceitos.
- Integridade SHA-256, packageName, versionCode/versionName e certificado de assinatura continuam sendo verificações independentes e obrigatórias.

## Limites de segurança
- Nenhum Secret ou material de assinatura foi acessado, criado, modificado ou transmitido.
- O job `release-final` permanece manual e condicionado aos Secrets.
- Nenhuma GitHub Release foi publicada e nenhum APK foi instalado.
- Nenhum teste físico nem comunicação real AI-01 ↔ AI-02 foi alegado.
- AI-03 permanece fora do escopo; somente AI-01 e AI-02 continuam no escopo ativo.

## Critério de aprovação
PASS técnico quando testes unitários Android, testes Python, build Debug e Release Preparation passarem nos workflows do SHA final. Isso não equivale a Release assinada ou atualização física validada.
