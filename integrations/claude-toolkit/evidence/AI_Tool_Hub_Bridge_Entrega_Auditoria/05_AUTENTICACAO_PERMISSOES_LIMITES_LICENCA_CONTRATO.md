# 05 — Autenticação, autorização, permissões, limites, logs, licença e contrato

## 1. Autenticação, identidade, autorização
**Estado: `BLOCKED — IDENTITY NOT TRUSTWORTHY`.**

| Aspecto exigido | Situação encontrada (verificada por busca e leitura do código) |
|---|---|
| Origem da identidade | Não existe. Nenhuma função recebe ou deriva `caller`/`principal`/`ai_id`/`user_id` |
| Validação de credencial, sessão, assinatura | Não existe |
| Autorização / escopo por ferramenta | Não existe. Qualquer código que importe o módulo chama qualquer função |
| Revogação, expiração, replay | Não existe |
| Permissões por ferramenta | Só documentação em texto (`PERMISSOES.md`, `API.md`: "Nenhuma"), sem declaração legível por máquina nem aplicação |
| Falsificação de identidade (teste) | **Não aplicável / não testável**: não há identidade a falsificar. Não executei esse teste e não afirmo que passou |

Não contornei a limitação. Qualquer bridge que repasse um `caller` enviado pelo cliente continuaria `BLOCKED`.

## 2. Permissões declaradas × observadas
`PERMISSOES.md` declara: sem rede, sem armazenamento, sem câmera/microfone/localização, sem bibliotecas externas; Python lê arquivos só na CLI e só os caminhos informados. Verificado por leitura: nenhuma chamada de rede, `fetch`, `XMLHttpRequest`, `localStorage` nem `eval`/`new Function` nas ferramentas; único `innerHTML` em `app.js:134` (saída do gráfico). **Ressalva:** a CSP da demo só tem `connect-src/form-action/base-uri` (F-12), então a afirmação "bloqueia requisições de rede" é mais forte que a política real.

## 3. Limites (tabela completa)
| Ferramenta | Limites existentes | Limites ausentes |
|---|---|---|
| duration_timer | máx. 7 dias (`parse`/`Timer`); ≥ 0 | tamanho do texto (F-02); `format_duration` sem teto (F-04); magnitude de inteiros no formato `h:m` (F-01) |
| recipe_scaler | quantidade finita ≥ 0; porções > 0; 10 unidades | nº de ingredientes (5.000 aceitos), magnitude (F-01), tamanho de nomes |
| quiz_engine | ≥ 2 opções por pergunta; ids únicos | nº de perguntas/opções (5.000 aceitas), tamanho de textos (200 KB aceitos) |
| svg_chart | 1–50 rótulos, 1–6 séries, 200–2000 × 150–2000 px, valores finitos ≥ 0, título 120, rótulo 20, nome 14 | magnitude de valores (F-01), inteiros em formato decimal (F-08) |
| link_card | URL ≤ 2048, título 120, descrição 300, só http/https, sem credenciais | política de hosts (F-17) |
| Rate limit / payload máximo | **nenhum** | tudo (F-14) |

## 4. Logs
Não há logging nas ferramentas. A CLI Python imprime `CÓDIGO: mensagem` no stderr; as mensagens de erro podem repetir o texto de entrada (ex.: duração inválida). Não há chave/token/cookie/sessão manipulados, então nenhum segredo é registrado hoje; porém **não há política de redação** para quando o bridge existir. Verificado por busca no código: nenhuma gravação de log e nenhum acesso a credenciais.

## 5. Schemas, manifests, discovery
Não existem JSON Schemas nem manifests por ferramenta (nome, versão, entrada, saída, campos obrigatórios/opcionais, permissões) e não existe capability discovery. Existe: `MANIFESTO.json` (inventário de arquivos com SHA-256; 54 itens conferidos), `API.md` (contrato em prosa; precisa correção, F-13). Versão única `0.1.0`. Entradas inválidas **obrigatórias** são rejeitadas de forma previsível com código estável (centenas de casos MATCH); **opcionais** de tipo errado são descartadas em silêncio (F-11).

## 6. Licença e titularidade
**Estado: `BLOCKED — LICENSE/AUTHORIZATION UNCLEAR`.** Nenhum `LICENSE`, nenhum aviso de copyright, nenhum autor humano identificado; `LIMITACOES.md`: "Nenhuma licença foi definida… Defina uma antes de redistribuir ou integrar." Os arquivos do pacote têm data de geração de 2026-11-28 e o texto diz que o código foi escrito do zero para o pacote e que não contém código da Anthropic nem de terceiros; **não verifiquei isso por comparação com nenhuma fonte** e não tenho como atestar a origem. Não invento licença. Não recomendo publicar como integração final até o titular escolher a licença ou declarar a titularidade.

## 7. Contrato `AI_TOOL_BRIDGE.md`
| Item | Valor |
|---|---|
| Arquivo recebido | `AI_TOOL_BRIDGE.zip` (377 bytes, SHA-256 `29593dfa38016a2b4ef93720a6e639526dde934d7bc918ea56c5b331fba06782`) contendo `AI_TOOL_BRIDGE.md` |
| Bytes do contrato | 418 |
| **SHA-256 do contrato** | `11370ef47ca1cabdb155dc5b19507218f8997061dd7d8a05c71e586ff3ef11dc` |
| Git blob SHA-1 calculado | `5ae9cac212b6ff901b39105effa1c124e7541e67` |
| Blob SHA citado para `docs/AI_TOOL_BRIDGE.md` no repositório (histórico) | `8ea000f51981b7f45ae34a4be37adee0417f8809` → **não confere** |
| Hash esperado | não existe |
| Resultado | `BLOCKED` |
Conteúdo (3 parágrafos, em português): a IA externa só usa ferramentas por interface autorizada; a ponte deve expor discovery, autenticação, contratos, schemas, escopo de permissões e erros/limites; chamadas não documentadas ou não autorizadas são rejeitadas. É um conjunto de princípios, **não um contrato técnico**. Nenhum contrato técnico completo foi fornecido.
