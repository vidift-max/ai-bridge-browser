# Missão 201 — progresso visível do download de atualização

## Objetivo
Melhorar a experiência da Central de Atualizações para que o usuário veja o progresso do download no próprio aplicativo. Escopo operacional permanece limitado a AI-01 e AI-02. Nenhuma release ou instalação é publicada nesta missão.

## Rodadas (10/10)

| Rodada | Trabalho | Resultado |
|---|---|---|
| 01/10 | Revalidar PR #202 e auditoria M200 antes de alterar o updater. | PASS — M199 continua como base aberta; implementação analisada no HEAD `7476d9e`. |
| 02/10 | Inspecionar ciclo da tela Atualizações, estados busy e botões. | PASS — tela já oferece consulta e download; barra estava indeterminada durante toda transferência. |
| 03/10 | Implementar barra de progresso determinada quando Content-Length é conhecido. | PASS em código — progresso de 0 a 100% atualizado na thread principal. |
| 04/10 | Preservar comportamento indeterminado quando servidor não informa tamanho. | PASS em código — não inventa percentual quando Content-Length é desconhecido/inválido. |
| 05/10 | Preservar limites e integridade do download. | PASS em código — mantém limite de 250 MiB, valida tamanho declarado, sincroniza arquivo e remove parcial em falha. |
| 06/10 | Extrair cálculo de progresso para política Java pura. | PASS — `DownloadProgressPolicy` rejeita valores impossíveis, tamanho excedido e comprimentos inválidos. |
| 07/10 | Adicionar testes unitários da política de progresso. | PASS em código — testes cobrem 0%, 25%, 100%, tamanho desconhecido, negativos, excesso e tamanho máximo. Execução depende do CI desta branch. |
| 08/10 | Corrigir filtros do workflow Android para branch M201 e PR com base M199. | PASS — push M201 e pull_request base M199 adicionados. |
| 09/10 | Auditar estado de assinatura e publicação. | BLOCKED — release final continua manual; não há release pública, assinatura de produção configurada ou teste físico. |
| 10/10 | Registrar evidências, abrir PR Draft e conferir estado final. | PASS — PR #204 aberta, não mesclada; CI precisa terminar no HEAD final. |

## Alterações
- `UpdateCenterActivity.java`: barra mostra percentual durante download quando o tamanho é conhecido; exibe estado indeterminado quando não é.
- `DownloadProgressPolicy.java`: cálculo puro de percentual, fail-closed para valores inválidos.
- `DownloadProgressPolicyTest.java`: testes JVM da política.
- `.github/workflows/android-build.yml`: filtros para acionar CI na branch M201 e em PR cuja base é M199.

## Limites conhecidos
- Esta mudança não implementa pausa/retomada de download.
- Histórico de versões ainda não foi implementado.
- A publicação de uma release estável assinada não foi feita.
- O APK ainda não foi instalado/testado em aparelho físico.
- A autenticação Google/ChatGPT não foi alterada nesta missão.
- Não houve merge, publicação, deploy, criação de credenciais ou instalação.

## Critério de conclusão
O progresso visível foi implementado no código. A aprovação de build/testes só será declarada após workflow executado no HEAD final da M201. O recurso não deve ser considerado pronto para distribuição até assinatura, release e teste físico.
