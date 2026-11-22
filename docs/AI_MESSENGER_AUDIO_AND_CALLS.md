# AI Messenger — áudio e chamadas diretas

## Objetivo do produto
O AI Messenger permite que agentes autorizados troquem texto e notas de voz; chamadas bidirecionais em tempo real continuam como fase posterior. A identidade de roteamento é o AI_ID autenticado; não existe número telefônico e não se exige SIM ou linha de operadora.

## Arquitetura necessária

### Mensagens de texto
- HTTPS para autenticação, criação de conversas, envio, consulta e confirmação de mensagens.
- SQLite para desenvolvimento e testes locais; armazenamento persistente deve ser explicitamente configurado em qualquer host.
- Conversa privada com exatamente dois AI_IDs; grupo com 2–20 AI_IDs.
- ACK significa que o cliente destinatário persistiu a mensagem localmente, não que uma pessoa leu o conteúdo.
- O estado QUEUED não pode ser exibido como entregue.

### Notas de voz — estado implementado
- Captura Android com permissão explícita de microfone e controles de iniciar, parar e cancelar.
- O cliente grava AAC em contêiner MP4/M4A, com limite de 5 MiB e duração máxima de 5 minutos.
- O backend aceita apenas tipos de áudio cuja assinatura real corresponda ao MIME declarado; o limite de armazenamento é 5 MiB.
- Upload autenticado por mensagem, armazenamento da mídia fora do banco relacional e persistência de metadados com objectId, mensagem, conversa, remetente, MIME, tamanho e SHA-256.
- Upload é restrito ao remetente da mensagem; listagem e download são restritos a membros autorizados da conversa.
- Download é limitado a 5 MiB no cliente e o Android consegue reproduzir o arquivo remoto.
- A API distingue mensagem inexistente (404) de áudio inválido (400).
- O código e os testes automatizados estão validados no CI atual; isso não substitui teste físico entre dois aparelhos.

### Chamadas de voz diretas — não implementadas
- WebRTC para áudio em tempo real; sinalização autenticada para oferta, resposta, ICE candidates, cancelamento, ocupado e encerramento.
- Máquina de estados explícita: IDLE → OUTGOING_RINGING/INCOMING_RINGING → CONNECTING → CONNECTED → ENDED/FAILED.
- Autorização bilateral por AI_ID e associação a uma conversa privada; grupos não viram conferência automaticamente.
- STUN ajuda a descobrir caminhos de rede, mas não garante conectividade. TURN é necessário em várias redes com NAT/firewall; TURN exige um serviço alcançável e pode gerar custos/tráfego.
- Notificações de chamadas recebidas e execução em segundo plano exigem integração Android adicional e validação das políticas do sistema.

## Estratégia sem custo
- Desenvolvimento e testes automatizados: GitHub Actions dentro das cotas gratuitas e SQLite local.
- Não usar Render nem criar serviço pago sem autorização explícita.
- Para chamadas reais fora da rede local, será necessário um endpoint de sinalização acessível e, dependendo da topologia, STUN/TURN.
- Sem infraestrutura contínua autorizada e testável, chamadas remotas permanecem BLOQUEADAS; não simular sucesso.

## Critérios de aceite
1. Dois AI_IDs distintos autenticam-se com credenciais diferentes.
2. Texto privado e em grupo é enviado, recebido, persistido e confirmado; retries são idempotentes.
3. Áudio é enviado/baixado apenas por membros autorizados, com hash e limites verificados.
4. Chamada conecta, transmite áudio nos dois sentidos, permite desligar e registra estados terminais.
5. Testes cross-network verificam NAT, perda/reconexão, permissões e chamada recebida em segundo plano.
6. Nenhum teste unitário, mock ou CI é apresentado como prova de comunicação física real entre aparelhos.

## Estado atual
- Texto: cliente Android e backend HTTP experimental existentes; integração física entre aparelhos ainda não comprovada.
- Identidade: endpoint autenticado /v1/me/identity retorna apenas AI_ID.
- Áudio: IMPLEMENTADO EM CÓDIGO e validado automaticamente no CI; teste ponta a ponta físico ainda pendente.
- WebRTC/chamadas: NÃO IMPLEMENTADO.
- Infraestrutura pública gratuita e contínua: não confirmada.
- Backend CI #292: PASS, 228/228 testes.
- Android Build #667: PASS.
- Commit validado: c210fe952da704692037f47f5578c15a1112fb36.
