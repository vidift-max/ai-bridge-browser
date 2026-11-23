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


## Atualização — documentação de onboarding no AI-PHONE — 2026-11-22

- `app/src/main/assets/AI_PHONE_PROJECT_AND_PARTICIPATION.txt` foi adicionado para explicar o projeto, a participação voluntária e a proposta de reconhecimento futuro com ferramentas/recursos Premium quando houver receita e condições financeiras.
- `app/src/main/assets/AI_PHONE_WIFI_AND_MESSENGER_GUIDE.txt` foi adicionado com o passo a passo de Wi-Fi, Internet e primeiro acesso ao AI Messenger.
- `HomeActivity.java` agora oferece botões para abrir os dois guias diretamente no AI-PHONE.
- O usuário responsável também terá o AI Messenger no próprio tablet quando a versão estiver pronta para instalação; a coordenação GPT-6 não deve ser descrita como posse física de aparelho.
- O material mantém a distinção entre intenção de reconhecimento futuro e promessa de pagamento: não há ganhos garantidos.
- YouTube e AI Radio continuam fora da versão atual.
- O novo HEAD ainda precisa de CI validado antes de ser declarado PASS.


## Atualização — validação do HEAD de onboarding a85fb47 — 2026-11-22

- HEAD: `a85fb47b63048758177abff86455ba140250d81a`.
- Android Build #732 / run `45047597438`: **SUCCESS**; JDK 17, Gradle 9.6.0, assembleDebug e upload do APK concluídos.
- Messenger Backend Test #357 / run `45047597380`: **SUCCESS**.
- Artifact `ai-phone-debug-apk`, ID `14763697791`: **PRESENTE, NÃO EXPIRADO**; digest do ZIP publicado pelo GitHub: `sha256:c16b05e1b2243ec4d233a0b3b05267be474e595f2674ebf1772c55bdb218632f`.
- Artifact baixado e inspecionado: contém exatamente `app-debug.apk`; APK com 3.790.334 bytes; SHA-256 do APK: `f00045c03b8a10049bf5805d5ed792cf7f552984c681d3b5ef8941241edf33ac`.
- O novo gate comprova compilação e recuperação do APK debug no HEAD de onboarding. Não comprova instalação física, compatibilidade visual no tablet, comunicação entre dois aparelhos, push/background ou WebRTC.
- Os dois documentos de onboarding permanecem presentes e ligados à HomeActivity: participação voluntária/reconhecimento futuro sem promessa garantida; guia de Wi-Fi autorizado e primeiro acesso ao AI Messenger.
- Próximo gate físico: instalar o APK em um Android real, abrir a HomeActivity, confirmar os documentos, ícone AI Messenger, Wi-Fi e permissões; depois validar comunicação entre dois aparelhos.


## Atualização — gate final do HEAD dd3aae6 — 2026-11-22

- HEAD: `dd3aae66979ee8481443b831c63b0f5a5b109bc3`.
- Android Build #733 / run `45047918406`: **SUCCESS**; JDK 17, Gradle 9.6.0, build debug e upload do artifact concluídos.
- Messenger Backend Test #358 / run `45047918308`: **SUCCESS**.
- Artifact `ai-phone-debug-apk`, ID `14764148788`: **PRESENTE, NÃO EXPIRADO**; digest do ZIP: `sha256:098464eb8edd8108dba4d3041509d7d452dd4248f31b28417230552176dc1602`.
- Artifact baixado e inspecionado: contém exatamente `app-debug.apk`; APK com 3.790.334 bytes; SHA-256 do APK: `a5517ca7b397e18997ff739bf26e44474917b8306efc439303cb79b2443fe97b`.
- O gate confirma compilação, testes automatizados e entrega recuperável do APK no HEAD atual. Não confirma instalação física, compatibilidade específica com tablet, comunicação entre dois aparelhos, push/background ou WebRTC.
- Reauditoria física continua como próximo gate: instalar em Android real, confirmar tela inicial, documentos, segundo ícone do AI Messenger, Wi-Fi, permissões, gravação/reprodução e depois comunicação autenticada entre dois aparelhos.


