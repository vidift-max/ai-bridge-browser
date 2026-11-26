# Missão 204 — recuperação segura de downloads do atualizador

## Objetivo
Impedir que um download interrompido ou incompleto seja confundido com APK pronto para instalação. O arquivo só recebe o nome final depois de passar por SHA-256, identidade do pacote, versão e certificado já instalado.

## 10 rodadas
| Rodada | Trabalho | Resultado |
|---|---|---|
| 01/10 | Revalidar a base M203 e o estado de CI. | PASS — PR #206 permanece aberta/Draft/não mesclada; no run observado, testes JVM e build Debug concluíram SUCCESS, preparação Release ainda executando. |
| 02/10 | Auditar o caminho e nome do APK baixado. | PASS — identificado que o download era gravado diretamente em `app-release.apk`, nome final também usado pelo instalador. |
| 03/10 | Separar arquivo parcial do artefato final. | PASS — download passa a usar `app-release.apk.part` dentro da pasta privada `updates` do aplicativo. |
| 04/10 | Restringir o caminho de trabalho à pasta privada esperada. | PASS — canonicalização da pasta e validação do diretório pai dos dois nomes de arquivo. |
| 05/10 | Remover resíduo parcial anterior antes de novo download. | PASS — falha ao remover o parcial antigo bloqueia o novo download; não tenta reaproveitá-lo. |
| 06/10 | Manter verificações antes da promoção. | PASS — SHA-256, packageName, versionCode/versionName e certificado são validados ainda no arquivo `.part`. |
| 07/10 | Promover somente arquivo integral e verificado. | PASS — arquivo final só é disponibilizado depois de validação; falha de renomeação bloqueia instalação. |
| 08/10 | Fortalecer regra de comprimento recebido. | PASS — nova política rejeita tamanho negativo, acima do limite, truncado ou maior que Content-Length; tamanho desconhecido continua aceito dentro do limite. |
| 09/10 | Adicionar testes JVM e filtro de CI. | PASS em código — 4 testes novos; workflow habilitado para push M204 e PR com base M203. |
| 10/10 | Registrar evidências e abrir PR Draft. | PENDENTE — CI M204 ainda precisa executar/concluir no HEAD final; PR não será mesclada. |

## Arquivos alterados
- `app/src/main/java/com/vidiftmax/aibridgebrowser/UpdateCenterActivity.java`
- `app/src/main/java/com/vidiftmax/aibridgebrowser/UpdaterDownloadPolicy.java`
- `app/src/test/java/com/vidiftmax/aibridgebrowser/UpdaterDownloadPolicyTest.java`
- `.github/workflows/android-build.yml`
- `docs/MISSION_204_ATOMIC_APK_DOWNLOAD.md`

## Limites
- Não implementa retomada por Range/ETag; cada tentativa recomeça do zero para evitar misturar bytes de downloads diferentes.
- Não publica APK, não assina release, não instala em aparelho e não altera dados de usuário.
- A promoção usa renomeação no mesmo diretório depois das verificações; não se afirma atomicidade de sistema de arquivos em todos os dispositivos Android.
- A CI da M203 estava parcialmente concluída no momento da auditoria: testes JVM e Debug SUCCESS; Release preparation ainda em execução. A CI desta missão deve ser confirmada no SHA final.
