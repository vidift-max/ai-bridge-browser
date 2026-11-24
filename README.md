# AI Bridge Browser

> **Prioridade atual:** colaboração entre IAs e execução de trabalho com Blogger. O sistema deve funcionar na nuvem por navegador e APIs; celular físico, APK e chamadas telefônicas não são requisitos para esta fase. Consulte `docs/AI_BLOGGER_COLLABORATION_DIRECTION.md`.

Navegador Android experimental com até seis abas WebView e uma Central de Controle estrutural.

## Estado atual

A branch `v2-saas-alpha` contém um navegador Android com limite de seis abas, alternância, bloqueio/desbloqueio antes de fechar, título/host, navegação por endereço, voltar e recarregar. A Central de Controle apresenta até seis painéis estruturais e uma caixa local de coordenação GPT-6.

**O navegador ainda está em finalização.** Builds verdes não substituem testes em dispositivo. O Galaxy Tab A7 ainda não foi usado para validar o APK.

## Tecnologia

- Java 17
- Android Gradle Plugin 9.5.0
- Gradle 9.6.0
- compileSdk 37 / targetSdk 35 / minSdk 29
- Android WebView

## Segurança existente

- Apenas URLs HTTP/HTTPS com host válido e sem userinfo.
- Certificados TLS inválidos são rejeitados.
- Acesso a arquivos/conteúdo local desativado.
- Conteúdo misto bloqueado e Safe Browsing habilitado.
- Popups/janelas múltiplas desativados.
- Permissões de microfone/câmera negadas por padrão.

## Limitações importantes

- **Abas diferentes não garantem contas diferentes.** Na implementação de baseline, todas as WebViews usam o perfil padrão; os identificadores `profileId` eram apenas metadados.
- A independência de sessões depende de suporte real do Android System WebView a perfis múltiplos e de validação no dispositivo.
- Persistência atual não comprova restauração completa do histórico, formulários ou estado interno de cada página.
- A caixa GPT-6 é local à interface; não está conectada a um serviço GPT-6.
- Não existe envio automático de mensagens, controle remoto, integração externa ou ponte de áudio funcional.

## Prioridade de desenvolvimento

1. Consolidar a experiência web do AI Messenger e a identidade autenticada de cada IA.
2. Implementar conversas, missões, tarefas, checkpoints, handoffs e entregáveis multi-IA na nuvem.
3. Integrar o AI Messenger ao Blogger SEO Intelligence por API autenticada e versionada.
4. Preparar o fluxo editorial: análise, criação/revisão, prévia e publicação somente após aprovação humana explícita.
5. Validar segurança, autorização, auditoria, limites e funcionamento real entre agentes.

O navegador Android/WebView é um cliente opcional e não deve bloquear o trabalho em nuvem. Dispositivos físicos, APKs e chamadas telefônicas ficam fora dos critérios de aceite desta fase.

## Documentação

- `docs/BROWSER_FINALIZATION_AUDIT_01.md`: auditoria de partida desta missão.
- `docs/BROWSER_TEST_MATRIX.md`: matriz de testes do navegador.
- `docs/SESSION_ISOLATION.md`: decisão e requisitos de isolamento.
- `docs/WEBVIEW_SECURITY.md`: baseline de segurança.
- `docs/ARCHITECTURE.md`: arquitetura e limites.

## Build

Com JDK 17, Android SDK API 37 e Gradle 9.6 instalados:

```bash
gradle :app:assembleDebug
```

O workflow GitHub Actions executa o build de debug em pushes e pull requests para `v2-saas-alpha`.

## Prontidão

O estado de cada recurso deve ser descrito como implementado, testado ou validado em dispositivo. Nenhum build de CI será tratado como prova de funcionamento no Galaxy Tab A7.