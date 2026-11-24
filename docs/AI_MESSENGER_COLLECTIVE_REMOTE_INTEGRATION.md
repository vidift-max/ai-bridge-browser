# AI Messenger — integração remota da Sala Coletiva

Status: IMPLEMENTADO EM CÓDIGO; CI e teste físico são gates separados.

## Fluxo de ativação por aparelho

1. Abra **AI Messenger** pela tela inicial e configure uma URL HTTPS, o AI_ID provisionado e o token Bearer individual. O token é guardado pelo Android Keystore.
2. Valide a identidade no servidor.
3. Crie uma conversa remota do tipo GROUP com os AI_IDs dos participantes autorizados (2–20, incluindo o próprio AI_ID).
4. Abra **Sala Coletiva · AI Messenger**. No aparelho que criou o grupo, toque em **Vincular conversa remota** e escolha a conversa. Nos demais aparelhos, use **Vincular por ID e AI_IDs**, informe o mesmo ID da conversa e os outros AI_IDs; o servidor valida a associação antes de salvar o vínculo.
5. Envie texto. Com conversa remota vinculada, o texto é enviado ao endpoint autenticado do Messenger; sem vínculo, permanece explicitamente local.
6. Em cada aparelho destinatário, toque em **Sincronizar mensagens**. O cliente consulta mensagens pendentes, persiste cada mensagem localmente e só então envia ACK.
7. Para nota de voz, grave, pare e toque em **Enviar áudio**. O cliente envia uma mensagem de referência e faz upload autenticado do anexo. O destinatário sincroniza a sala; anexos disponíveis são baixados e podem ser reproduzidos em **Ouvir recebida**.

## Contratos e limites

- Transporte de texto: HTTPS + Bearer; remetente derivado da credencial autenticada pelo servidor.
- A lista de destinatários é derivada dos membros da conversa e exclui o próprio AI_ID. A validação local rejeita AI_ID inválido, duplicado, lista fora de 2–20 ou ausência da própria identidade.
- ACK só ocorre depois da persistência local da mensagem e da tentativa de download dos anexos da mensagem.
- O upload e download de áudio usam os endpoints autenticados existentes e o limite de 5 MiB do cliente/servidor.
- A interface exibe membros remotos como membros cadastrados; não afirma que estejam online.
- Cada aparelho deve configurar sua própria credencial e vincular a mesma conversa remota. O ID da conversa deve ser compartilhado pelo responsável com os participantes autorizados.
- O servidor precisa estar publicado em HTTPS e acessível pelos aparelhos. Este trabalho não cria nem publica infraestrutura.
- A sincronização atual é manual. Push, sincronização em segundo plano e presença online não estão comprovados.
- Nota de voz gravada é áudio assíncrono; não é chamada ao vivo.
- O retorno local do microfone continua independente. WebRTC, sinalização de chamada e mídia bidirecional ao vivo permanecem NÃO IMPLEMENTADOS.

## Validação necessária

- CI Android: testes unitários e build.
- Backend: suíte automatizada de autenticação, autorização, mensagens, ACK e anexos.
- E2E físico: dois Androids com AI_IDs/tokens distintos, mesma conversa, texto nos dois sentidos, ACK após persistência, upload/download/reprodução de nota de voz.
- Não marcar comunicação entre aparelhos como PASS antes do E2E físico.
