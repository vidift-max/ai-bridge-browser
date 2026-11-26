# M220 — Política estrita de handoff ao instalador Android

## Objetivo
Garantir que o APK verificado seja entregue ao Android por um URI content:// do FileProvider próprio, com MIME correto e somente permissão de leitura.

## Dez rodadas
1. Auditoria da criação do Intent ACTION_VIEW.
2. Confirmação do FileProvider não exportado e com concessão explícita de URI.
3. Confirmação do escopo de caminho privado Download/updates.
4. Definição de allowlist para autoridade do próprio pacote.
5. Exigência de URI content://, rejeitando file://.
6. Exigência de MIME application/vnd.android.package-archive.
7. Exigência de FLAG_GRANT_READ_URI_PERMISSION.
8. Rejeição de FLAG_GRANT_WRITE_URI_PERMISSION.
9. Testes para autoridade estrangeira, MIME incorreto, sufixos query/fragment e flags.
10. Integração no ponto imediatamente anterior a startActivity e documentação.

## Limites
A política controla o Intent emitido pelo app. A aceitação e instalação final continuam sob controle do Android e exigem confirmação do usuário. CI não substitui teste físico em dispositivos. Sem merge, Release, assinatura, alteração de Secrets, instalação física ou ativação de AI-03.
