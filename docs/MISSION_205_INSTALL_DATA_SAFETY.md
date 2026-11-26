# Missão 205 — segurança da instalação e preservação de dados

## Objetivo
Revalidar o artefato imediatamente antes de entregá-lo ao instalador Android, limitar o compartilhamento do FileProvider à pasta de atualizações e explicitar a condição de identidade necessária para atualizar sem desinstalar o aplicativo.

## 10 rodadas
| Rodada | Trabalho | Resultado |
|---|---|---|
| 01/10 | Revalidar M204 e sua CI no HEAD final. | PASS — PR #207 aberta/Draft/não mesclada; CI do SHA `d5d5350`: debug-build SUCCESS, release-preparation SUCCESS, release-final SKIPPED. |
| 02/10 | Auditar o FileProvider e a pasta de APK. | PASS — encontrado compartilhamento mais amplo que o necessário dentro da pasta Download privada do app. |
| 03/10 | Restringir o FileProvider ao diretório `Download/updates/`. | PASS — somente o diretório usado pelo atualizador fica exposto pelo provider. |
| 04/10 | Revalidar o caminho e a identidade do arquivo ao clicar em instalar. | PASS — helper exige arquivo existente, não vazio, nome esperado, diretório privado canônico e igualdade com o candidato verificado. |
| 05/10 | Recalcular SHA-256 imediatamente antes de abrir o instalador. | PASS — a entrega é bloqueada se o arquivo mudou depois do download/verificação. |
| 06/10 | Revalidar pacote, versão e certificado antes da entrega. | PASS — validação de package/version/signing permanece obrigatória na segunda checagem. |
| 07/10 | Codificar a compatibilidade de identidade da instalação. | PASS — política exige mesmo application package e certificado correspondente; identidade diferente bloqueia a atualização. |
| 08/10 | Cobrir as políticas com testes JVM. | PASS em código — testes para caminho privado, arquivo vazio/ausente, nome incorreto, candidato diferente e identidade pacote/certificado. |
| 09/10 | Corrigir filtros duplicados e habilitar CI M205/PR sobre M204. | PASS em código — filtro push M204 duplicado removido; branch M205 e base M204 configuradas. |
| 10/10 | Registrar evidências e abrir PR Draft. | PENDENTE — CI final M205 precisa concluir; PR será mantida sem merge. |

## Preservação de dados: o que o código permite afirmar
- O atualizador chama o instalador Android para atualizar o pacote existente; não executa desinstalação prévia, limpeza de SharedPreferences, exclusão de bancos ou remoção de perfis.
- O `applicationId` continua `com.vidiftmax.aibridgebrowser`; a versão atual do projeto é `0.1.0` / versionCode `1` nesta base.
- A verificação de atualização exige que o APK recebido tenha o mesmo package name e o certificado da instalação atual. Essa é a condição de compatibilidade necessária para o Android aceitar uma atualização normal do pacote e preservar o armazenamento privado.
- A persistência das abas e do estado da Central de Controle continua em SharedPreferences no armazenamento privado do app; a atividade principal mantém rotinas de persistência/restauração.
- Isto é uma garantia condicional do fluxo de atualização padrão do Android, não um teste físico. A preservação real de cookies WebView, contas e dados após atualizar precisa ser validada num dispositivo com APKs Release assinados pela mesma chave.

## Limites
- Nenhuma chave de assinatura foi criada, lida ou alterada.
- Nenhum APK Release final foi publicado ou instalado.
- Não há prova de atualização física nem de restauração de contas/cookies em aparelho.
- O Android ainda pode solicitar autorização para instalar apps desconhecidos e confirmação do usuário.
- PR Draft, sem merge ou publicação.
