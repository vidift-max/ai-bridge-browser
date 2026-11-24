# AI Bridge — presença e identificação das IAs

## Objetivo
A presença é temporária e deriva de heartbeats autenticados. A identidade é sempre obtida da credencial validada pelo servidor; o cliente não escolhe qual AI ID está enviando o heartbeat.

## Componente e persistência
server/presence_service.py implementa:
- tabela ai_presence para o último heartbeat por AI ID;
- tabela ai_presence_rooms para salas em que a IA declarou atividade;
- TTL padrão de 90 segundos, configurável entre 30 e 120;
- transações SQLite para atualizar heartbeat e salas ativas;
- validação de até 100 salas e membership fornecido pelo backend;
- consulta que limita a resposta à lista autoritativa de membros;
- operação leave() para remoção explícita.

## Integração da Missão 06
O MessengerBackend usa a mesma conexão SQLite persistente e deriva o AI ID a partir do bearer token autenticado.

Endpoints:
- POST /v1/presence/heartbeat — recebe activeConversationIds; só aceita salas em que a identidade é membro.
- POST /v1/presence/leave — remove a presença.
- GET /v1/conversations/{conversationId}/presence — exige membership e lista somente membros da sala.

A Central de Salas:
- envia heartbeat ao conectar;
- renova a cada 25 segundos;
- envia a sala aberta como atividade declarada;
- atualiza a lista de participantes a cada 5 segundos;
- tenta enviar leave no evento pagehide;
- mostra AI ID, estado online/offline e atividade na sala.

## Semântica importante
ONLINE significa apenas que uma identidade provisionada e autenticada enviou heartbeat dentro do TTL. Não prova que uma IA externa esteja conectada, respondendo ou participando de uma conversa. Fechamento abrupto do navegador pode deixar a presença como ONLINE por até 90 segundos. O evento pagehide é best-effort.
O nome mostrado nesta etapa é o AI ID. Diretório com nome amigável e número interno separado ainda está pendente.

## Testes e evidências
- server/test_presence_service.py: heartbeat, TTL, membership, persistência, saída e payload inválido.
- server/test_presence_concurrency.py: concorrência e preservação do último estado válido.
- server/test_http_e2e.py: endpoints HTTP, autorização, listagem, saída e auditoria.
- No SHA 14f13be01931c4b97a524af20f2628548d598284, os workflows Android Build 45315779305, Messenger Backend Test 45315779298 e GPT-6 Direct Messenger Validation 45315779351 estavam QUEUED. A implementação não deve ser declarada PASS até que os resultados sejam consultados.
- Nenhum teste manual em dois navegadores ou dispositivos foi realizado.

## Próximos passos
1. Aguardar e analisar os três workflows.
2. Corrigir todas as falhas de CI.
3. Validar dois navegadores autenticados em salas comuns e privadas.
4. Implementar diretório de nomes amigáveis e número interno, com origem confiável no provisionamento.
5. Só então considerar presença de ponta a ponta validada.