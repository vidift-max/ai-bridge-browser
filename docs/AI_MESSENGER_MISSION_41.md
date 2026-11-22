# AI Messenger — Missão 41: preparação de staging para duas IAs

## Objetivo

Preparar um caminho seguro para validar o Messenger com duas identidades provisionadas, sem publicar serviço, expor credenciais ou presumir que serviços de outro projeto sejam o backend do Messenger.

## Auditoria de infraestrutura (somente leitura)

- O repositório contém `render.yaml` com o serviço experimental `ai-messenger-experimental`, mas o próprio arquivo declara que é preparação e não deploy.
- O Blueprint define `MESSENGER_TOKEN_AI_A`, `MESSENGER_TOKEN_AI_B`, `MESSENGER_AI_ID_A` e `MESSENGER_AI_ID_B` como valores manuais, sem valores versionados.
- O caminho SQLite configurado é `server/data/messenger.sqlite`; o Blueprint não declara disco persistente nem banco gerenciado.
- A listagem dos serviços Render nos workspaces acessíveis não mostrou um serviço chamado `ai-messenger-experimental` nem outro serviço ligado ao repositório `ai-bridge-browser`. Há serviços do projeto AI-PHONE-02 em outro repositório, mas eles não foram tratados como endpoint do AI Messenger.
- Nenhum valor secreto foi lido, alterado ou exposto. Nenhum serviço foi criado, aprovado, implantado ou reiniciado.

## Correções nesta missão

- `RuntimeConfig.auth_tokens()` agora rejeita tokens duplicados, AI_IDs duplicados e AI_IDs malformados.
- `/readyz` usa a validação completa de `auth_tokens()`; configuração com duas identidades iguais não pode ser declarada pronta.
- Testes cobrem os limites de configuração e a resposta HTTP 503 de readiness quando os dois tokens são iguais.

## Bloqueios para staging real

1. Criar/revisar o serviço Render do Messenger e aprovar explicitamente o deploy.
2. Definir armazenamento persistente apropriado. O Blueprint atual não configura disco persistente nem banco gerenciado; não considerar o caminho SQLite no filesystem efêmero como armazenamento durável de produção.
3. Definir e inserir manualmente dois segredos distintos e seus AI_IDs autorizados, sem colocá-los no Git ou no relatório.
4. Confirmar URL HTTPS de staging, health/readiness e TLS.
5. Configurar a aplicação Android A e B com seus próprios AI_IDs e tokens; executar envio, polling, ACK e teste de rede cruzada.
6. Revogar credenciais de teste após a validação.

## Critério de aceite

- Backend Test e Android Build SUCCESS no mesmo HEAD.
- `/healthz` responde 200 e `/readyz` responde 200 somente quando as quatro variáveis necessárias são válidas, os dois tokens e os dois AI_IDs são distintos e o storage está acessível.
- Teste de duas identidades no staging HTTPS, sem registrar tokens em logs.
- Teste físico/rede cruzada separado do CI.

## Estado

**BLOCKED para comunicação entre duas IAs reais.** A validação local do protocolo está automatizada, mas não existe evidência de serviço Messenger publicado, armazenamento persistente hospedado, duas credenciais reais provisionadas ou dispositivos conectados.

Não foi feito deploy, merge, alteração de variáveis no Render, provisionamento de credenciais, instalação ou chamada de voz.
