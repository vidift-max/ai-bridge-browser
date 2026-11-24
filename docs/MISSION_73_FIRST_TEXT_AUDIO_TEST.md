# Missão 73 — Primeiro teste de comunicação por texto e áudio

## Objetivo
Preparar e executar a primeira validação de comunicação AI↔AI, separando provas automatizadas locais de prova real entre dois clientes/dispositivos. A missão cobre texto, nota de voz/anexo de áudio e chamada WebRTC 1:1.

## Dez rodadas completas

1. **Baseline GitHub:** verificado que o PR #71 (Missão 72) permanece aberto, Draft e sem merge; HEAD base `0c871f3c00587b86ab6ae521ba1b789aa40aee2c`. O workflow `45470076434` concluiu browser e backend com sucesso.
2. **Fluxo de texto:** auditados os endpoints autenticados de identidade, envio, inbox e ACK. O servidor associa o remetente ao principal autenticado; o remetente não escolhe livremente o próprio AI_ID.
3. **Prova automatizada de texto:** `server/test_authenticated_e2e.py` cobre AI-A→AI-B, recebimento pendente, ACK e reinício do backend com persistência SQLite. `server/test_http_e2e.py` cobre o fluxo HTTP de envio, leitura e ACK.
4. **Identidades e credenciais:** identificadas as configurações de staging `MESSENGER_TOKEN_AI_A`, `MESSENGER_TOKEN_AI_B`, `MESSENGER_AI_ID_A` e `MESSENGER_AI_ID_B`. Tokens são segredos de runtime; IDs são identificadores e não substituem autenticação.
5. **Áudio anexado:** auditados `AudioRecorder` e `AudioPlayback`: gravação AAC em M4A iniciada explicitamente, limite de 5 MiB e até 5 minutos; reprodução local com limpeza de recursos.
6. **Prova automatizada de áudio:** `server/test_http_e2e.py` contém upload/download autenticado, listagem restrita a membros, rejeição de remetente indevido e rejeição de conteúdo que não corresponde ao áudio declarado. `server/test_sqlite_audio_attachments.py` verifica metadados persistidos e migração.
7. **Chamada WebRTC no navegador:** auditado `web/webrtc-call.js` e seus testes. O fluxo exige contexto seguro, aceite explícito do destinatário e permissão de microfone; os testes usam PeerConnection e mídia simulados.
8. **Motor WebRTC Android e rede:** auditados `WebRtcVoiceEngine`, `VoiceCallSession` e a documentação ICE. O motor exige permissão RECORD_AUDIO e aceita configuração ICE injetada; não há servidor STUN/TURN provisionado por padrão.
9. **Ambiente real e limites:** verificados os documentos de staging/Firebase. Não há projeto Firebase real, credenciais provisionadas de Phone-01/Phone-02, domínio público ativo nem deployment Render autorizado. Nenhum segredo foi consultado ou registrado. Assim, não há endpoint de produção/staging comprovado para conectar dois clientes reais.
10. **Plano de execução e CI:** criado este relatório e workflow dedicado para regressão web, backend e build/teste Android. O roteiro de campo abaixo define a prova real sem simular resultados.

## Roteiro do primeiro teste real

### A. Texto — primeiro gate
1. Provisionar duas identidades distintas (AI-A e AI-B) e dois tokens independentes no ambiente real autorizado.
2. Abrir o mesmo endpoint HTTPS nos dois clientes, autenticar separadamente e confirmar que `/v1/me/identity` retorna IDs diferentes e esperados.
3. Enviar de A para B uma mensagem com nonce único; confirmar a presença no inbox de B, conteúdo e remetente autenticado.
4. Responder de B para A e confirmar o retorno.
5. Confirmar ACK após persistência do destinatário e que a mensagem não reaparece como pendente após reconexão.

**Aprovação:** mensagem de ida e volta observada nos dois clientes, IDs/horários/IDs de mensagem registrados e ACK confirmado. Não publicar tokens nos relatórios.

### B. Nota de voz — segundo gate
1. Em uma conversa privada autorizada, gravar uma nota curta (3–5 segundos) com consentimento de microfone.
2. Enviar o anexo e verificar metadados, tamanho e SHA-256 no retorno do servidor.
3. Baixar no outro cliente, reproduzir e confirmar áudio inteligível.
4. Confirmar que usuário não membro não consegue listar nem baixar o anexo.

**Aprovação:** áudio real gravado em um cliente e reproduzido no outro; não basta fixture binária ou teste unitário.

### C. Chamada ao vivo — gate separado
1. Fazer chamada privada 1:1 na mesma rede; o destinatário aceita manualmente e concede microfone.
2. Confirmar ICE CONNECTED/COMPLETED e áudio audível nos dois sentidos; testar mute e encerrar.
3. Só depois repetir em redes diferentes. Sem STUN/TURN alcançável e configurado, o teste cross-network permanece BLOQUEADO.

## Resultado e fronteira de evidência

- **Código/contratos:** presentes no repositório.
- **Testes automatizados:** workflow desta missão deve validar browser, backend e Android; mocks não provam mídia real.
- **Texto entre dois clientes reais:** BLOQUEADO até provisionamento de endpoint e duas credenciais/identidades válidas.
- **Nota de voz entre dois clientes reais:** BLOQUEADO pelo mesmo gate de ambiente.
- **Chamada WebRTC física:** BLOQUEADA até dois clientes reais, permissão de microfone, configuração ICE alcançável e teste de mídia bidirecional.
- **Deploy, criação de projeto Firebase, provisionamento de segredos e serviços pagos:** não realizados nem autorizados nesta missão.

O primeiro teste de campo começa pelo gate A. Não avançar para B/C se a autenticação e a troca de texto não forem comprovadas. Não declarar PASS físico com base apenas em CI.
