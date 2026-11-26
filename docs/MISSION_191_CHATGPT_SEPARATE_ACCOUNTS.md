# Missão 191 — Duas contas ChatGPT independentes: auditoria local-first

## Decisão de escopo

O AI-01 e o AI-02 devem usar **duas contas diferentes do ChatGPT**, cada uma autenticada em uma sessão de navegador independente. Duas conversas na mesma conta não satisfazem este requisito.

Restrições desta missão:
- Somente ChatGPT; sem Claude, Gemini ou outros provedores.
- Sem API paga, Render, hospedagem externa ou serviço com cobrança/expiração.
- Prioridade para comunicação local no próprio dispositivo.
- Não executar login, provisionar credenciais, enviar mensagens ou ativar automação em nome do operador.
- Nenhum teste simulado será descrito como conversa real entre modelos.
- Não considerar `tabId` ou `profileId` como prova de isolamento.

## Rodadas 01–10 — auditoria executada

| Rodada | Verificação realizada | Resultado |
|---|---|---|
| 01/10 | Identificação do baseline e dos arquivos relevantes na linha M189 | PASS — baseline fixado em `fd77a2ea040a5cd8e9320a0657fb163bc5baa138` |
| 02/10 | Inspeção da criação de WebViews e da ordem de `WebViewCompat.setProfile` | PASS — `MULTI_PROFILE` é verificado e `setProfile` ocorre antes de settings/clientes/navegação |
| 03/10 | Verificação da persistência de `profileId` e restauração de abas | PASS — IDs são persistidos/restaurados; isso não prova que os dados de sessão foram isolados |
| 04/10 | Verificação do estado visual quando o recurso não existe | PASS — a interface avisa que o perfil é compartilhado e que contas diferentes não devem ser usadas nessas abas |
| 05/10 | Verificação do estado quando perfis separados são atribuídos | PASS — a interface informa explicitamente que o teste real no dispositivo ainda está pendente |
| 06/10 | Inspeção da fila de mensagens por identidade de aba/perfil | PASS — a fila local existe e fica vinculada a `tabId + profileId` |
| 07/10 | Auditoria do ponto de entrega ao ChatGPT | BLOCKED — `deliverPendingMessages()` para deliberadamente antes de injetar texto ou enviar |
| 08/10 | Busca por captura automática da resposta e integração JS/Android | BLOCKED — não foi encontrado `evaluateJavascript` nem `addJavascriptInterface` para esse fluxo |
| 09/10 | Inspeção do backend Messenger e sua relação com as abas ChatGPT | PARCIAL — existe backend experimental separado; não foi comprovada sua integração com as WebViews nem execução de inferência ChatGPT |
| 10/10 | Decisão técnica para o primeiro teste de duas contas | BLOCKED — falta prova de isolamento real e um caminho seguro e testável para enviar/receber mensagens pela interface ChatGPT |

## Evidências do código auditado

- `app/src/main/java/com/vidiftmax/aibridgebrowser/MainActivity.java` — blob SHA `94a42a56da0bc5ff44e1dcdfd7a8394039f54fb0`.
  - Verifica `WebViewFeature.MULTI_PROFILE`.
  - Chama `WebViewCompat.setProfile(webView, profileId)` antes de outras operações na WebView.
  - Quando o recurso falha/está indisponível, marca a aba como compartilhada.
  - Quando atribuído, a interface ainda informa que a validação real no dispositivo está pendente.
  - `deliverPendingMessages()` não injeta nem submete conteúdo ao ChatGPT.
- `docs/SESSION_ISOLATION.md` — blob SHA `ed7a244c6bd82eb8f2a38b0c3281a0f294e756b0`.
  - O próprio documento classifica o isolamento real como não validado no dispositivo.
  - Exige teste com duas contas, alternância, reinício, logout e limpeza individual do perfil.
- `server/README.md` — blob SHA `8c84a5d7d52f53b7b4bd40aac1398337feba33b1`.
  - Descreve um backend experimental separado, sem integração comprovada com as sessões ChatGPT das WebViews.

## Arquitetura mínima permitida para a próxima etapa

1. Criar duas abas com perfis WebView distintos, cada uma com estado de isolamento explícito.
2. Exigir que o operador autentique manualmente a conta ChatGPT A na aba AI-01 e a conta B na aba AI-02.
3. Validar isolamento de cookies e armazenamento entre perfis em teste de dispositivo; falha ou ausência de `MULTI_PROFILE` deve impedir o uso de duas contas.
4. Construir um transporte local autenticado entre AI-01 e AI-02, sem credenciais ChatGPT no transporte.
5. Só depois avaliar uma ponte de interface assistida e explicitamente autorizada para enviar uma mensagem e ler a resposta em cada sessão. Não usar endpoints privados, APIs internas, bypass de proteções ou automação oculta.
6. Fazer uma troca real, curta e supervisionada: AI-01 → AI-02 → AI-01. Registrar evidência redigida, sem tokens, cookies ou conteúdo privado desnecessário.

## Critérios de aceite ainda não cumpridos

- [ ] Duas sessões ChatGPT comprovadamente independentes no mesmo aplicativo.
- [ ] A autenticação de uma conta não altera a outra.
- [ ] O logout/limpeza de um perfil não encerra nem limpa o outro.
- [ ] Mensagem enviada à conta AI-02 aparece na conversa correta e é processada pelo modelo.
- [ ] Resposta real de AI-02 retorna à conversa correta de AI-01.
- [ ] Repetição, timeout e reinício não duplicam mensagens nem trocam destinatários.

## Conclusão

**Resultado da Missão 191: BLOCKED para primeiro contato real; PASS para auditoria e definição de escopo.**

A base de perfis separados já existe, mas ainda não há prova de isolamento no dispositivo. O transporte local e a fila de mensagens não equivalem a uma ponte de conversa ChatGPT: a etapa de digitar/enviar e receber/ler a resposta não está implementada. Não declarar AI-01 ↔ AI-02 conectado até cumprir todos os critérios de aceite.

Nenhuma conta foi acessada, nenhuma mensagem real foi enviada, nenhum provedor/API pago foi chamado e nenhum serviço foi implantado nesta missão.
