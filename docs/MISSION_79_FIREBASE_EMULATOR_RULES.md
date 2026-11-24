# Missão 79 — Testes reais de Security Rules no Firebase Emulator

## Dez rodadas
1. Baseline: PR #77 Draft aberto, sem merge; CI anterior confirmado SUCCESS.
2. Auditoria: inspeção das regras identificou leitura permitida apenas em cada nó de mensagem, sem autorização explícita no nó de coleção `messages`.
3. Compatibilidade: o runner M74 consulta `/messages.json`; regras por filho não garantem leitura da coleção no Realtime Database.
4. Correção: adicionada regra `.read` no nó `messages`, restrita a usuários autenticados cuja identidade está na membership da conversa.
5. Paridade: atualização da cópia de deploy para manter igualdade com a regra canônica.
6. Harness: criado teste Node usando `@firebase/rules-unit-testing` contra Firebase Realtime Database Emulator.
7. Leitura: casos para AI-01 e AI-02 autorizados e terceiro AI não membro bloqueado.
8. Escrita: casos para remetente membro permitido, identidade falsificada e não membro bloqueados.
9. ACK: casos para destinatário permitido, remetente se passando pelo destinatário, não membro e valor inválido bloqueados.
10. CI: workflow instala versões fixadas, inicia o emulador e executa os testes de regras, paridade e regressões Python.

## Limites
O Emulator valida as regras versionadas localmente em CI, não prova que as mesmas regras estejam publicadas em um projeto Firebase real. Nenhum projeto externo, conta, credencial ou aparelho foi acessado. Nenhuma mensagem real foi enviada. Round-trip remoto permanece BLOCKED até provisionamento e execução autorizada.
