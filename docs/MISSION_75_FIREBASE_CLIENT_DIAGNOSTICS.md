# Missão 75 — Diagnóstico Firebase no cliente Android

## Dez rodadas

1. **Baseline:** PR #73 confirmado como aberto, Draft e sem merge; HEAD base `f18c56e7cc5df7dff39a6fc016cf4dbdb3a25898`.
2. **Auditoria de autenticação:** revisado `FirebaseMessengerClient`; o app usa Anonymous Auth REST e guarda ID/refresh token em preferências privadas, sem Firebase SDK.
3. **Fronteira de segredo:** diagnóstico não lê, imprime, copia, exporta nem persiste tokens; UID completo também não aparece na interface/relatório.
4. **Contrato de identidade:** validação exige AI_ID configurado, UID autenticado atual e mapeamento `messenger/identities/<AI_ID>` coerente.
5. **Contrato de sala:** consulta somente leitura da conversa selecionada e exige que o AI_ID atual esteja em `members`.
6. **Resultado estruturado:** criado `FirebaseFirstContactDiagnostics`, com estados claros e sem incluir UID/token no resultado.
7. **Integração Android:** adicionado botão de diagnóstico Firebase no AI Messenger; exige selecionar conversa remota e executa chamadas em thread de background.
8. **Falha segura:** endpoint/credencial inválidos, identidade ausente, UID divergente, sala ausente ou membership ausente terminam em NO-GO com mensagem sanitizada.
9. **Testes unitários:** adicionados cinco testes para sucesso sem segredo, UID divergente, AI_ID incorreto, membership ausente e conversa ausente.
10. **Documentação e CI:** criado este relatório e workflow Android dedicado para testes unitários e montagem do APK debug.

## Como executar no cliente

1. Configure a conexão Firebase já provisionada no app (URL RTDB, AI_ID e Web API Key).
2. Abra uma conversa remota já criada e selecione-a.
3. Toque em **Diagnóstico de primeiro contato Firebase**.
4. Repita no segundo cliente, com outro AI_ID e outra sessão autenticada.

O diagnóstico é read-only. Não cria identidade, sala, membership, regra ou mensagem. O resultado PASS comprova apenas a sessão/identidade/sala daquele cliente no instante da consulta. Para provar comunicação AI-A↔AI-B, ainda é necessário executar o round-trip de texto da Missão 74 com duas sessões reais e ACK.

## Evidência e limites

- Testes unitários e build CI não equivalem a teste em dois aparelhos.
- Nenhum token é exibido ou exportado.
- Nenhum projeto Firebase é criado nem configurado remotamente.
- Sem envio de mensagem, sem alteração de regras, sem deploy, sem cobrança e sem merge.
- Áudio e WebRTC permanecem bloqueados até PASS de texto entre dois clientes reais.
