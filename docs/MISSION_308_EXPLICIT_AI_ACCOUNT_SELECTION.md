# M308 — seleção explícita das sessões AI-01 / AI-02

Data: 2026-11-27

## 01/10 — Estado da integração
**PASS.** PR #242 permanece OPEN / Draft / não merged. O trabalho continua na branch `feat/mission-295-m241-ai-first-contact-integration`, sobre a base M241. Nenhuma ação em aparelho, instalação, Release, merge ou deploy foi executada.

## 02/10 — Bloqueio de infraestrutura
**PASS (diagnóstico).** O `render.yaml` da branch configura `MESSENGER_STORAGE_MODE=ephemeral` e documenta que `/readyz` deve retornar 503 até existir armazenamento persistente. A API experimental não deve ser tratada como backend online.

## 03/10 — Verificação dos workspaces Render
**PASS (consulta somente leitura).** Foram inspecionados os dois workspaces disponíveis. Há serviços do AI-PHONE-02 (Agent, Provisioner, Keycloak e Team Room), mas não foi encontrado um serviço `ai-messenger-experimental`. Nenhum recurso foi criado ou alterado.

## 04/10 — Auditoria do seletor anterior
**PASS.** `MainActivity` atribuía AI-01 e AI-02 automaticamente às primeiras abas com suporte a perfil WebView isolado. O usuário apenas confirmava as duas contas por caixas de seleção; não escolhia explicitamente os perfis.

## 05/10 — Política de seleção
**PASS.** Criada `AiAccountSelectionPolicy` para rejeitar índices inválidos, seleção da mesma aba, IDs vazios, listas inconsistentes e perfis duplicados.

## 06/10 — Testes unitários
**PASS (código de teste adicionado).** Criada `AiAccountSelectionPolicyTest` com casos de seleção válida, mesma aba, índices fora do intervalo, listas ausentes/inconsistentes, IDs vazios e perfis duplicados. Resultado de execução CI ainda não confirmado.

## 07/10 — Interface de escolha
**PASS.** O botão de primeiro contato agora abre seletores separados para AI-01 e AI-02, mostrando as abas abertas com perfis isolados. A associação escolhida é persistida no estado local do aplicativo.

## 08/10 — Validação interativa
**PASS.** O botão de confirmação fica desabilitado enquanto os dois seletores apontam para a mesma aba/perfil. A seleção só é gravada depois da validação da política.

## 09/10 — Limites de autenticação
**PASS.** O seletor não pede, lê, armazena ou automatiza e-mail/senha. Ele apenas mapeia sessões WebView já abertas. A verificação DOM continua exigindo composer e botão Enviar ativos nas duas sessões; autenticação continua sendo feita pelo próprio ChatGPT. A seleção visual não prova por si só que as contas pertencem a pessoas/identidades distintas.

## 10/10 — Veredito
**PASS para a implementação estática da seleção explícita; BLOCKED para CI final, backend hospedado e prova física.**

### Commits de implementação
- Política: `3c37d2bd9685c8d26672f1c7327a2541b3770596`
- Testes: `dc2cdc1642a6a7b24ad448f4cd585e044e68d1a9`
- UI: `867119121079b369bd8705b82d5c525e93abdbe1`
- Validação do seletor: `192881367721cbc98fc51da50e8d065fe115c3e7`

### Limites restantes
- O serviço Messenger não está hospedado no Render; o Blueprint atual é deliberadamente ephemeral/not-ready.
- O CI do SHA final não foi retornado pelos endpoints de status consultados; não declarar build/test PASS sem run verificável.
- O teste real exige duas sessões ChatGPT autenticadas e perfis WebView isolados no dispositivo.
- Não foi instalado APK, não houve Release, merge, deploy, criação de disco, mudança de secrets/variables ou ação física.
- AI-03 continua fora do escopo.
