# M244 — Conclusão do CI e teste isolado de continuidade da assinatura

## Objetivo

Concluir as pendências verificáveis da M243, tornar a comparação de signatários do atualizador testável por JVM e registrar os gates que ainda impedem uma atualização física segura.

## Evidências revalidadas

- Repositório: `vidift-max/ai-bridge-browser`.
- Branch de trabalho: `feat/mission-241-updater-backport-v2-saas-alpha`.
- Branch principal: `v2-saas-alpha`, SHA `183a478681a3607f8e6612e4d68ab37583a6a5f3`.
- PR #234: aberta, Draft, mergeable, não mergeada.
- A branch tinha 5 commits à frente e 0 atrás antes das alterações M244.
- CI M243: run `45799623806`, SHA `9e1035f496d2faef205b18bf82051e0ed04b3439`, conclusão SUCCESS. O job `debug-build` passou; `release-final` foi SKIPPED, como esperado para evento pull_request.
- Releases oficiais: nenhuma publicada na última consulta.

## Alteração M244

A comparação de assinaturas foi extraída de `UpdateCenterActivity` para a classe pura `SigningCertificatePolicy`.

Contrato:
- exige conjuntos não nulos, não vazios e com a mesma quantidade de signatários;
- compara os bytes exatos de cada certificado;
- não depende da ordem dos signatários;
- faz correspondência um-a-um, sem reutilizar um signatário para satisfazer entradas duplicadas;
- rejeita entradas nulas ou vazias;
- mantém a postura conservadora: qualquer divergência bloqueia a atualização.

A atividade Android converte os objetos `Signature` em bytes e delega a comparação à política. O comportamento permanece de correspondência exata; não foi introduzida aceitação automática de rotação de chave.

## Testes adicionados

`SigningCertificatePolicyTest` cobre:
1. signatário idêntico;
2. mesma coleção em ordem diferente;
3. bytes diferentes;
4. signatário ausente ou adicional;
5. arrays/entradas nulas ou vazias;
6. correspondência um-a-um com entradas repetidas.

O CI da PR executa `gradle :app:testDebugUnitTest`, testes Python e `gradle :app:assembleDebug`. A execução do novo SHA deve ser verificada antes de marcar o código como CI PASS.

## Segurança e limites

- O workflow `release-final` só roda por `workflow_dispatch` na branch padrão `v2-saas-alpha`.
- Exige os quatro Secrets de assinatura e a variável `AI_PHONE_EXPECTED_SIGNING_CERT_SHA256`.
- O workflow compara o certificado do APK Release com o fingerprint esperado antes de publicar.
- Nenhum Secret foi lido, alterado ou transmitido.
- Nenhuma chave privada foi criada.
- Nenhuma Release foi publicada.
- Nenhum APK foi instalado e nenhum dado do aparelho foi alterado.
- O certificado do aplicativo fisicamente instalado ainda não foi obtido. O procedimento ADB/apksigner da M243 permanece pendente de execução no dispositivo.
- Não desinstalar o app, não limpar dados e não tentar contornar incompatibilidade de assinatura.

## Critério de saída

M244 pode ser considerada PASS para implementação e testes automatizados somente após o CI do SHA final concluir SUCCESS. A atualização física permanece BLOCKED até identificar o certificado real instalado e produzir uma Release assinada pelo mesmo certificado. PR aberta/Draft não equivale a merge ou publicação.
