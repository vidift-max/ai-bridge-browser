# Missão 199 — Central de Atualizações dentro do aplicativo

## Objetivo
Começar a implementação real da área Atualizações para que novas versões possam ser verificadas e instaladas pelo próprio AI Bridge Browser, sem exigir que o usuário procure links nas conversas.

## 10 rodadas

| Rodada | Trabalho verificável | Resultado |
|---|---|---|
| 01/10 | Revalidar PR #201, HEAD M198 e execuções Android. | PASS — PR #201 Draft e não mesclada; CI M198 passou em push e pull_request no HEAD `74d952a1d41d397e867d5e5c70352e978e5a54eb`. |
| 02/10 | Criar branch isolada M199 a partir do HEAD M198. | PASS — `feat/mission-199-in-app-updates`. |
| 03/10 | Implementar `UpdateCenterActivity` com versão instalada, consulta de releases estáveis e estado de atualização. | PASS em código — tela nativa com botão Verificar atualizações e estado de versão. |
| 04/10 | Implementar leitura de manifesto e descoberta de assets de release. | PASS em código — exige `ai-bridge-update.json`, `app-release.apk`, pacote esperado e versionCode superior. |
| 05/10 | Implementar download e verificações antes do instalador. | PASS em código — limita tamanho, valida SHA-256, packageName e certificado de assinatura comparado com a instalação atual; falhas bloqueiam a instalação. |
| 06/10 | Integrar o handoff seguro ao instalador Android. | PASS em código — usa FileProvider e Intent ACTION_VIEW; respeita autorização Android para instalar apps de fontes desconhecidas. |
| 07/10 | Adicionar entrada Atualizações à tela inicial e registrar Activity/permissões/paths. | PASS em código — botão visível em HomeActivity, Activity interna, permissão REQUEST_INSTALL_PACKAGES e caminho app-private do FileProvider. |
| 08/10 | Criar política de manifesto fail-closed e testes JVM. | PASS em código — `UpdateManifestPolicy` e 5 testes para versão, package, asset, hash, origem e metadados ausentes. |
| 09/10 | Atualizar filtros do workflow e documentação de estado. | PASS em código/documentação — M199 incluída em push; M198 incluída como base de PR; estado e limitações descritos. |
| 10/10 | Abrir PR Draft e validar CI do novo HEAD. | PENDENTE — aguardando conclusão da execução Android no HEAD M199 e abertura/checagem final da PR. |

## Evidências

- PR M198: https://github.com/vidift-max/ai-bridge-browser/pull/201
- Branch M199: `feat/mission-199-in-app-updates`.
- Base: HEAD M198 `74d952a1d41d397e867d5e5c70352e978e5a54eb`.
- Arquivos novos:
  - `app/src/main/java/com/vidiftmax/aibridgebrowser/UpdateCenterActivity.java`
  - `app/src/main/java/com/vidiftmax/aibridgebrowser/UpdateManifestPolicy.java`
  - `app/src/test/java/com/vidiftmax/aibridgebrowser/UpdateManifestPolicyTest.java`
- Arquivos alterados:
  - `app/src/main/java/com/vidiftmax/aibridgebrowser/HomeActivity.java`
  - `app/src/main/AndroidManifest.xml`
  - `app/src/main/res/xml/file_paths.xml`
  - `.github/workflows/android-build.yml`
  - `docs/ANDROID_UPDATE_AND_GOOGLE_ACCOUNT_SELECTION.md`

## Protocolo esperado para uma release futura

O app consulta `GET /repos/vidift-max/ai-bridge-browser/releases/latest`. Uma release estável precisa conter:
- `ai-bridge-update.json` com `versionCode`, `versionName`, `packageName`, `apkAssetName`, `sha256` e `notes`.
- `app-release.apk` com o mesmo applicationId e certificado de assinatura do app instalado.

O APK só é oferecido quando a versão é superior, o pacote e nome do asset correspondem, o hash tem formato válido e a origem do download é HTTPS oficial do repositório. No download, o app verifica tamanho máximo, integridade SHA-256, packageName e assinatura do APK contra o certificado já instalado. Só então abre o instalador do Android. A confirmação/permite instalação do Android continua obrigatória quando exigida.

## CI M198 — baseline confirmada

No HEAD `74d952a1d41d397e867d5e5c70352e978e5a54eb`:
- Push run #45747077705: SUCCESS.
- PR run #45747085523: SUCCESS.
- Em ambos, `debug-build` e `release-preparation` SUCCESS; `release-final` SKIPPED.
- Artefatos do push run: debug #15082759604 e release-preparation #15083134330.
- Isso valida a baseline M198, não a implementação M199.

## Limitações e bloqueios

- O endpoint de latest release retornou HTTP 404 na auditoria: não existe release estável publicada. A tela informa que ainda não existe versão oficial disponível; não fabrica atualização.
- Nenhuma release, APK assinado, manifesto de distribuição, chave ou segredo foi criado/publicado nesta missão.
- O fluxo de atualização ainda precisa passar pelo CI M199 e por teste físico: download real, validação de hash/certificado, permissão de instalação, instalação sobre versão anterior e preservação dos dados/perfis.
- Download atual é executado dentro da tela e não promete retomada em segundo plano; se interrompido, usuário poderá iniciar novamente.
- O seletor de conta Google/ChatGPT não foi implementado nesta missão; continua como requisito documentado.
- Não houve login em conta, instalação, publicação, deploy, merge, envio de mensagens ou ativação de AI-03+.
- Escopo permanece AI-01 e AI-02.

## Conclusão
**PASS** para a primeira implementação de interface e pipeline de atualização dentro do app, com validação fail-closed no código. **BLOCKED** para CI final M199, publicação de release assinada e validação física. A PR deve permanecer Draft e não mesclada.
