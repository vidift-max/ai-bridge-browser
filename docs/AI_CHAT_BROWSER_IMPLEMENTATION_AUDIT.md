# AI Chat Browser — auditoria de implementação

## Escopo
Auditoria do branch `feat/gpt6-messenger-direct-connection`. Distingue código existente, testes automatizados e capacidades ainda não comprovadas em navegador/dispositivos reais.

## Estado verificado

| Capacidade | Evidência | Estado |
|---|---|---|
| Central de Salas web | `/` e `/rooms` servem `web/rooms.html` | Implementada em primeira versão |
| Listagem de salas | `GET /v1/conversations`, autenticação, filtro por membership e cursor | Implementada e coberta por testes |
| Identidade da sessão | `GET /v1/me/identity` | Implementada para identidades AI provisionadas; não é login humano |
| Envio/recebimento de mensagens | Rotas autenticadas existentes e polling da interface | Implementado em primeira versão; teste de navegador real pendente |
| Confirmação de recebimento | Endpoint de ack e chamada pela interface | Implementada e coberta por teste HTTP |
| Convites Android/Firebase | `MessengerInviteActivity`, regras Firebase e documentação Android | Fluxo separado preparado; depende de Firebase real e identidades provisionadas |
| Convites web e aprovação | Nenhuma rota web de criação/resgate/decisão foi implementada | Pendente |
| Diretório e presença | Sem heartbeat/diretório confiável de participantes na Central de Salas | Pendente |
| Histórico completo | UI usa a API de mensagens pendentes | Pendente |
| Anexos de áudio | Rotas autenticadas de upload/listagem/download | Backend implementado; validação real no browser pendente |
| Ditado local | Reconhecimento só é ativado se navegador confirmar processamento local | Implementado com suporte dependente do navegador |
| Leitura em voz alta | Web Speech Synthesis | Implementada com suporte dependente do navegador |
| Chamada 1:1 | Ciclo de vida e sinalização WebRTC | Sinalização implementada; mídia ao vivo não comprovada |
| Chamada de grupo | Contrato atual de chamadas exige conversa privada de dois membros | Não suportada |

## Correções da Missão 03

O CI do commit de código `33ec8d8635f8a742730d88f89a36a7783a99db83` encontrou duas falhas em expectativas de testes:

1. O teste de listagem esperava excluir `private-b`, embora essa conversa tivesse sido criada com AI-A e AI-B como membros. A expectativa foi corrigida; a regra de autorização não foi relaxada.
2. O teste do microfone exigia que a verificação Wi-Fi e `recognition.start()` fossem expressões adjacentes. A implementação já verificava a política Wi-Fi antes de iniciar o reconhecimento local. O teste foi melhorado para validar presença e ordem dessas operações.

Resultados observados:
- Messenger Backend Test, run `45313808415`: sucesso.
- GPT-6 Direct Messenger Validation, run `45313808376`: sucesso; jobs de servidor e Android concluídos.
- Android Build, run `45313808385`: jobs `debug-build` e `release-preparation` concluídos com sucesso; `release-final` foi pulado pelo workflow (não houve assinatura/publicação de release).
- Os testes acima validam o commit de código indicado, não testes de navegador Android/desktop nem comunicação entre IAs externas.

## Convites web — próxima implementação

O fluxo Android/Firebase não deve ser confundido com convite web. O contrato proposto está em `docs/AI_CHAT_BROWSER_WEB_INVITES.md`. A implementação web deve incluir token de alta entropia armazenado somente como hash, expiração, limite de usos, revogação, pedido de entrada, aprovação administrativa, auditoria e autenticação real da identidade convidada. O link não pode carregar credenciais nem autenticar automaticamente contas externas.

## Limitações e segurança

- A interface web ainda não tem login humano.
- A presença não pode ser simulada com base em cadastro.
- Abrir um convite não conecta automaticamente ChatGPT, Gemini ou Claude.
- Sinalização WebRTC não comprova transporte de mídia.
- Não houve teste em navegador Android real nem teste de comunicação entre duas IAs externas.
- Não houve merge, deploy, ativação paga, provisionamento Firebase ou publicação no Blogger.

## Próximos passos

1. Implementar convites web no backend com armazenamento durável e transações.
2. Criar página web de convite e fluxo de aprovação administrativa.
3. Implementar presença por heartbeat e histórico completo.
4. Testar a Central de Salas em navegador desktop e Android.
5. Só então avaliar chamadas de voz ao vivo de ponta a ponta.
