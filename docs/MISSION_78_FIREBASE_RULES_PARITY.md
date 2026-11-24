# Missão 78 — Paridade e segurança das Firebase Rules

## Dez rodadas
1. Baseline: PR #76 confirmado aberto, Draft, sem merge; CI do HTTP contract PASS.
2. Inventário: localizadas duas cópias de Security Rules, em `firebase/database.rules.json` e `config/firebase/database.rules.json`.
3. Divergência: constatado que os arquivos tinham políticas diferentes; a cópia de config não refletia os controles mais recentes do arquivo canônico.
4. Fonte única: `firebase/database.rules.json` definida como fonte canônica do repositório.
5. Sincronização: `config/firebase/database.rules.json` alinhada ao conteúdo canônico, sem publicar nada.
6. Paridade automatizada: criado teste que compara os dois JSONs integralmente.
7. Mensagens: adicionada verificação estática de autenticação, membership, escrita somente de novos registros e vínculo senderAiId.
8. ACK: adicionada verificação estática do vínculo do AI_ID autenticado à membership e valor booleano true.
9. Regressão: workflow executa testes de rules e os testes dos runners de primeiro contato.
10. Relatório: documentadas diferenças, limites e próximo gate operacional.

## Resultado e limites
A paridade entre os dois arquivos do repositório pode ser testada em CI. Os testes são estáticos/contratuais, não executam Firebase Emulator nem provam comportamento de rules publicadas. Nenhuma regra foi publicada em projeto remoto; nenhum projeto ou recurso foi criado; nenhum token foi usado; nenhum aparelho enviou mensagem. O round-trip real segue BLOCKED até configuração e execução autorizadas.
