# Missão 80 — Autorização de destinatários e ACK no Firebase RTDB

## Dez rodadas completas
1. Baseline: PR #78 (Missão 79) permanece Draft, aberto e sem merge; workflow no SHA c3b6e7448636217fe37155d3ebfae1621f091cef concluiu SUCCESS.
2. Auditoria das regras: envio era protegido por identidade do remetente e membership, mas a lista de destinatários não era validada no servidor.
3. Auditoria de ACK: qualquer membro podia gravar ACK no próprio AI-ID mesmo sem ser destinatário daquela mensagem.
4. Modelo de ameaça: cliente modificado poderia incluir AI externo à sala como destinatário; cliente membro poderia gerar ACK sem ter recebido a mensagem.
5. Correção de destinatários: cada chave em recipientAiIds deve ser true e corresponder a membro real da conversa.
6. Integridade de payload: mensagem deve conter pelo menos um destinatário, além dos campos obrigatórios existentes.
7. Correção de ACK: autorização exige identidade autenticada correspondente ao AI-ID, membership e presença do AI-ID na lista de destinatários da mensagem.
8. Testes negativos: incluídos destinatário não membro, mapa vazio, membro não endereçado e ACK para mensagem inexistente.
9. Paridade: as regras canônicas e a cópia de configuração/deploy são atualizadas com o mesmo conteúdo.
10. CI: workflow dedicado executa Firebase Realtime Database Emulator, casos de autorização e regressões Python.

## Limites
As regras e testes são versionados no repositório e validados no Emulator/CI. Isso não comprova publicação em Firebase real, provisionamento de identidades, tokens válidos, instalação em aparelhos ou round-trip remoto. Nenhuma mensagem externa foi enviada. PR Draft; sem merge ou deploy.