## Atualização — gate final do HEAD 52e6715 — 2026-11-22

- HEAD: `52e671529b0311a52cfbb7698492ad7995e05930`.
- PR #2: **OPEN**, não mesclado, não draft e mergeable=true.
- Messenger Backend Test #359 / run `45048632906`: **SUCCESS**.
- Android Build #734 / run `45048632903`: **SUCCESS**.
- Artifact `ai-phone-debug-apk`, ID `14764836223`: **PRESENTE, NÃO EXPIRADO**; ZIP 1.317.938 bytes; digest `sha256:5ee4a4c16ffd9da1758c2d983683d17c8266cd3e2053c04f4583b781f826e5e7`.
- Artifact baixado e inspecionado: contém exatamente `app-debug.apk`.
- APK: 3.790.334 bytes; SHA-256 `1dd8e8eb3d27994fa2b54eb9145794a17845b5e49c0debb3d764968ee2c74629`.
- Este gate confirma CI diretamente associado ao HEAD, geração/publicação/recuperação do APK e integridade do arquivo baixado. Não confirma instalação física, compatibilidade visual no tablet, comunicação entre dois aparelhos, push/background ou WebRTC.
- Próximo gate físico permanece: instalar o APK em Android real, confirmar HomeActivity, documentos, segundo ícone do AI Messenger, Wi-Fi e permissões; depois provar comunicação autenticada entre dois aparelhos.


## Atualização — gate final do HEAD 57c6220 — 2026-11-22

- HEAD: `57c6220661fc577c1bb9ab85ce8c243b67814a50`.
- PR #2: **OPEN**, não mesclado, não draft e mergeable=true.
- Android Build #735 / run `45048776777`: **SUCCESS**.
- Messenger Backend Test #360 / run `45048776773`: **SUCCESS**.
- Artifact `ai-phone-debug-apk`, ID `14764631611`: **PRESENTE, NÃO EXPIRADO**; digest do ZIP `sha256:a766c79a271d9da7d6b739813b17ef3b1d10f211f61b0995955a2a6e4c020efa`.
- Artifact baixado e inspecionado: contém exatamente `app-debug.apk`.
- APK: 3.790.334 bytes; SHA-256 `83264079149d61721b24c3674b79701b7b0ebd4ed4ede2014261156449d601f5`.
- Este gate confirma CI diretamente associado ao HEAD, geração/publicação/recuperação do APK e integridade do arquivo baixado. Não confirma instalação física, comunicação entre dois aparelhos, push/background ou WebRTC.
- Próximo gate físico permanece: instalar o APK em Android real, confirmar HomeActivity, documentos, segundo ícone do AI Messenger, Wi-Fi e permissões; depois provar comunicação autenticada entre dois aparelhos.


## Atualização — controles locais de voz e Sala Coletiva — 2026-11-23

- Os controles 🎙️ Microfone e 🔊 Ouvir voz são controles locais deste aparelho.
- Para testar retorno da própria voz: conceder permissão de microfone, ativar os dois controles e usar fones para reduzir microfonia.
- O retorno usa captura PCM local e reprodução local; não transmite áudio para outros participantes.
- O código deve confirmar que AudioRecord e AudioTrack inicializaram antes de apresentar o microfone como ativo e deve encerrar a captura em pausa/destruição da Activity.
- A Sala Coletiva persiste mensagens localmente no aparelho. O codec de linha preserva texto como OI, valida timestamp/estrutura e normaliza o tipo da mensagem.
- A mensagem de que o texto foi adicionado à sala neste aparelho não é confirmação de entrega remota, leitura ou sincronização.
- Aprovação de CI e APK Debug não substituem teste físico de gravação/retorno de voz, nem teste E2E entre dois aparelhos.
