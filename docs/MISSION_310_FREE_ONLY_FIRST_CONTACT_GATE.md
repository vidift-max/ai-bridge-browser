# M310 — bloqueio de primeiro contato sob política 100% gratuita

Data: 2026-11-27

## Decisão obrigatória
- Orçamento autorizado: US$ 0/mês.
- Não solicitar cartão, billing, upgrade ou plano pago.
- Escopo: somente AI-01 e AI-02.
- Nenhum serviço, disco ou deploy pago pode ser provisionado.
- AI-03 permanece fora do escopo.

## Auditoria realizada
1. **PASS** — PR #242 permanece OPEN / Draft / não merged; branch `feat/mission-295-m241-ai-first-contact-integration`; HEAD auditada `eddfb92f989884a155c3ed477ac94da4376d043d`.
2. **PASS** — Confirmado que o backend atual implementa autenticação por dois tokens independentes, convites direcionados, aceite, membership, envio, sincronização e acknowledgements.
3. **PASS** — Confirmado que o armazenamento do backend é SQLite via `SQLiteMessengerStore`; o backend não possui adaptador PostgreSQL, Supabase ou Durable Objects nesta HEAD.
4. **PASS** — Confirmado que `RuntimeConfig.validate_storage_contract()` rejeita explicitamente `MESSENGER_STORAGE_MODE=ephemeral`; não é correto contornar a verificação usando armazenamento efêmero como se fosse durável.
5. **PASS** — Confirmado que o `render.yaml` atual ainda declara plano pago `0.5c-512mb` e disco de 1 GB; essa configuração não deve ser aprovada sob a política US$ 0.
6. **PASS** — Inventário do workspace Render `AI-PHONE-02` confirmou que o serviço `ai-messenger-experimental` não existe. Serviços gratuitos existentes pertencem a outros projetos e não foram alterados ou reutilizados.
7. **PASS** — Blueprint `exs-dc4t6huc6qcc73esomlg` permanece sem aprovação; o planejamento anterior retornou `need_payment_info`; nenhum recurso ou deploy foi criado.
8. **PASS** — Confirmado que o APK DEBUG do M307 não prova conectividade real; os convites são links de texto colados manualmente, e a integração exige backend hospedado e credenciais individuais.
9. **BLOCKED** — Nenhum provedor gratuito com armazenamento persistente foi conectado/configurado para este backend. Render Free sozinho não fornece disco persistente e não pode ser tratado como armazenamento confiável para o SQLite atual.
10. **BLOCKED** — Primeiro contato bidirecional AI-01 → AI-02 → AI-01 não pode ser declarado nem liberado até existir backend gratuito persistente, duas credenciais provisionadas com segurança, endpoint operacional e teste real nos dois perfis/dispositivos.

## Veredito
- **NO-GO:** aplicar o Blueprint Render pago.
- **NO-GO:** implantar SQLite em filesystem efêmero e afirmar persistência.
- **BLOCKED:** primeiro contato real entre AI-01 e AI-02.
- **PASS:** contenção de custos; nenhum cartão, upgrade, serviço pago, disco pago, deploy ou alteração em serviços existentes.
- **Não houve:** merge, Release, instalação, acesso a aparelho, exposição de tokens ou alteração de Secrets/Variables.

## Próximo caminho técnico gratuito
Migrar a camada de persistência para um provedor gratuito com banco durável, mantendo o contrato HTTP e os controles de autenticação/membership. Alternativas a validar antes de qualquer provisionamento:
- Supabase Free/Postgres: exige projeto e credenciais do usuário; validar pausa por inatividade, limites e política vigente.
- Cloudflare Workers + Durable Objects/SQLite: armazenamento durável e canal em tempo real, mas exige adaptação do backend Python para TypeScript/JavaScript e acesso autorizado à conta Cloudflare.
- Não selecionar ou provisionar provedor sem verificar os limites gratuitos vigentes e sem comprovar que não haverá cobrança automática.

## Próximo gate de liberação
1. Implementar e testar o adaptador para o provedor gratuito escolhido.
2. Provisionar somente recursos gratuitos, com alertas/limites de uso quando disponíveis.
3. Configurar tokens AI-01 e AI-02 diretamente no cofre seguro dos dispositivos; nunca registrar valores no GitHub ou chat.
4. Validar health/readiness, persistência após reinício, isolamento de identidades, convite/aceite e autorização.
5. Executar prova bidirecional real AI-01 → AI-02 → AI-01 nos dois perfis.
6. Somente então atualizar o status para **FIRST CONTACT PASS**.

Este relatório não declara o primeiro contato liberado. Ele registra o bloqueio técnico sem violar a regra permanente de custo zero.
