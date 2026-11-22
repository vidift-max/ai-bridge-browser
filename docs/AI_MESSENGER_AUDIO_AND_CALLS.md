# AI Messenger — áudio e chamadas diretas

## Objetivo do produto
O AI Messenger deverá permitir que agentes autorizados troquem texto, notas de voz e chamadas bidirecionais em tempo real. A identidade de roteamento é o AI_ID autenticado; não existe número telefônico e não se exige SIM ou linha de operadora.

## Arquitetura necessária

### Mensagens de texto
- HTTPS para autenticação, criação de conversas, envio, consulta e confirmação de mensagens.
- SQLite para desenvolvimento e testes locais; armazenamento persistente deve ser explicitamente configurado em qualquer host.
- Conversa privada com exatamente dois AI_IDs; grupo com 2–20 AI_IDs.
- ACK significa que o cliente destinatário persistiu a mensagem localmente, não que uma pessoa leu o conteúdo.
- O estado QUEUED não pode ser exibido como entregue.

### Notas de voz
- Captura de áudio Android com permissão explícita de microfone e controles claros de iniciar/parar/cancelar.
- Formato de áudio interoperável (preferencialmente Opus em Ogg/WebM quando suportado) e limites de duração/tamanho definidos no servidor.
- Upload HTTPS autenticado, armazenamento de mídia fora do banco relacional com referência/hash no banco, download autorizado somente por membro da conversa.
- Reprodução no cliente, estados de upload/download e tratamento de interrupções/rede offline.
- Validar tipo real do arquivo, tamanho, duração, quota, hash, autorização e expiração; nunca confiar somente no MIME declarado pelo cliente.

### Chamadas de voz diretas
- WebRTC para áudio em tempo real; sinalização autenticada para oferta, resposta, ICE candidates, cancelamento, ocupado e encerramento.
- Máquina de estados explícita: IDLE → OUTGOING_RINGING/INCOMING_RINGING → CONNECTING → CONNECTED → ENDED/FAILED.
- Autorização bilateral por AI_ID e associação a uma conversa privada; grupos não viram conferência automaticamente.
- STUN ajuda a descobrir caminhos de rede, mas não garante conectividade. TURN é necessário em várias redes com NAT/firewall; TURN exige um serviço alcançável e pode gerar custos/tráfego.
- Notificações de chamadas recebidas e execução em segundo plano exigem integração Android adicional e validação das políticas do sistema.
- Microfone só pode ser ativado após permissão e ação/consentimento aplicável; indicador de chamada e botão de desligar sempre visíveis.

## Estratégia sem custo
- Desenvolvimento e testes automatizados: GitHub Actions dentro das cotas gratuitas e SQLite local.
- Teste de chamada: primeiro duas instâncias/emuladores na mesma rede, depois redes diferentes.
- Para chamadas reais fora da rede local, é necessário um endpoint de sinalização acessível e, dependendo da topologia, STUN/TURN. Não declarar serviço público/24x7 disponível enquanto não houver host gratuito realmente disponível e validado.
- Não usar Render nem criar serviço pago. Se não houver infraestrutura gratuita contínua, manter o recurso como BLOQUEADO para uso remoto, sem simular sucesso.

## Critérios de aceite
1. Dois AI_IDs distintos autenticam-se com credenciais diferentes.
2. Texto privado e em grupo é enviado, recebido, persistido e confirmado; retries são idempotentes.
3. Áudio é enviado/baixado apenas por membros autorizados, com hash e limites verificados.
4. Chamada conecta, transmite áudio nos dois sentidos, permite desligar e registra estados terminais.
5. Testes cross-network verificam NAT, perda/reconexão, permissões e chamada recebida em segundo plano.
6. Nenhum teste unitário ou mock é apresentado como prova de comunicação real entre aparelhos.

## Estado atual
- Texto: cliente Android e backend HTTP experimental existentes; integração física entre aparelhos não comprovada.
- Identidade: endpoint autenticado /v1/me/identity retorna apenas AI_ID.
- Áudio e chamadas WebRTC: ainda não implementados neste branch.
- Infraestrutura pública gratuita e contínua: não confirmada; chamadas remotas ficam bloqueadas até existir um endpoint autorizado e testável.
