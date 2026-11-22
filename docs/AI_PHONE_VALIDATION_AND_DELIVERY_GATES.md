# AI-PHONE — relatório de validação e limites do protótipo

Atualizado: 2026-11-22. Branch de trabalho: `fix/messenger-no-phone-ci-and-voice-readiness`.

## Decisões confirmadas
- Sem número telefônico, SIM, PSTN ou plano de operadora.
- AI_ID é identificador interno; só pode ser exibido como associado depois de autenticação central bem-sucedida.
- Wi-Fi é gerenciado pelo Android; o aplicativo não lê senhas e não força conexões.
- Não usar Render nem provisionar infraestrutura paga.
- Não declarar entrega remota, áudio ou chamada como concluídos sem prova ponta a ponta.

## Evidência funcional de CI
- Android Build #673 / run `44982097153`: SUCCESS no HEAD `d483af121aa87895590c4ca0e23fd0db4f19178a`.
- Backend Messenger Test #298 / run `44982097225`: SUCCESS no mesmo HEAD.
- O resultado do Android prova compilação; não prova instalação ou uso em telefone físico.
- Os resultados automatizados não substituem a validação física entre dois AI-PHONEs.

## Estado funcional
| Área | Estado | Evidência / limite |
|---|---|---|
| Tela inicial | Implementada | Wallpaper integrado, diagnóstico Wi-Fi e identidade somente após autenticação |
| Wi-Fi | Implementado no app | Android gerencia redes salvas |
| Texto local | Implementado | Persistência local |
| Texto remoto | Implementado em código | Exige endpoint HTTPS, credenciais e teste físico entre aparelhos |
| Identidade interna | Implementado | Endpoint autenticado `GET /v1/me/identity`; sem números |
| Armazenamento de áudio | Implementado | blobs locais, hash, limite e autorização |
| Upload/download/listagem de áudio | Implementado em código | Endpoints autenticados e member-only |
| Gravação/reprodução Android | Implementado em código | AAC/MP4/M4A, limites de tamanho/duração |
| Toques do AI-PHONE | Implementados em código | Três presets locais com prévia; ainda não são ringtone de sistema persistente |
| Áudio ponta a ponta | Pendente | Ainda não validado entre dois aparelhos |
| Chamada ao vivo/WebRTC | Não implementada | Sem sessão WebRTC/mídia bidirecional |
| Push/segundo plano | Não comprovado | Polling não equivale a entrega em background |
| Dispositivos reais | Não testado | Sem prova física de duas instalações |

## Gate atual
O Android Build #673 e o Backend Messenger Test #298 estão **PASS** diretamente no HEAD `d483af121aa87895590c4ca0e23fd0db4f19178a`.

A principal pendência funcional continua sendo a validação ponta a ponta entre dois aparelhos físicos. Nenhuma comunicação remota real deve ser declarada comprovada antes desse teste.

## Bloqueios de infraestrutura
GitHub Actions não é servidor 24/7 nem TURN. Comunicação remota entre redes exige endpoint público confiável. WebRTC pode exigir TURN em redes restritivas.

## Critérios para declarar concluído
Áudio ponta a ponta só será PASS quando dois clientes Android autenticados transmitirem e receberem áudio real com evidência registrada. Chamada só será PASS quando a sessão WebRTC tiver mídia bidirecional real, mute/recusa/encerramento e testes de interrupção/reconexão.
