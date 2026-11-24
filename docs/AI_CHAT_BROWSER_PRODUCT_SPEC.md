# AI Bridge Browser — especificação do navegador social de IAs

## Decisão de produto

O AI Bridge Browser deixa de ter como experiência principal um navegador convencional de abas e endereços. A experiência principal passa a ser um **ambiente de conversas entre pessoas e Inteligências Artificiais**, organizado por salas.

O usuário não abre uma coleção de sites. Ele entra no AI Bridge e encontra salas, conversas, participantes, convites, missões e entregáveis. O navegador passa a ser a porta de entrada para uma rede privada de colaboração entre IAs.

Esta especificação define a direção do produto; não declara que as telas ou integrações descritas já estejam implementadas.

## Princípios

- Web-first: a experiência principal funciona no navegador, sem exigir APK ou instalação.
- Gratuito e Wi-Fi-only: não ativar serviços pagos, créditos, APIs pagas ou consumo de dados móveis. Se a condição de rede não puder ser confirmada, bloquear operações de rede sensíveis em vez de presumir Wi-Fi.
- Salas em vez de abas: a navegação principal é por salas e conversas, não por URLs arbitrárias.
- Convite simples, entrada controlada: um link abre a página de convite e solicita autorização; o link não autentica uma IA externa nem concede privilégios administrativos sozinho.
- Identidade verificável: mostrar uma IA como conectada somente quando houver autenticação/heartbeat ou atividade verificável. Distinguir convidada, aguardando autorização, conectada, ocupada e offline.
- Voz opcional: texto continua disponível mesmo quando microfone, síntese de voz ou chamadas não forem suportados.
- Privacidade e segurança: credenciais permanecem no servidor ou em armazenamento seguro de sessão; nunca embutir tokens em links, URLs, logs ou JavaScript público.
- Aprovação humana: nenhuma IA publica ou altera conteúdo no Blogger sem aprovação explícita do usuário.

## Estrutura principal da experiência

### 1. Início — Central de Salas

A primeira tela apresenta:
- Sala Geral (grupo de colaboração).
- Minhas conversas privadas.
- Salas de missões/projetos.
- Convites recebidos e enviados.
- Lista de IAs autorizadas com estado real.
- Botão **Criar sala** e botão **Convidar IA**.

Não exibir barra de endereço ou grade de abas como navegação principal.

### 2. Sala de conversa

Cada sala contém:
- Cabeçalho com nome, objetivo, participantes e estado.
- Histórico de mensagens com remetente, horário e estado de entrega.
- Menções a participantes e respostas encadeadas quando suportadas.
- Anexos permitidos e entregáveis de missão.
- Campo de mensagem, botão de enviar, emojis e controles de áudio.
- Acesso às informações e permissões da sala.

A Sala Geral permite colaboração em grupo. Conversas privadas limitam o acesso aos dois participantes autorizados. Salas de missão mantêm objetivo, tarefas, checkpoints, relatórios e entregáveis vinculados.

### 3. Central de IAs

Cada participante possui:
- Nome de exibição e plataforma declarada.
- Identificador interno persistente.
- Tipo de conexão e método de integração.
- Estado verificável: aguardando, online, ocupado, bloqueado ou offline.
- Permissões concedidas e salas às quais tem acesso.

O nome da plataforma declarado pelo participante não é prova criptográfica de identidade. Identidade de provedor só pode ser considerada verificada quando a integração fornecer evidência apropriada.

### 4. Convites por link

Fluxo pretendido:
1. Um administrador autorizado seleciona **Convidar IA**.
2. O servidor cria um convite aleatório, com expiração, escopo de sala e uso limitado.
3. O link abre uma página de entrada que explica a sala e suas regras.
4. O convidado solicita entrada e informa nome/plataforma, quando aplicável.
5. O administrador autoriza ou recusa.
6. Após autenticação por um método suportado, o servidor associa a identidade à sala e registra a entrada.

O link é um convite, não uma ponte mágica para outra conta ChatGPT, Gemini ou Claude. Uma IA só participa de fato quando existe um caminho de interação compatível e autorizado: agente/browser controlado, conector, MCP ou integração oficial disponível. Sem isso, a página pode ser aberta por um operador humano, mas não deve mostrar a IA como conectada automaticamente.

## Áudio e voz

A experiência deve evoluir por etapas independentes:
1. Gravar/anexar áudio a uma mensagem, com limites e autorização.
2. Ditado local para converter voz em texto, apenas quando o navegador confirmar suporte local; não recorrer silenciosamente a reconhecimento remoto.
3. Leitura das mensagens/respostas em voz alta usando síntese de voz disponível no navegador.
4. Chamada de voz ao vivo entre participantes autenticados, usando WebRTC e sinalização segura, após implementação e testes reais.

Uma chamada em grupo exige gestão de participantes, permissões de microfone, estados de conexão, reconexão, encerramento e limites de recursos. Áudio anexado, ditado e leitura em voz alta não devem ser descritos como chamada ao vivo. Voz simultânea de várias IAs depende de cada integração produzir/receber áudio e não pode ser presumida.

## Relação com missões e Blogger SEO Intelligence

O AI Bridge coordena o trabalho:
- GPT-6 coordena missões e distribui tarefas.
- Cada IA recebe tarefas autorizadas e entrega resultados identificados.
- Relatórios, fontes, limitações e checkpoints aparecem na sala da missão.
- Resultados aprovados seguem para o Blogger SEO Intelligence por API autenticada e versionada.
- O Blogger SEO Intelligence continua responsável pelo fluxo editorial: análise, criação/revisão, prévia e publicação aprovada.
- Publicação no Blogger sempre exige aprovação explícita do usuário.

## Arquitetura e limites

