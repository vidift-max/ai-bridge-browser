# AI Messenger — roteiro de áudio e chamadas com custo zero

Status: planejamento técnico atualizado em 2026-11-21. Não representa implementação.

## Decisões do produto
- Não existe número telefônico, SIM, PSTN ou cobrança de operadora.
- Cada participante é identificado por AI_ID interno autenticado.
- O AI-PHONE usa Wi-Fi/internet autorizada.
- Texto, áudio gravado e chamada ao vivo são recursos diferentes e devem ter estados separados.
- Nenhum recurso pode ser anunciado como funcional antes de testes de ponta a ponta.

## Arquitetura por recurso

### 1. Texto
O protocolo HTTP autenticado atual já possui criação de conversas, envio, polling e ACK com persistência SQLite. A cobertura atual é de backend em testes locais; ainda não demonstra duas instalações Android reais conectadas pela internet.

### 2. Mensagem de áudio gravada
Fluxo necessário:
1. Android solicita permissão de microfone no momento em que a pessoa inicia a gravação.
2. Gravação local com duração e tamanho limitados, cancelamento e pré-visualização.
3. O app codifica metadados (formato, duração, tamanho, SHA-256) e envia o arquivo por HTTPS autenticado.
4. Servidor valida associação do remetente à conversa, MIME real, tamanho, hash e quota; armazena o objeto com identificador aleatório.
5. Mensagem aponta para o anexo; destinatário baixa com autorização e confirma recebimento.
6. App oferece reprodução local, exclusão e política de retenção.

Não usar Base64 em mensagens comuns para arquivos grandes. Não aceitar URL arbitrária como mídia. Não gravar em segundo plano nem iniciar microfone sem ação/consentimento explícito.

### 3. Chamada de voz ao vivo
- Android: permissão RECORD_AUDIO no momento apropriado, tela de chamada, toque, aceitar/recusar, silenciar, alto-falante, encerrar e ciclo de vida correto.
- Sinalização: sessão autenticada com estados RINGING, ACCEPTED, REJECTED, CANCELLED, CONNECTING, ACTIVE, RECONNECTING, ENDED, FAILED e EXPIRED.
- Mídia: WebRTC com DTLS-SRTP, ICE e negociação de codec.
- STUN ajuda a descobrir caminhos de rede; não é relay.
- TURN retransmite mídia quando NAT/firewall impede conexão direta. TURN consome banda e pode gerar custo.
- Se a IA/provedor só oferece texto, o app não deve fingir que há voz bidirecional. Síntese de voz não equivale a chamada viva.

## Estratégia gratuita realista
- Desenvolvimento, testes unitários e integração local: gratuitos com ferramentas locais e GitHub Actions dentro dos limites.
- Dois dispositivos na mesma rede local: podem validar um protótipo WebRTC ponto a ponto, desde que a rede permita.
- Redes diferentes: precisam de sinalização alcançável pela internet; conexões diretas podem funcionar em alguns NATs, mas não são garantidas.
- Redes restritivas podem exigir TURN. Não existe promessa honesta de chamada global confiável, sempre disponível e sem custo de infraestrutura.
- GitHub/GitHub Actions hospedam código e executam CI; não são servidor permanente de WebSocket, mídia ou TURN.
- Não usar Render nem criar recursos pagos. Não configurar serviços externos, contas, chaves ou despesas sem autorização explícita.
- Se não houver serviço gratuito confiável para a etapa, manter a etapa BLOCKED e continuar com protótipo/testes locais, sem simular disponibilidade.

## Critérios de aceite
- Áudio gravado: gravação, cancelamento, envio, autorização, download, integridade SHA-256, reprodução, limites e exclusão testados.
- Chamada: dois clientes Android, identidades diferentes, aceitar/recusar, estados corretos, áudio bidirecional, mute, troca Wi-Fi/dados, interrupção, recuperação e encerramento testados.
- Segurança: autorização por membro da conversa, rate limits, limites de duração/tamanho, proteção de credenciais e ausência de áudio capturado antes do aceite.
- Prova física: evidência dos dois dispositivos, versões do app, rede usada, logs redigidos e IDs de teste sem tokens.
- A chamada só é ACTIVE após mídia bidirecional confirmada; convite enviado ou ICE conectado isoladamente não prova que as duas pessoas se ouvem.

## Hardening recente do backend de texto

- Limitação deslizante por AI_ID aplicada às rotas de identidade, criação de conversa, envio, polling e ACK.
- O limitador em memória usa seção crítica para que requisições simultâneas no mesmo processo não ultrapassem o limite configurado.
- O estado do limitador é local ao processo: reinicia junto com o servidor e não é compartilhado entre múltiplas instâncias. Antes de escalar horizontalmente, será necessário um limitador compartilhado ou uma política explícita de afinidade.
- Payloads de mensagem validam tipos, campos vazios e lista de destinatários antes da autorização e persistência.
- Os testes automatizados cobrem isolamento por AI_ID, concorrência, destinatários inválidos, respostas HTTP 400 e 429. O resultado final do CI deste commit ainda precisa ser confirmado.

## Concorrência e robustez HTTP — hardening em andamento

- O servidor de desenvolvimento/execução usa ThreadingHTTPServer para atender mais de uma requisição ao mesmo tempo.
- O estado em memória do Messenger é protegido por RLock; envios idempotentes concorrentes no mesmo processo são serializados.
- O ciclo de vida das credenciais (autenticar, revogar, expirar e rotacionar) é sincronizado.
- O registro de auditoria protege gravação e leitura concorrentes.
- O endpoint ACK analisa o caminho sem confundir parâmetros de query com o ID da mensagem.
- JSON com bytes UTF-8 inválidos é rejeitado com HTTP 400, sem propagar exceção de decodificação.
- Essas garantias são por processo. SQLite continua sendo o armazenamento persistente; múltiplas instâncias independentes ainda exigem coordenação compartilhada e testes específicos.
- Os testes de concorrência e HTTP foram adicionados; aguardar CI para classificá-los como aprovados.

## Hardening adicional de autenticação e entrada HTTP

- A autenticação captura AI_ID e geração da credencial em uma única operação sincronizada; isso evita combinar a identidade obtida antes de uma rotação com a geração obtida depois dela.
- O parser JSON rejeita chaves duplicadas e constantes não padronizadas como NaN, evitando interpretações ambíguas entre clientes.
- A camada HTTP tem testes para Content-Type incorreto, JSON malformado, UTF-8 inválido, corpo acima do limite, cursores de polling inválidos e envios simultâneos idempotentes.
- O backend serializa o acesso à conexão SQLite compartilhada dentro de um processo. Não executar múltiplos processos independentes sobre o mesmo arquivo como se houvesse coordenação distribuída; essa topologia ainda exige desenho e testes próprios.
- Os testes novos foram adicionados e aguardam o resultado do CI deste HEAD.

## Estado atual verificado
- Texto: backend HTTP com persistência, testes de dois principais e ACK; sem prova de comunicação entre dois Android físicos.
- Áudio gravado: não implementado.
- Chamadas/WebRTC: especificação existente, runtime não implementado.
- Backend público 24/7: não existe nem foi provisionado.
- Wi-Fi e diagnóstico do aparelho: UI existente; teste físico pendente.
