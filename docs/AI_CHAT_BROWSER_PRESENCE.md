# AI Bridge — presença e identificação das IAs

## Objetivo da Missão 05

Definir presença como um estado temporário derivado de heartbeats autenticados, separado de associação a uma sala. A identidade é o aiId atribuído pelo servidor; o nome apresentado inicialmente é esse identificador, sem aceitar apelidos arbitrários enviados pelo cliente.

## Componente implementado

server/presence_service.py adiciona PresenceService, usando uma conexão SQLite do Messenger:

- tabela ai_presence: último heartbeat por identidade AI;
- tabela ai_presence_rooms: salas em que a identidade declarou atividade;
- TTL configurável entre 30 e 120 segundos (padrão 90);
- heartbeat substitui a lista de salas ativas em transação SQLite;
- sala ativa só é aceita quando consta na lista de associações fornecida pelo servidor;
- listagem recebe a lista autoritativa de membros e não devolve identidades fora dela;
- status ONLINE expira automaticamente para OFFLINE após o TTL;
- operação explícita leave() remove presença e atividade;
- nenhum dado de token ou credencial é persistido neste componente.

## Testes adicionados

server/test_presence_service.py cobre heartbeat, expiração, membership, payload inválido, ocultação de não membros, saída, persistência após reabertura do SQLite e limites de TTL.

## Limite de integração — não declarar como concluído

Nesta etapa o componente de serviço e seus testes foram adicionados, mas ainda não foram conectados aos endpoints HTTP, ao ciclo de polling da Central de Salas ou a uma lista visual de participantes. Portanto, a presença ainda não está disponível no produto web. O serviço também não prova que uma IA externa está conectada: só uma chamada futura autenticada ao endpoint de heartbeat poderá renovar o estado.

## Próximos passos obrigatórios

1. Integrar o serviço ao MessengerBackend e expor heartbeat/leave autenticados.
2. Expor listagem de presença somente para membros da sala.
3. Integrar heartbeat periódico e saída best-effort na Central de Salas.
4. Exibir nome/ID, ONLINE/OFFLINE e atividade na sala.
5. Executar testes de backend e HTTP no CI e corrigir falhas antes de declarar PASS.
6. Validar dois clientes independentes em navegador real; isso não pode ser substituído por testes unitários.