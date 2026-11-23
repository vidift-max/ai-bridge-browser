# Ponte de áudio digital entre duas IAs — contrato inicial

Status: ESPECIFICAÇÃO PREPARATÓRIA; NÃO IMPLEMENTADO
Branch: `feat/digital-ai-audio-bridge-contract`
Base: `caa112af5f5831b89c9560b5da88580b2076a8c4`

## 1. Objetivo

Permitir que o operador humano seja o gatilho e controlador de uma conversa entre dois provedores de IA, encaminhando áudio digital diretamente entre adaptadores de API. O caminho de áudio entre as IAs não deve depender de microfone físico, alto-falante, captura de áudio do Android, MediaProjection ou injeção de áudio em WebView.

Fluxo pretendido:

`OPERADOR_INICIA -> ADAPTER_A -> AUDIO_DIGITAL -> ADAPTER_B -> RESPOSTA -> AUDIO_DIGITAL -> ADAPTER_A`

O operador pode pausar, retomar ou encerrar a sessão. A implementação deve ser estritamente consentida e visível.

## 2. Limite fundamental de integração

Uma conversa aberta no aplicativo/site ChatGPT não é, por si só, um endpoint de API acessível ao APK. O APK não pode anexar-se à sessão interna desta conversa, ler seu áudio interno, ou comandar a interface do ChatGPT.

Cada lado precisa de um adaptador autorizado:
- API oficial do provedor com entrada e saída de áudio; ou
- outro endpoint documentado e autorizado pelo proprietário do serviço.

Se o provedor oferecer apenas texto, o adaptador deve declarar `AUDIO_INPUT=false` e/ou `AUDIO_OUTPUT=false`. Não se deve fingir que existe voz: a sessão pode usar texto como fallback somente se o operador aceitar esse modo.

Nenhuma automação de UI, captura silenciosa, contorno de proteção do Android ou extração de sessão/cookies é permitida.

## 3. Arquitetura lógica

- `HumanTriggerController`: start, pause, resume, stop e aprovação de modo.
- `BridgeSessionCoordinator`: identidade da sessão, estado global, timeouts e encerramento.
- `AiProviderAdapter`: contrato comum para os dois provedores.
- `AudioFormatNegotiator`: negociação de codec, taxa de amostragem, canais, framing e limites.
- `TurnScheduler`: alternância A/B; uma resposta por turno; sem concorrência por padrão.
- `AudioRelay`: encaminha bytes de áudio entre adaptadores, sem reproduzir o som no alto-falante.
- `SafetyBudgetGuard`: limites de duração, bytes, turnos e custo; gasto pago desabilitado por padrão.
- `SessionAuditLog`: metadados mínimos (estado, turno, duração, erros); não armazena áudio por padrão.

O WebRTC peer-to-peer já existente no AI Messenger é para chamadas entre dispositivos com microfone/alto-falante locais. Ele não substitui os adaptadores de API de IA e não deve ser confundido com esta ponte digital API-a-API.

## 4. Contrato mínimo do adaptador

Cada adaptador deve informar, antes de iniciar:
- `providerId`, `modelId` e `adapterVersion`;
- `supportsAudioInput`, `supportsAudioOutput`, `supportsTextInput`;
- formatos aceitos/produzidos e limites de duração/tamanho;
- modo de autenticação e validade da sessão;
- se a API exige sessão em tempo real, upload de arquivo ou mensagens por turnos;
- limites e indicação de custo conhecido/desconhecido.

Operações conceituais:
- `connect(sessionConfig)`
- `sendAudio(turnId, audioPayload, format)`
- `sendText(turnId, text)` (fallback explicitamente aprovado)
- `receiveOutput()`
- `interrupt(reason)`
- `close()`

O contrato é independente de SDK. Os nomes acima são especificação, não classes já existentes.

## 5. Máquina de estados

`IDLE -> VALIDATING -> READY -> A_SPEAKING -> RELAY_TO_B -> B_SPEAKING -> RELAY_TO_A -> A_SPEAKING`

Estados transversais: `PAUSED`, `STOPPING`, `STOPPED`, `ERROR`.

Regras:
1. A sessão só começa após o operador pressionar INICIAR e os dois adaptadores passarem pela validação.
2. Por padrão, somente um lado gera áudio por vez.
3. O áudio de saída de A vira entrada digital de B; não passa por alto-falante/microfone.
4. O áudio de saída de B vira entrada digital de A.
5. Cada turno possui ID único, sequência, timeout e limite de bytes/duração.
6. Pausar interrompe novas transmissões e solicita interrupção aos dois adaptadores.
7. Parar fecha sessões, descarta buffers pendentes e revoga credenciais temporárias quando suportado.
8. Repetição de turnId, loop de conteúdo, timeout ou limite excedido interrompe a sessão e exige ação do operador.

## 6. Segurança e privacidade

- Chaves permanentes nunca ficam no APK.
- Credenciais temporárias devem ser emitidas por backend confiável, com escopo e validade mínimos.
- Não registrar áudio/transcrições por padrão.
- Não transmitir antes do gatilho humano.
- Exibir claramente qual IA está falando e para qual IA o áudio está sendo enviado.
- Botão STOP deve funcionar localmente mesmo se a rede falhar.
- Sem infraestrutura paga ou chamadas pagas sem autorização explícita.
- O limite de custo inicial é zero: se um adaptador exigir serviço pago ou preço não confirmado, ele fica desativado.

## 7. Gate de compatibilidade antes da implementação

A ponte só pode passar para implementação executável quando ambos os lados fornecerem:
1. provedor e modelo exatos;
2. documentação oficial da API autorizada;
3. suporte confirmado a áudio de entrada e saída, ou aceite explícito de fallback de texto;
4. formatos de áudio e limites;
5. autenticação viável sem segredo no APK;
6. preço/condição de uso confirmado e autorização para qualquer custo.

O relatório do segundo provedor ainda é necessário. Até recebê-lo, não escolher endpoint, modelo, codec definitivo, SDK, nem afirmar interoperabilidade.

## 8. Plano de validação

- Teste unitário do agendador de turnos e da máquina de estados.
- Teste de payload inválido, áudio acima do limite, timeout, interrupção e reconexão.
- Teste de loop/eco lógico por IDs de turno e limite de repetição.
- Teste com adaptadores simulados sem rede e sem custo.
- Teste de integração com cada API somente após autorização e confirmação de custo.
- Teste final reproduzível A -> B -> A, com logs de metadados e sem microfones/alto-falantes físicos.

## 9. Estado honesto

- Contrato de arquitetura: DOCUMENTADO nesta branch.
- Adaptadores OpenAI/segundo provedor: NÃO IMPLEMENTADOS.
- Sessão ChatGPT atual conectável diretamente: NÃO.
- Encaminhamento digital API-a-API: NÃO IMPLEMENTADO.
- Integração com o WebRTC peer engine do AI Messenger: NÃO É EQUIVALENTE; não foi feita.
- APK com ponte digital funcional: NÃO GERADO.
- Teste A -> B -> A: NÃO EXECUTADO.
- Custo: nenhuma chamada paga ou infraestrutura criada.