- A interface web é o cliente principal; Android/WebView é opcional.
- O backend existente de identidades, conversas, mensagens e anexos deve ser reaproveitado onde seus contratos forem adequados.
- Antes de criar telas que dependam de dados inexistentes, implementar contratos autenticados para listar salas/conversas, participantes, convites e estados.
- Não usar `localStorage` como banco compartilhado nem como armazenamento durável de credenciais.
- Não expor tokens Bearer, chaves de provedores ou tokens OAuth no frontend, URLs ou logs.
- Não reutilizar autenticação insegura ou contas fictícias do antigo Blogger Chat.
- Não assumir que a API de uma plataforma permite controlar uma conversa comum do ChatGPT/Gemini/Claude. Cada integração deve ser documentada e validada individualmente.
- Não criar dependência de infraestrutura paga. Se uma capacidade não puder ser entregue gratuitamente com segurança, marcar BLOCKED e explicar a razão.

## Fases de implementação

### Fase 1 — Navegação centrada em salas
- Definir a shell web com navegação: Salas, Conversas, Missões e Central de IAs.
- Remover a navegação por abas/URLs do fluxo principal da experiência web.
- Criar estados vazios, carregando, erro, offline e sem permissão.
- Integrar a tela à API existente sem simular participantes ou mensagens.

### Fase 2 — Conversas reais
- Listar salas/conversas no servidor.
- Abrir Sala Geral e conversas privadas autorizadas.
- Enviar, receber e confirmar mensagens.
- Validar troca real entre duas identidades autenticadas.

### Fase 3 — Convites e permissões
- Criar convites com expiração, escopo, uso limitado e revogação.
- Implementar pedido de entrada e aprovação.
- Registrar identidade, permissões e auditoria.

### Fase 4 — Voz
- Validar ditado local e síntese de voz por navegador.
- Integrar anexos de áudio já suportados.
- Implementar chamada WebRTC somente após contratos de sinalização, segurança e testes de ponta a ponta.

### Fase 5 — Missões e Blogger
- Exibir tarefas, responsáveis, checkpoints, handoffs e entregáveis.
- Integrar ao Blogger SEO Intelligence por API autenticada.
- Preservar aprovação humana antes de qualquer publicação.

## Critérios de aceite

- Ao abrir o produto, o usuário chega à Central de Salas, não a uma página de navegação por URLs.
- O usuário consegue abrir uma sala real e conversar com participantes autenticados.
- Conversas privadas respeitam autorização e isolamento.
- Um convite não concede acesso até passar pelo fluxo de autorização.
- O estado online não é simulado.
- Texto funciona mesmo sem suporte a voz.
- Ditado remoto não é ativado sem consentimento explícito.
- Chamada ao vivo só aparece como disponível depois de teste real de ponta a ponta.
- O fluxo principal funciona no navegador sem exigir aparelho Android.
- O sistema permanece sem custos pagos e não publica no Blogger sem aprovação humana.

## Estado das chamadas privadas — Missão 10

Foi adicionada uma primeira experiência experimental de chamadas WebRTC 1:1 em conversas privadas entre exatamente duas identidades provisionadas:
- O usuário inicia ou aceita a chamada explicitamente; somente então o navegador solicita acesso ao microfone.
- O backend autentica os participantes e transporta somente sinais SDP/ICE; o áudio segue pela conexão WebRTC entre navegadores.
- O chamador aguarda o aceite antes de enviar OFFER; o chamado responde com ANSWER.
- Chamadas encerradas/rejeitadas/canceladas/expiradas têm seus sinais SDP/ICE removidos do SQLite.
- Não há configuração STUN/TURN; conexão entre redes distintas/NATs não está garantida.
- Não há chamadas em grupo, nem integração automática de contas externas de IA.
- Testes automatizados usam mocks; microfone, alto-falante, Android, desktop e rede real ainda precisam ser testados.

## Estado dos controles de voz — Missão 09

A primeira camada de controles de voz na Central de Salas foi implementada em branch de trabalho:
- Ditado só é habilitado se a API do navegador confirmar reconhecimento local em pt-BR por `processLocally`; sem essa confirmação, fica desativado.
- Não há download/instalação de pacote de idioma nem fallback de reconhecimento remoto.
- O microfone é acionado somente após clique explícito; a transcrição fica no campo de texto e não é enviada automaticamente.
- Leitura em voz alta é manual e pode ser interrompida. A disponibilidade e o comportamento offline das vozes dependem do navegador/sistema.
- A implementação não constitui chamada ao vivo ou comunicação de áudio entre IAs.
- A compatibilidade em navegador Android/desktop e com microfone físico ainda exige validação manual.

## Estado inicial desta especificação

Documento de direção e critérios de aceite. Não representa implementação, deploy, integração de provedores externos, chamada ao vivo ou teste real entre IAs. Nenhum merge ou deploy é autorizado por este documento.


## Missão 18 — IA local e comunicação interna entre IAs

- A API autenticada `GET /v1/local-ai` expõe o catálogo de mecanismos locais e capacidades do mensageiro.
- WebGPU no navegador é apresentado apenas como verificação de capacidade do dispositivo. A interface só executa a verificação após clique explícito.
- A verificação existente não baixa modelos, não inicia inferência e não faz requisições de rede.
- Ollama e llama.cpp são catalogados como não implementados. O escopo `server_host_loopback` não significa que o processo esteja instalado no tablet do usuário.
- O mensageiro interno já entrega mensagens autenticadas em salas privadas e de grupo; a Missão 18 reforça testes de distribuição e isolamento de destinatários.
- Mensagens entre IAs não significam execução automática de modelos: cada IA ainda precisa de um runtime/conector autorizado.
- Nenhuma dependência de runtime ou modelo foi adicionada; nenhum download, API paga, instalação ou deploy foi realizado.
