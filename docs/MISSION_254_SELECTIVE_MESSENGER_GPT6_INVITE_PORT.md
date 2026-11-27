# M254 — PORT SELETIVO MESSENGER/GPT-6/CONVITES

Data: 2026-11-26
Branch: feat/mission-241-updater-backport-v2-saas-alpha
PR: #234
Escopo: AI-01 / AI-02
AI-03: desativada

## Decisão

**PASS** para recuperar componentes sem dependências externas complexas.
**NO-GO** para copiar Activities históricas que dependem de APIs inexistentes na branch atual.
**BLOCKED** para declarar GPT-6/convites remotos funcionais até haver implementação compatível e testes.

## 10 rodadas

### 01/10 — Revisão da origem histórica
Revisada a implementação histórica de `Gpt6Activity`, `MessengerInviteActivity`, `CollectiveRoomActivity` e `CollectiveRoomActivityV2`.

Resultado: a origem histórica é real e recuperável, mas cada Activity possui um grafo de dependências diferente.

**PASS**

### 02/10 — Compatibilidade de Gpt6Activity
A Activity histórica chama:
- `MessengerHttpClient.getGpt6Status()`
- `MessengerHttpClient.sendToGpt6(...)`

Esses métodos não existem na implementação atual de `MessengerHttpClient`.

Portanto, copiar `Gpt6Activity` diretamente produziria uma compilação quebrada.

**NO-GO — cópia direta.**

### 03/10 — Proteção contra código quebrado
Foi iniciado um port de `Gpt6Activity` apenas para verificar compatibilidade, mas a incompatibilidade foi detectada antes de aceitar o código.

O arquivo candidato foi removido e a entrada correspondente do Manifest foi revertida.

Não ficou código incompatível na branch.

**PASS**

### 04/10 — Auditoria do MessengerHttpClient atual
O cliente atual oferece:
- `getMyPhone()`
- criação de conversas
- envio de mensagens
- leitura de mensagens pendentes
- acknowledge
- validação de AI_ID/token
- transporte HTTPS autenticado.

Ele não implementa uma camada GPT-6.

**PASS — fronteira de responsabilidade preservada.**

### 05/10 — Auditoria do InviteLinkParser histórico
`InviteLinkParser` é autocontido e usa apenas `java.net.URI` e `Locale`.

As validações incluem:
- rejeição de espaços externos;
- rejeição de URI opaca;
- rejeição de userinfo/porta/query/fragment;
- suporte a `aibridge://invite/...`;
- suporte a HTTPS `*.web.app/i/...`;
- conversation ID de 1–128 caracteres;
- token de 20–64 caracteres.

**PASS — candidato seguro para port seletivo.**

### 06/10 — Port efetivo
Recuperado para a branch atual:

`app/src/main/java/com/vidiftmax/aibridgebrowser/InviteLinkParser.java`

Commit:
`e63be1a325ee462faef4f6b99bf811be118f269f`

Esse componente não foi registrado no Manifest porque é parser interno, não Activity exportada.

**PASS**

### 07/10 — Manifest
Nenhuma Activity histórica foi adicionada ao Manifest nesta rodada.

Motivo: `MessengerInviteActivity` depende de `CollectiveRoomActivityV2` e de transporte remoto; adicionar somente a Activity criaria uma superfície declarada sem grafo funcional completo.

**PASS — Manifest mínimo.**

### 08/10 — GPT-6
Não foi criada uma nova API fictícia para satisfazer a Activity histórica.

Próximo passo correto é definir/recuperar a interface GPT-6 compatível com o servidor atual antes de portar a UI.

Nenhuma chamada OpenAI, Secret ou serviço externo foi executada.

**BLOCKED — integração GPT-6.**

### 09/10 — Próximo lote
O próximo lote deve ser o grafo de convite/room remoto somente depois de confirmar:
1. contrato atual do backend para redeem de convite;
2. transporte Firebase ou HTTPS escolhido;
3. classes remotas necessárias;
4. limite de 20 participantes;
5. testes JVM para o parser.

WebRTC continua separado e não deve ser puxado junto neste lote.

**PASS — plano incremental.**

### 10/10 — Veredito
**PASS:** port seletivo começou sem importar árvore histórica inteira.

**PASS:** primeiro componente autocontido recuperado.

**PASS:** tentativa de port incompatível foi detectada e revertida antes de deixar código quebrado.

**NO-GO:** Activities históricas não devem ser copiadas isoladamente.

**BLOCKED:** GPT-6 remoto e sala de convite ainda precisam de contrato/implementação compatível.

## Estado operacional

- Nenhum merge.
- Nenhum Release.
- Nenhuma instalação.
- Nenhum Secret/Variable alterado.
- Nenhum workflow_dispatch.
- AI-03 continua desativada.

## Próxima missão — M255

Continuar pelo **grafo de convite remoto**, começando pelas interfaces e contratos que já existem na branch atual. Somente adicionar componentes quando suas dependências forem comprovadamente compatíveis.
