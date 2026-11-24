# Missão 74 — Firebase First Contact Runner

## Dez rodadas completas

1. **Baseline:** PR #72 confirmado aberto, Draft e sem merge; branch de trabalho parte do HEAD final da Missão 73.
2. **Transporte escolhido:** confirmada a arquitetura Firebase Realtime Database Spark + Anonymous Auth, sem Render. Firebase atua como relay/rendezvous de texto e sinalização, não como telefonia.
3. **Identidades:** revisados os caminhos `messenger/identities` e `identitiesByUid`; o UID autenticado precisa corresponder ao AI_ID provisionado. Dois tokens/UIDs distintos são obrigatórios.
4. **Sala privada:** analisadas as Security Rules; o teste exige que AI-01 e AI-02 sejam membros autorizados da mesma conversa.
5. **Contrato de mensagem:** verificado o esquema RTDB `senderAiId`, `recipientAiIds`, `body`, `messageKind` e timestamp; o remetente é conferido contra a identidade vinculada ao UID.
6. **Confirmação de recebimento:** verificado o caminho de ACK por mensagem e identidade destinatária. O runner só marca round-trip PASS depois de AI-B receber o nonce e AI-A ler o ACK.
7. **Runner de preflight:** criado `tools/firebase_first_contact_smoke.py`, que valida URL Firebase HTTPS, IDs distintos, mapeamentos de UID e associação à conversa sem enviar mensagens por padrão.
8. **Runner de ida e volta:** adicionado modo opt-in `--send`, que envia uma única mensagem nonce, espera até 180 segundos pelo recebimento por AI-B, grava ACK como AI-B e verifica o ACK como AI-A.
9. **Proteção de credenciais e testes:** tokens são obtidos somente de variáveis de ambiente; não são impressos nem incluídos em URLs de diagnóstico/logs. Adicionados testes para configuração inválida, identidade duplicada, host não Firebase, membership e preflight sem envio.
10. **CI e roteiro de campo:** adicionado workflow de testes Python para o runner e documentação de configuração/execução com separação explícita entre preflight, round-trip remoto, áudio e chamada WebRTC.

## Execução local quando o projeto Firebase estiver provisionado

Variáveis necessárias:
- `MESSENGER_FIREBASE_DATABASE_URL`
- `MESSENGER_FIREBASE_AI_A_ID` e `MESSENGER_FIREBASE_AI_B_ID`
- `MESSENGER_FIREBASE_AI_A_ID_TOKEN` e `MESSENGER_FIREBASE_AI_B_ID_TOKEN` — tokens de sessão reais obtidos dos dois clientes autenticados, nunca tokens de admin.
- `MESSENGER_FIREBASE_CONVERSATION_ID`

Comandos:
- `python -m unittest server.test_firebase_first_contact_smoke -v`
- `python tools/firebase_first_contact_smoke.py` — apenas preflight, sem enviar.
- `python tools/firebase_first_contact_smoke.py --send` — envia uma mensagem de teste real e verifica recebimento/ACK.

Não colocar tokens em argumentos de linha de comando, arquivos versionados, screenshots ou relatórios. Injetá-los apenas no ambiente do processo local e limpar a sessão ao terminar. O runner não cria projeto, identidade, sala, regras ou deploy.

## Estado e fronteira de prova

- Runner e testes: implementados nesta branch; CI é a prova automatizada.
- Projeto Firebase real, Anonymous Auth, RTDB e Hosting: ainda dependem de criação/configuração pelo proprietário.
- Mapeamentos UID↔AI_ID e sala privada: precisam existir no projeto real.
- Preflight remoto: não executado por falta de configuração/credenciais reais.
- Texto entre dois clientes reais: não declarado PASS até executar `--send` com tokens dos dois clientes e observar ACK.
- Nota de voz e chamada WebRTC: fora do gate desta missão; continuam pendentes após o texto.
- Sem Render, sem projeto Firebase criado, sem deploy, sem cobrança e sem merge nesta missão.
