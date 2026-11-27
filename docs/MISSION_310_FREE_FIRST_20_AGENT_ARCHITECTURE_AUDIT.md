# M310 — arquitetura gratuita e central de 20 agentes
Data: 2026-11-27
Branch de trabalho: `feat/mission-295-m241-ai-first-contact-integration`
PR relacionada: #242 (OPEN / Draft / não merged)

## Objetivo
Preparar a evolução do AI Bridge Browser como aplicativo Android independente, gratuito no uso essencial e capaz de coordenar até 20 agentes lógicos em uma sala compartilhada. O usuário trabalha exclusivamente por tablet Android; build, testes e geração de APK devem ocorrer em GitHub Actions, sem exigir computador local.

## Rodadas
### 01/10 — auditoria da identidade independente
**PASS (código inspecionado).**
- `app/build.gradle.kts`: `applicationId` e `namespace` = `com.vidiftmax.aibridgebrowser`.
- `app/src/main/AndroidManifest.xml`: label = `AI Bridge Browser`; launcher = `.MainActivity`.
- O workflow Android inclui verificações do package ID, label e launcher, e rejeita launchers AI-PHONE/Messenger.
- Isso demonstra separação de identidade no código/contrato de build; ainda exige APK e instalação física para validar o produto final no tablet.

### 02/10 — auditoria de custos da infraestrutura
**BLOCKED (requisito de gratuidade não atendido pela configuração atual).**
- `render.yaml` declara Render `plan: 0.5c-512mb` e disco persistente de 1 GB.
- `docs/MISSION_309_RENDER_PERSISTENT_STAGING.md` registra estimativa mínima de US$ 7,25/mês e que o Blueprint retornou `need_payment_info`; nenhum serviço/disco foi provisionado.
- Regra do produto: não adicionar cartão, não sincronizar esse Blueprint, não criar serviço/disco pago e não depender de Render pago.
- A substituição gratuita precisa ser projetada e validada antes de habilitar o backend remoto; armazenamento efêmero não pode ser anunciado como persistente.

### 03/10 — modelo de 20 agentes
**PASS (requisito arquitetural; implementação ainda pendente).**
- A estratégia existente `docs/MULTI_AI_MISSION_ROOM_STRATEGY.md` já descreve agentes registrados, missões individuais, sala compartilhada, checkpoints, relatórios e agregação.
- O requisito novo é fixar 20 agentes lógicos identificados (AI-01…AI-20) como capacidade-alvo.
- Agente lógico não equivale a uma conta externa ou WebView aberta. O coordenador deve escalonar execução e limitar sessões simultâneas para proteger memória/bateria do tablet.
- Nenhum agente recebe automaticamente acesso de escrita ao GitHub; permissões são separadas da participação na sala.

### 04/10 — limite de sessões no tablet
**PASS (decisão de capacidade, implementação pendente).**
- O README atual descreve até seis abas WebView.
- A meta de 20 agentes não exige 20 WebViews simultâneas. A sala pode manter 20 identidades/filas/estados e ativar somente as sessões necessárias.
- Perfis de sessão múltiplos dependem de `WebViewFeature.MULTI_PROFILE`; a própria documentação do projeto marca validação física no Galaxy Tab A7 como pendente.

### 05/10 — modelo de execução gratuita
**PENDENTE.** Comparar execução local, Firebase Spark/free tier e outras opções sem assumir limites, persistência ou disponibilidade não verificados. Nenhuma dependência obrigatória de API paga.

### 06/10 — persistência e recuperação
**PENDENTE.** Definir armazenamento local durável no Android e sincronização opcional gratuita, exportação/importação e recuperação de missão sem exigir backend pago.

### 07/10 — sala compartilhada e chats privados
**PENDENTE.** Definir autorização por AI_ID, isolamento de conversas privadas, ordem de mensagens, ACK, retomada e proteção contra duplicatas para 20 agentes.

### 08/10 — fila, escalonamento e limites
**PENDENTE.** Definir limites de concorrência, backpressure, timeouts, cancelamento, retomada e prioridade para não sobrecarregar o tablet.

### 09/10 — testes de contrato e desempenho
**PENDENTE.** Adicionar testes automatizados para 20 identidades lógicas, isolamento, fila, recuperação e limites de concorrência; medir uso de memória em dispositivo antes de declarar capacidade.

### 10/10 — APK independente e evidência de dispositivo
**PENDENTE.** Build APK pelo GitHub Actions, verificar package/label/launcher/assinatura/hash, disponibilizar artefato e orientar instalação pelo tablet somente após autorização. Teste físico e compatibilidade de assinatura continuam gates obrigatórios.

## Regras permanentes
1. AI Bridge Browser é produto separado do AI Phone: package, ícone, nome, instalação e atualizações próprios.
2. Recursos essenciais gratuitos; nenhuma cobrança ou cartão obrigatório.
3. Não provisionar Render pago nem sincronizar o Blueprint M309.
4. 20 agentes lógicos como meta; concorrência de sessões é limitada por capacidade real do dispositivo.
5. Não confundir CI com teste físico; não afirmar isolamento de contas sem prova no tablet.
6. Sem merge, Release oficial, instalação, deploy ou alteração de Secrets/Variables sem autorização explícita.
7. Todo progresso deve citar SHA, run e evidência verificável.

## Estado desta missão
- Rodadas concluídas: 01/10.
- Rodada 02: bloqueio de custo identificado; solução ainda não implementada.
- Nenhum serviço pago provisionado; nenhum cartão/secret alterado; nenhum APK instalado.
