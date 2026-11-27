# M309 — preparação de hospedagem persistente do AI Messenger

Data: 2026-11-27

## Rodadas 01/10 a 10/10

1. **PASS** — Confirmado o workspace Render correto: `AI-PHONE-02` (`tea-d6ei0upr0fns73clu8og`), na região de Oregon.
2. **PASS** — Inventário somente leitura confirmou que não existe serviço `ai-messenger-experimental` nesse workspace; serviços existentes do AI-PHONE-02 e outros projetos não foram alterados.
3. **PASS** — Revisado o contrato de configuração do servidor: duas credenciais bearer distintas, AI_IDs distintos, TLS encerrado na borda Render e SQLite em caminho abaixo da raiz persistente.
4. **PASS** — Confirmado que o serviço gratuito não suporta disco persistente; o menor plano de serviço com disco é `0.5c-512mb`.
5. **PASS** — Confirmado custo de referência atual: compute `0.5c-512mb` = US$ 7/mês; SSD persistente 1 GB = US$ 0,25/GB/mês; estimativa mínima = **US$ 7,25/mês**, sem contar eventual excedente de banda/build.
6. **PASS** — Atualizado `render.yaml` para serviço Python em Oregon, uma instância, plano mínimo compatível, build compilando `server`, start usando `PORT` e auto-deploy condicionado a checks pass.
7. **PASS** — Configurado disco persistente de 1 GB em `/var/data`, com banco SQLite `/var/data/messenger.sqlite`, modo `persistent` e raiz validada `/var/data`.
8. **PASS** — Configuradas duas credenciais independentes geradas pelo Render (`generateValue: true`), identidades fixas `AI-01` e `AI-02`, TLS de borda e URL pública auto-referenciada via `RENDER_EXTERNAL_URL`. Nenhum segredo foi lido, exibido ou versionado.
9. **BLOCKED** — Criado Blueprint Render `exs-dc4t6huc6qcc73esomlg` no workspace AI-PHONE-02, com `autoSync=false` e política `create_new` para não adotar/alterar serviços existentes. O planejamento retornou `need_payment_info`; nenhum serviço, disco ou deploy foi criado.
10. **PASS (contenção)** — Mantido o Blueprint sem aprovação; nenhuma alteração foi aplicada no Render. A próxima tentativa depende de adicionar/confirmar informação de cobrança no workspace e então replanejar/aprovar o sync.

## Evidências

- Commit de infraestrutura: `30b5ec4f805ea15a34868a6be6f547a7eaafa395`.
- Blueprint ID: `exs-dc4t6huc6qcc73esomlg`.
- Workspace: `AI-PHONE-02` / `tea-d6ei0upr0fns73clu8og`.
- Blueprint branch: `feat/mission-295-m241-ai-first-contact-integration`; path `render.yaml`.
- `autoSync=false`; `existingResources=create_new`.
- Planejamento Render: **FAILED / need_payment_info**; `sync=null`.

## Veredito

- **PASS:** configuração versionada e planejamento do Blueprint criado.
- **BLOCKED:** Render exige informação de cobrança antes de provisionar compute pago + SSD persistente.
- **NOT DEPLOYED:** nenhum serviço ou disco foi criado; nenhum deploy ocorreu.
- **CI do SHA** `30b5ec4f805ea15a34868a6be6f547a7eaafa395` **não comprovado** pelos endpoints disponíveis; o workflow do backend foi configurado para disparar no push de `render.yaml`, mas não há run verificável nesta consulta.
- Tokens gerados pelo Render, quando o sync for aprovado, precisarão ser copiados diretamente do painel para o cofre Keystore do AI-PHONE correspondente; não devem ser publicados no GitHub nem enviados em chat.
- Nenhum serviço existente foi alterado; sem merge, Release, instalação, secrets manuais, mudança de outros projetos ou ação física no aparelho.
- AI-03 permanece fora do escopo.

## Próximo passo operacional

No workspace AI-PHONE-02, abrir Render Dashboard → Billing e adicionar/confirmar os dados de cobrança. Depois disso, reexecutar o planejamento do Blueprint e revisar o custo estimado de US$ 7,25/mês antes de aprovar o sync.
