# M226 — publicação do APK oficial para o primeiro teste AI-01 ↔ AI-02

## Objetivo
Preparar uma versão Android atualizável, assinada e publicável como GitHub Release, para permitir o primeiro teste físico do par AI-01 / AI-02.

## Dez rodadas de engenharia
1. Auditar a cadeia de PRs, os resultados de CI e a existência de Releases.
2. Identificar e corrigir os workflows ancestrais M208/M209 que tentavam executar um Gradle Wrapper inexistente.
3. Criar esta branch a partir do código M225 aprovado em CI.
4. Incrementar a versão Android de 0.1.0 (versionCode 1) para 0.2.0 (versionCode 2), permitindo atualizar instalações da versão-base.
5. Manter a geração assinada restrita ao evento manual `workflow_dispatch`.
6. Conceder `contents: write` somente ao job de publicação final.
7. Publicar o APK assinado, o manifesto de atualização, o SHA-256 e o relatório de assinatura como assets de uma GitHub Release.
8. Adicionar testes estáticos para o contrato de publicação, versão e assets esperados.
9. Executar CI e confirmar artefatos, versão e gates; não considerar CI como prova de assinatura ou instalação física.
10. Fazer o dispatch manual do workflow, confirmar a Release, atualizar o Android e executar o teste de 10 turnos AI-01 ↔ AI-02.

## Contrato entre publicação e atualizador
O workflow gera a tag no formato `v<versionName>-<versionCode>` (atualmente `v0.2.0-2`). O atualizador consulta `/releases/latest`, rejeita drafts/prereleases, exige exatamente um asset `ai-bridge-update.json` e um `app-release.apk`, e valida que as URLs dos dois assets apontem para a mesma tag da Release. O manifesto vincula pacote, versão, nome do APK e SHA-256. A assinatura recebida ainda precisa corresponder ao certificado da instalação já presente no Android; isso só pode ser confirmado no dispositivo.

## Publicação manual
O workflow `workflow_dispatch` precisa estar presente na branch padrão do repositório para que o GitHub habilite a execução manual. A branch padrão atual é `v2-saas-alpha`, e o job de publicação também rejeita dispatch feito em qualquer outra branch. Portanto, toda a cadeia de PRs precisa ser integrada à `v2-saas-alpha`, após revisão e autorização explícita. Depois que o PR M226 estiver integrado e o workflow aprovado:
1. Abrir GitHub Actions → Android Build.
2. Selecionar Run workflow.
3. Selecionar exclusivamente a branch padrão `v2-saas-alpha`.
4. Executar o workflow manualmente.
5. O job `release-final` exige os quatro Secrets de assinatura já previstos no workflow. Se algum estiver ausente, a execução falha antes de criar a Release.
6. Quando a assinatura for validada, o workflow cria a Release `v0.2.0-2` e anexa `app-release.apk`, `ai-bridge-update.json`, `app-release.apk.sha256` e `app-release-signature.txt`.

Não cole senhas, keystore ou tokens no chat. Configure os Secrets diretamente em Settings → Secrets and variables → Actions do repositório.

## Critérios de PASS
- CI do SHA final aprovado.
- APK release assinado e identidade do pacote verificada.
- Manifesto contém o mesmo versionCode, versionName, nome do asset e SHA-256 do APK.
- GitHub Release criada com os quatro assets.
- Atualizador encontra a Release e valida APK/manifesto.
- Instalação no dispositivo confirma atualização sem perder dados.
- Teste físico conclui 10 turnos alternados entre AI-01 e AI-02.

## Limites
- Nenhuma senha, token ou keystore é lido ou armazenado pelo aplicativo.
- A Release não é criada por CI de PR/push; somente pelo dispatch manual.
- A assinatura deve permanecer compatível com a instalação existente.
- AI-03 permanece desativada.
- Até haver evidência no dispositivo, a conversa real permanece BLOCKED, não PASS.
