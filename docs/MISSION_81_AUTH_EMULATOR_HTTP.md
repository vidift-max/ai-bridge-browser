# Missão 81 — Firebase Auth Emulator + RTDB HTTP round trip

## Dez rodadas
1. Confirmação do baseline: Missão 80 no commit be5f133a7f16cd8aea150bb471ed1d7061b12694.
2. Confirmação de CI: workflows de push e pull_request da Missão 80 concluíram SUCCESS.
3. Configuração local do Auth Emulator na porta 9099 e RTDB Emulator na porta 9000.
4. Criação de três identidades efêmeras pelo endpoint REST do Auth Emulator; tokens permanecem apenas em memória.
5. Provisionamento de fixture isolada no RTDB Emulator via contexto de teste com regras desabilitadas, sem tocar em Firebase externo.
6. Verificação HTTP de identidade e membership com ID tokens emitidos pelo Auth Emulator.
7. Envio de mensagem AI-01→AI-02 via REST POST autenticado e leitura por AI-02 via REST GET.
8. Confirmação de ACK: AI-02 grava via REST PUT e AI-01 verifica via REST GET.
9. Testes negativos HTTP: membro não endereçado não consegue ACK; destinatário fora da sala é rejeitado; não membro não lê conversa.
10. CI dedicado executa Auth + Database Emulator, testes REST e regressões anteriores.

## Limites de evidência
O teste usa tokens efêmeros do Firebase Authentication Emulator e chamadas HTTP reais aos emuladores locais. Não usa credenciais de produção, não publica regras, não cria projeto Firebase remoto e não prova comunicação em aparelhos físicos. O nonce e o ACK são locais ao ambiente efêmero do CI.

## Estado
Implementação registrada em PR Draft; aguardar CI final para declarar PASS de validação.
