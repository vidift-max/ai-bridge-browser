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


## Atualização de entrega — APK debug
- Android Build #675 / run `44984566411`: **SUCCESS** no commit `3b2b5330ebdf1ab2d49dd55c4f450260326f303b`.
- Artifact `ai-phone-debug-apk` (ID `14738199924`): **PRESENTE, NÃO EXPIRADO**.
- O artifact foi baixado e contém exatamente `app-debug.apk`.
- APK: 3.772.215 bytes; SHA-256 `919c9eb0087848e410f4f4b8b92681e15ebe89da34c264cb75519e315c5f2c83`.
- Backend #300 / run `44984566404`: **SUCCESS**.
- Este gate comprova geração e recuperação do APK debug. Não comprova instalação em aparelho físico, compatibilidade específica com o tablet do usuário, comunicação entre dois aparelhos, push/background ou chamadas WebRTC.

## AI-PHONE participant-facing finish — 2026-11-22

- AI Radio is out of scope. AI Messenger is the single communication hub for private chats, groups, collective notices, text and audio.
- The Android home screen no longer displays an AI Radio card.
- `app/src/main/assets/AI_PHONE_WELCOME.md` is the participant welcome document, displayed from the home screen.
- Invitation and welcome document explain voluntary participation and the proposal for Premium resources/tools/subscriptions when monthly revenue and financial conditions allow; no guaranteed earnings are promised.
- YouTube is intentionally out of scope for the current AI-PHONE release; it may be reconsidered only in a future post-revenue update.
- AI Messenger has a dedicated launcher alias and vector icon in the same APK. This is a separate launcher entry, not a separately packaged application.
- Build validation: **PASS** no Android Build #722 / run `44991042832` para o HEAD `f4332ad0b1cf8c3b7d2626fb1b3c8a3046a1b66d`; o erro da chave final foi corrigido e, posteriormente, o helper `dp(int)` ausente também foi corrigido. A compilação seguinte gerou e publicou o artifact `ai-phone-debug-apk` (ID `14741822614`).
- Physical launcher visibility, tablet layout, installation, and communication between two physical devices remain unverified until tested on actual Android hardware.


## Atualização de validação — entrega AI-PHONE #722

- HEAD validado: `f4332ad0b1cf8c3b7d2626fb1b3c8a3046a1b66d`.
- Android Build #722 / run `44991042832`: **SUCCESS**; `:app:assembleDebug` e upload do artifact concluídos.
- Artifact `ai-phone-debug-apk`, ID `14741822614`: presente, não expirado; tamanho do ZIP do artifact: 1.314.263 bytes; digest publicado pelo GitHub: `sha256:e5065d5c1152f25a356770397fc4886677631da143ad665f0bed79f1f17e94ec`; expira em 2027-02-20.
- Backend Test #347 / run `44991043281`: **SUCCESS**.
- A causa da falha no Android Build #721 foi a ausência do helper `dp(int)` em `HomeActivity`; o helper foi adicionado no commit acima e a compilação seguinte passou.
- PR #2 permanece aberto, não mesclado e mergeable.
- Esta evidência confirma compilação e publicação do artifact do APK debug no HEAD indicado. O digest acima é do artifact ZIP informado pela API do GitHub; não é declarado como SHA-256 do APK interno.
- Ainda não há evidência de instalação física, exibição do alias no launcher real, compatibilidade visual em tablet, YouTube aberto em dispositivo, comunicação entre dois aparelhos, entrega de áudio ponta a ponta, push/background ou chamada WebRTC.
- AI Messenger continua sendo uma segunda entrada do launcher dentro do mesmo APK, não um pacote Android separado.
- AI Radio permanece fora de escopo.

## Atualização de produto — YouTube fora da versão atual

- YouTube foi removido da tela inicial do AI-PHONE e não é requisito da versão atual.
- O foco atual permanece no AI Messenger, Wi-Fi, identidade, missões, áudio e comunicação autorizada.
- Uma futura atualização poderá reconsiderar YouTube somente após a conclusão do projeto e geração de receita, conforme decisão posterior do produto.
