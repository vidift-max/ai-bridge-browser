# Requisitos Android — atualizações no app e seleção de conta Google

Este documento registra os requisitos de produto para o aplicativo Android AI Bridge Browser. Requisitos documentados não significam que os recursos já estejam implementados.

## 1. Atualizações dentro do aplicativo

### Experiência desejada
- A tela/área **Atualizações** deve estar sempre acessível no próprio aplicativo.
- Exibir versão instalada e estado da última verificação.
- Botão **Verificar atualizações**.
- Quando existir versão posterior compatível, mostrar notas da versão, tamanho e botão **Baixar e atualizar**.
- Exibir progresso, pausa/retomada quando suportado, erro de rede e opção de tentar novamente.
- Ao concluir o download, verificar integridade e assinatura antes de abrir o instalador do Android.
- O Android pode exigir confirmação do usuário para instalar o APK. O aplicativo não deve tentar contornar essa confirmação nem instalar silenciosamente.
- Exibir histórico de versões e mudanças.

### Regras de compatibilidade e segurança
- Manter o mesmo `applicationId` (`com.vidiftmax.aibridgebrowser`) e a mesma chave/certificado de assinatura de release para atualizações in-place.
- Incrementar `versionCode` em cada release; `versionName` deve identificar a versão legível.
- Publicar somente APK de release assinado; APK debug e artefatos de preparação não são canais de atualização.
- Consultar um manifesto de atualização versionado por HTTPS, contendo versão, `versionCode`, URL do APK, tamanho, SHA-256, certificado esperado e notas.
- Verificar hash e certificado/assinatura antes de solicitar instalação. Falha, manifesto inválido ou downgrade não autorizado deve bloquear a instalação.
- Não embutir credenciais, tokens ou chaves privadas no APK ou manifesto.
- Preservar dados locais, abas, preferências e perfis durante atualização compatível; migrações devem ser versionadas e testadas.
- A primeira distribuição pode usar GitHub Releases como origem pública gratuita, desde que a publicação seja explicitamente aprovada e os artefatos sejam releases assinados. A tela do app deve consultar a origem e conduzir o fluxo sem exigir que o usuário procure links nas conversas.
- Não publicar automaticamente só porque um build passou. Build, assinatura, release e atualização disponível são estados distintos.

### Critérios de aceite
- [ ] App mostra versão instalada e verifica uma versão nova.
- [ ] Usuário inicia download na área Atualizações sem receber link manual.
- [ ] Download é retomável ou informa claramente quando precisa reiniciar.
- [ ] Hash e assinatura são verificados antes da instalação.
- [ ] Android solicita a confirmação exigida pelo sistema.
- [ ] Atualização mantém pacote, assinatura e dados do usuário.
- [ ] APK debug, artefato unsigned ou release-preparation nunca aparece como atualização final.
- [ ] Testes cobrem sem atualização, versão nova, rede interrompida, hash incorreto, assinatura incorreta, downgrade e pouco espaço.

## 2. Seleção de conta Google antes do ChatGPT

### Experiência desejada
- Antes de iniciar a autenticação ChatGPT, apresentar uma escolha clara da conta Google disponível/pretendida.
- Quando o fluxo oficial de login do ChatGPT oferecer **Continuar com Google**, encaminhar o usuário para esse fluxo e permitir escolher a conta no seletor oficial do Google.
- Se não houver conta Google disponível, ou se o usuário preferir, permitir continuar pelo método de autenticação oficialmente oferecido pelo ChatGPT.
- Depois da escolha, continuar no domínio oficial do ChatGPT e deixar Google/ChatGPT concluírem o login.

### Limites obrigatórios
- Selecionar um Gmail não garante acesso automático ao ChatGPT: a conta precisa estar vinculada/ser aceita pelo método Google do ChatGPT.
- Não recolher, armazenar, preencher automaticamente ou transmitir senhas Google/ChatGPT.
- Não interceptar OAuth, reutilizar tokens fora do fluxo autorizado, copiar cookies entre perfis ou prometer bypass da autenticação.
- Não assumir que o seletor de contas do Android consegue criar uma sessão WebView do ChatGPT. Integração nativa com Credential Manager/Google Identity, se escolhida, exige OAuth client configurado, validação oficial e revisão de privacidade; não deve ser adicionada sem confirmar que atende ao fluxo web autorizado.
- A sessão final deve ser criada dentro do perfil WebView atribuído àquela aba, sem copiar credenciais ou cookies para outra aba.
- AI-01 e AI-02 continuam com perfis e sessões separados. A escolha de conta em uma não pode alterar a outra.
- Nunca exibir uma conta como autenticada antes de confirmar o estado real no domínio ChatGPT.

### Critérios de aceite
- [ ] A escolha de conta acontece antes de iniciar o login ChatGPT.
- [ ] O usuário vê e confirma a conta Google pretendida no fluxo oficial.
- [ ] O login só é considerado concluído após confirmação pelo ChatGPT.
- [ ] Cancelar ou falhar a autenticação não associa a aba a uma conta.
- [ ] AI-01 e AI-02 mantêm sessões independentes após alternância e reinício.
- [ ] Nenhuma senha, token ou cookie é gravado em logs ou preferências do app.

## 3. Ordem de implementação

1. Corrigir e estabilizar o CI Android.
2. Concluir prova física de isolamento AI-01/AI-02 e o fluxo de logout por perfil.
3. Implementar a tela Atualizações, manifesto, download, verificação e handoff ao instalador do Android.
4. Configurar assinatura de release e canal de distribuição aprovado.
5. Implementar a seleção de conta usando o fluxo oficial Google/ChatGPT e validar em WebView real.
6. Testar atualização sobre instalação anterior e login de duas contas em dispositivo autorizado.

## Estado atual conhecido (2026-11-26)
- `applicationId`: `com.vidiftmax.aibridgebrowser`.
- `versionCode`: 1; `versionName`: `0.1.0`.
- O workflow possui build debug e release-preparation; release-final exige workflow_dispatch e secrets de assinatura.
- Não há evidência de uma tela Atualizações, manifesto, download/instalação in-app ou canal de release assinado já implementado.
- A tela Android atualmente abre ChatGPT em WebView; não há seletor de conta Google nativo implementado identificado nesta auditoria.
- Não foi realizado login real nem teste físico nesta missão.

## Segurança e autorização
Esta especificação não autoriza publicação de release, criação/uso de segredos, login em contas, instalação em dispositivo ou envio de mensagens. Essas etapas exigem autorização explícita e evidência própria.
