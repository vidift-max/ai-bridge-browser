# Missão 192 — AI Messenger: segurança e contrato do link de convite

## Objetivo

Endurecer a criação e o resgate de convites do AI Messenger sem afirmar que o compartilhamento HTTPS universal já está pronto. Esta missão não substitui a prioridade principal do AI Bridge Browser: duas contas diferentes do ChatGPT, AI-01 e AI-02, em perfis independentes.

## Restrições

- Sem implantação do Firebase, hospedagem, Render ou serviços pagos.
- Sem provisionar credenciais, criar sala real ou aceitar convite real.
- Sem publicar regras no Firebase.
- Sem login ou envio de mensagens reais.
- PR Draft, aberta e não mesclada.
- Não gerar um domínio `.web.app` por suposição: o repositório não comprova qual site Firebase Hosting está configurado.

## Rodadas 01–10

| Rodada | Trabalho verificável | Resultado |
|---|---|---|
| 01/10 | Fixar a base de trabalho na PR #193 / branch `feat/mission-191-chatgpt-separate-accounts`, HEAD `1cd0c50062a6057b188cc6db29d2c00d1f88ebf8`. | PASS |
| 02/10 | Comparar o formato gerado pelo Firebase client com `InviteLinkParser` e os filtros do Manifest. | PASS — `aibridge://invite/{conversationId}/{token}` é reconhecido pelo caminho nativo. |
| 03/10 | Separar link nativo de HTTPS App Link. | PASS — parser aceita `https://<site>.web.app/i/{id}/{token}`, mas o gerador não o produz. |
| 04/10 | Verificar infraestrutura de hosting e domínio público. | BLOCKED — não há configuração de Firebase Hosting/site/assetlinks comprovada nesta base; não inventar URL HTTPS. |
| 05/10 | Auditar pré-condições de criação e autorização da sala. | PASS — encontrado risco: o cliente podia tentar criar convite para conversa que não fosse GROUP ou cujo owner não fosse a IA atual. |
| 06/10 | Auditar regras RTDB e fluxo de resgate. | PASS — identificado risco adicional: o marcador `invitesByAi` é escrito antes da validação final da sala; convites antigos sem metadado de tipo não devem avançar. |
| 07/10 | Adicionar validação local de tipo GROUP e owner antes de gerar token. | PASS em código — `MessengerRemoteConfig.validateGroupInviteOwner` e chamada prévia a `getConversation`. |
| 08/10 | Vincular o convite ao tipo GROUP e validar antes de gravar `invitesByAi`. | PASS em código — registro passa a conter `conversationKind: GROUP`; convites antigos sem esse campo são recusados. |
| 09/10 | Reforçar regras Firebase e testes unitários da política de owner/tipo. | PASS em código — regra exige conversa GROUP e metadado GROUP; testes positivos e negativos adicionados. |
| 10/10 | Registrar evidências, limites e gate de aceitação. | PASS documental / BLOCKED operacional — ainda faltam CI no HEAD final, Firebase Emulator/rules test e teste real entre dois aparelhos. |

## Alterações propostas

- `MessengerRemoteConfig.java`: valida que a conversa seja GROUP e que a IA atual seja a owner.
- `FirebaseMessengerClient.java`: lê a conversa antes de criar convite; inclui `conversationKind=GROUP`; recusa resgate de convite sem esse metadado antes de criar o marcador de pré-autorização.
- `firebase/database.rules.json`: exige que a conversa de origem seja GROUP e que o novo registro declare `conversationKind=GROUP`.
- `MessengerRemoteConfigTest.java`: adiciona casos de sucesso para owner correto e rejeição de conversa PRIVATE / owner diferente.

## Evidência de commits

- `597401411934d0bf5f65ded9e03184372304e9d7` — política de owner/tipo.
- `865f4da0596899bc3fae69efe9c8bd4ebf02bc36` — testes unitários.
- `fc2500cece3d29f0cc09af335c25a1a9bbe5e3ec` — validação de sala antes de criar convite.
- `42a02039ab22b8215bc4e4dfbc5559ddc49f91d7` — regra RTDB group-only.
- `3dc1a7eb87131e52475021a6326188fd92322ce1` — metadado GROUP e validação antecipada no resgate.
- `de230a4bf194e23049768adb358a523decb6ba3c` — validação do metadado nas regras RTDB.

## Limite do link nesta missão

O link atualmente gerado continua sendo o esquema nativo `aibridge://`. Ele é destinado a dispositivos Android com o AI Bridge Browser instalado e registrado para esse esquema. O parser também aceita HTTPS `/i/`, mas não há site Firebase Hosting e domínio comprovados para gerar um link HTTPS real. Portanto, esta missão não declara convites universais por navegador como prontos.

## Critérios pendentes

- [ ] Executar testes Android/Java no HEAD final e registrar o run/job.
- [ ] Validar as regras com Firebase Emulator Suite, incluindo tentativa de convite para PRIVATE e owner não autorizado.
- [ ] Publicar as regras somente após autorização explícita e confirmação do projeto Firebase correto.
- [ ] Testar criação e resgate em dois aparelhos com identidades distintas.
- [ ] Confirmar expiração, convite inválido, sala lotada e reentrada idempotente.
- [ ] Configurar e verificar um domínio HTTPS real + Android App Links antes de gerar link público.

## Conclusão

**Missão 192: PASS para endurecimento de código e contrato; BLOCKED para implantação e funcionamento real.** O link nativo é compatível com o parser e o Manifest em código, mas exige o aplicativo instalado. A missão fecha um risco de segurança na criação/resgate de convites e deixa explícito o trabalho restante para links HTTPS. Não houve deploy, publicação de regras, autenticação, convite real, nem troca de mensagens.

A prioridade de duas contas ChatGPT independentes permanece separada: esta missão não comprova isolamento de perfis nem comunicação AI-01 ↔ AI-02.
