# AI-PHONE — relatório de validação e limites do protótipo

Atualizado: 2026-11-21/22. Branch de trabalho: `fix/messenger-no-phone-ci-and-voice-readiness`.

## Decisões confirmadas
- Sem número telefônico, SIM, PSTN ou plano de operadora.
- AI_ID é identificador interno; só pode ser exibido como associado depois de autenticação central bem-sucedida.
- Wi-Fi é gerenciado pelo Android; o aplicativo não lê senhas e não força conexões.
- Não usar Render nem provisionar infraestrutura paga.
- Não declarar entrega remota, áudio ou chamada como concluídos sem prova ponta a ponta.

## Evidência de CI observada
- Backend Messenger Test #221 / run `44973854657`: SUCCESS no commit `5938ada3967032f4a759b0b7e3cc7ce1a7d4f067`.
- Android Build #596 / run `44973854645`: SUCCESS no mesmo commit.
- O CI acima prova testes automatizados e compilação Android, não instalação ou uso em telefone físico.
- Alterações posteriores nesta branch exigem nova execução de CI; os resultados acima não cobrem commits posteriores.

## Estado funcional
| Área | Estado | Evidência / limite |
|---|---|---|
| Tela inicial | Implementada | Wi-Fi, RAM e armazenamento exibidos; associação de AI_ID não é inventada |
| Wi-Fi | Implementado no app | Diagnóstico via Android; reconexão depende das redes salvas no sistema |
| Texto local | Implementado | Persistência local no app |
| Texto remoto | Backend e cliente existentes | Exige endpoint HTTPS, credenciais válidas e teste entre aparelhos |
| Identidade interna | Endpoint autenticado | `GET /v1/me/identity`; sem números |
| Áudio gravado | Não implementado | Sem captura, upload ou reprodução de anexos |
| Chamada ao vivo | Não implementada | Sem sinalização WebRTC, ciclo de chamada ou mídia bidirecional |
| Push/segundo plano | Não comprovado | Polling manual não equivale a entrega confiável em background |
| Dispositivos reais | Não testado | Não há prova física de duas instalações |

## Bloqueios de infraestrutura gratuita
GitHub Actions não é servidor de mensagens permanentemente acessível, nem TURN. O backend atual pode ser executado em ambiente de teste/local, mas comunicação remota entre redes exige um endpoint público confiável. WebRTC pode conectar diretamente em algumas redes; NAT/firewalls restritivos podem exigir TURN, que consome banda e não tem garantia de custo zero. Não prometer cobertura global sem relay.

## Próximas etapas técnicas
1. Corrigir e testar o contrato Android de identidade interna, sem reutilizar registro telefônico.
2. Criar armazenamento seguro de anexos de áudio com quotas, hash, autorização e retenção.
3. Implementar captura/reprodução de áudio com permissões solicitadas sob ação do usuário.
4. Implementar sessões de chamada e sinalização autenticada.
5. Integrar WebRTC Android e validar mídia bidirecional em dois dispositivos.
6. Fazer testes de interrupção, reconexão, privacidade, autorização e limites.
7. Só depois avaliar opções de hospedagem realmente gratuitas e suas limitações.

## Critérios para declarar concluído
Uma chamada só é considerada funcional quando dois clientes Android autenticados estabelecem sessão, ambos recebem e transmitem áudio real, mute/recusa/encerramento funcionam e a evidência de teste é registrada. Um status HTTP, um convite enviado ou ICE conectado não é prova suficiente.
