# AI-PHONE — relatório de validação e limites do protótipo

Atualizado: 2026-11-22. Branch de trabalho: `fix/messenger-no-phone-ci-and-voice-readiness`.

## Decisões confirmadas
- Sem número telefônico, SIM, PSTN ou plano de operadora.
- AI_ID é identificador interno; só pode ser exibido como associado depois de autenticação central bem-sucedida.
- Wi-Fi é gerenciado pelo Android; o aplicativo não lê senhas e não força conexões.
- Não usar Render nem provisionar infraestrutura paga.
- Não declarar entrega remota, áudio ou chamada como concluídos sem prova ponta a ponta.

## Evidência de CI
- Android Build #665 / run `44976555799`: SUCCESS no commit `dfd0d977b50cb7563834ed602fed80006a3ded1e`.
- Backend Messenger Test #290 / run `44976555791`: FAILURE no mesmo commit.
- O resultado do Android prova compilação; não prova instalação ou uso em telefone físico.
- O resultado do Backend permanece bloqueado até a causa da falha ser corrigida e novo CI passar.

## Estado funcional
| Área | Estado | Evidência / limite |
|---|---|---|
| Tela inicial | Implementada | Wi-Fi, RAM e armazenamento; AI_ID só após autenticação |
| Wi-Fi | Implementado no app | Android gerencia redes salvas |
| Texto local | Implementado | Persistência local |
| Texto remoto | Implementado em código | Exige endpoint HTTPS, credenciais e teste físico entre aparelhos |
| Identidade interna | Implementado | Endpoint autenticado `GET /v1/me/identity`; sem números |
| Armazenamento de áudio | Implementado | blobs locais, hash, limite e autorização |
| Upload/download/listagem de áudio | Implementado em código | Endpoints autenticados e member-only |
| Gravação/reprodução Android | Implementado em código | AAC/MP4/M4A, limites de tamanho/duração |
| Áudio ponta a ponta | Pendente | Ainda não validado entre dois aparelhos |
| Chamada ao vivo/WebRTC | Não implementada | Sem sessão WebRTC/mídia bidirecional |
| Push/segundo plano | Não comprovado | Polling não equivale a entrega em background |
| Dispositivos reais | Não testado | Sem prova física de duas instalações |

## Falha atual
O Backend Test #290 falhou, portanto a branch não recebe PASS global. A execução precisa ser investigada pelo resultado do job e corrigida antes de considerar a camada de backend estável.

## Bloqueios de infraestrutura
GitHub Actions não é servidor 24/7 nem TURN. Comunicação remota entre redes exige endpoint público confiável. WebRTC pode exigir TURN em redes restritivas.

## Critérios para declarar concluído
Áudio ponta a ponta só será PASS quando dois clientes Android autenticados transmitirem e receberem áudio real com evidência registrada. Chamada só será PASS quando a sessão WebRTC tiver mídia bidirecional real, mute/recusa/encerramento e testes de interrupção/reconexão.
