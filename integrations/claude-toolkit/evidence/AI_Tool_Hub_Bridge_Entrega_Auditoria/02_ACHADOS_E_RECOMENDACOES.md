# 02 — Achados e recomendações

Fase **somente leitura**: nenhum código do pacote foi alterado, nenhuma correção foi aplicada, não houve commit/push. As recomendações abaixo são **propostas**, não correções feitas. Todos os "casos" citados (IDs) estão em `03_MATRIZ_PARIDADE.md` e `tests_auditoria/`.

Severidade: **BLOQUEANTE** (impede integração), **ALTA**, **MÉDIA**, **BAIXA**, **INFO**.

## Resumo

| ID | Sev. | Ferramenta | Achado |
|---|---|---|---|
| F-14 | BLOQUEANTE | todas | Não existe camada de bridge: sem autenticação, autorização, rate limit, logs, manifests/schemas por ferramenta nem capability discovery |
| F-15 | BLOQUEANTE | todas | Licença/titularidade indefinidas |
| F-16 | BLOQUEANTE | contrato | Contrato `AI_TOOL_BRIDGE.md` é só um resumo de 418 bytes; sem hash esperado; blob SHA diverge do repositório |
| F-02 | ALTA | duration_timer | Tempo quadrático em `parse_duration` (sem limite de tamanho de entrada) |
| F-01 | ALTA/MÉDIA | recipe_scaler, svg_chart, duration_timer, CLI | Overflow numérico: Python lança exceção não controlada; JS devolve `Infinity`/`null` em silêncio |
| F-09 | MÉDIA | link_card | URL normalizada de forma diferente em Python e JS (44 divergências) |
| F-06 | MÉDIA | svg_chart | Rótulos numéricos, espaços e truncamento diferem entre Python e JS (14 casos) |
| F-03 | MÉDIA | duration_timer | Python aceita dígitos Unicode; JS não (5 casos) |
| F-08 | MÉDIA | svg_chart | `width`/`height` como `640.0`/`1e3`: JS aceita, Python recusa (8 casos) |
| F-11 | MÉDIA | todas | Sem limites de payload; tipos errados em campos opcionais são descartados em silêncio |
| F-07 | BAIXA | svg_chart | SVG gerado pode não ser XML bem formado (U+FFFE/FFFF, substituto solitário) |
| F-04 | BAIXA | duration_timer | `format_duration`: estilo `null` e segundos gigantes divergem |
| F-05 | BAIXA | recipe_scaler | `format_amount(1e21)` diverge |
| F-10 | BAIXA | adapters | Número errado de argumentos: Python lança `TypeError`, JS ignora |
| F-12 | BAIXA | demo/docs | Saídas de quiz/receita não escapadas; CSP da demo incompleta |
| F-13 | BAIXA | docs | `API.md` afirma comportamento idêntico nas duas linguagens; os testes mostram o contrário |
| F-17 | INFO | link_card | Sem política para hosts internos (`localhost`, `169.254.169.254`) |

**Segurança de injeção em SVG e HTML: nenhum achado.** Veja a seção "O que passou" no final.

---

## F-14 — BLOQUEANTE — Não há bridge (autenticação, autorização, limites, logs, schemas, discovery)

**Evidência (executada agora):** busca por `caller`, `principal`, `ai_id`, `user_id`, `bearer`, `token`, `api key`, `rate limit`, `session`, `cookie`, `secret`, `log` nos `.py`/`.js` das ferramentas: **0 ocorrências**. O pacote não tem schemas JSON, manifests por ferramenta nem endpoint de discovery. O `MANIFESTO.json` é um inventário de arquivos (54 arquivos com SHA-256; todos conferem — ver `logs/execucao_agora.log`).
**Consequência:** a identidade de quem chama não é derivada de nada. Não há nada a "validar": é uma biblioteca local. Qualquer integração que repasse um `caller` livre estaria fora do que a missão permite.
**Estado:** `BLOCKED — IDENTITY NOT TRUSTWORTHY` (ver `05_...`).
**Recomendação:** o bridge precisa ser escrito: identidade vinda de credencial verificada no servidor (não do corpo da requisição), escopos por ferramenta, expiração/revogação/anti-replay, limite por chamador e por período, teto de payload, logs com redação de segredos, `schema` + `manifest` por ferramenta, discovery. Isso é trabalho novo, não está no pacote.

## F-15 — BLOQUEANTE — Licença/titularidade
**Evidência:** nenhum arquivo `LICENSE*`; nenhum cabeçalho de copyright; `LIMITACOES.md` §4 diz "Nenhuma licença foi definida"; §1 diz que o código foi "escrito do zero para este pacote". Não há registro de autor humano nem de autorização explícita.
**Estado:** `BLOCKED — LICENSE/AUTHORIZATION UNCLEAR`. Não invento licença. Decisão pendente do titular (você).

## F-16 — BLOQUEANTE — Contrato do bridge
**Evidência:** `AI_TOOL_BRIDGE.md` enviado: 418 bytes, SHA-256 `11370ef47ca1cabdb155dc5b19507218f8997061dd7d8a05c71e586ff3ef11dc`; git blob SHA-1 calculado `5ae9cac2…`, enquanto o inventário histórico do repositório cita `8ea000f5…` para `docs/AI_TOOL_BRIDGE.md`. **Não são o mesmo conteúdo** (ou o arquivo enviado é outra versão/traduzido). Não existe hash esperado para comparar; o contrato técnico completo não foi encontrado.
**Estado:** `BLOCKED` (nem PASS nem FAIL de hash).

## F-02 — ALTA — Tempo quadrático em `parse_duration`
**Reprodução (executada):** `parse_duration("1"*N + "x")`. A regex `(\d+(?:\.\d+)?)\s*([dhms])` é reavaliada a partir de cada posição.

| N | Python | JavaScript |
|---:|---:|---:|
| 2.000 | 0,13 s | 0,013 s |
| 4.000 | 0,48 s | 0,039 s |
| 8.000 | 2,1 s | 0,18 s |
| 16.000 | 8,2 s | 0,65 s |
| 32.000 | **31,9 s** | 2,55 s |

Dobrar a entrada quadruplica o tempo. Não há limite de tamanho de string. Em um servidor, uma única requisição de ~32 KB prende uma CPU por ~30 s (Python). Em uma execução anterior, uma entrada de 200 mil caracteres travou meu comando por mais de 5 minutos (interrompido pelo ambiente).
**Recomendação (proposta):** limitar o texto a poucas dezenas de caracteres antes de qualquer regex; trocar a varredura por um analisador linear; teto de payload no bridge.

## F-01 — ALTA/MÉDIA — Overflow numérico sem tratamento
Números **finitos** muito grandes passam na validação e quebram depois.
- **Python** lança exceção não controlada (não é `ToolError`): `OverflowError` em `svg_chart` com valor `1e308` (ids 297–300), rótulo `1e309` (263), inteiro de 400 dígitos (311–312); em `recipe_scaler` (ids 75, 105, 119, 137); `ValueError` em `parse_duration("9"*5000+":00")` (limite de 4300 dígitos do `int()`); na CLI `python -m ai_tool_hub chart` com `NaN` no rótulo ou `1e308` no valor: traceback e exit code 1 (executado).
- **JavaScript** não quebra, mas devolve lixo: gráfico com `1e308` contém o texto `Infinity` nos rótulos do eixo (verificado); `scaleRecipe` com `amount: 1e308` devolve `Infinity`, que vira `null` em JSON.
**Consequência:** comportamento diferente entre linguagens e erro não previsível. Falta o teto de magnitude e o teste do resultado calculado (`isfinite`) antes de formatar.
**Recomendação:** limitar magnitudes na entrada (ex.: valores e quantidades até um máximo documentado), verificar o resultado, e converter qualquer exceção em `ToolError` com código estável.

## F-09 — MÉDIA — `link_card`: URL normalizada de forma diferente
O JS usa o parser `URL` (padrão WHATWG); o Python usa `urlsplit` e monta a URL à mão. 44 de 157 casos de `link_card` divergem (ids em `03_...`). Exemplos (todos executados):

| Entrada | Python | JavaScript |
|---|---|---|
| `http://127.1/` | `127.1` | `127.0.0.1` |
| `http://0x7f.1/`, `http://2130706433/`, `http://0177.0.0.1/` | mantém | `127.0.0.1` |
| `http://256.256.256.256/`, `http://1.2.3.4.5/` | aceita | `INVALID_URL` |
| `http://[0:0:0:0:0:0:0:1]/` | mantém | `[::1]` |
| `http://[fe80::1%25eth0]/` | aceita | `INVALID_URL` |
| `http://[v1.fe]/` | vira `http://v1.fe/` (remove os colchetes, muda o host) | `INVALID_URL` |
| `http://example.com/a/../b` | mantém | `/b` |
| `http://evil.com\@good.com` | `CREDENTIALS_IN_URL` | aceita, host `evil.com` |
| `https://exam\u00a0ple.com` | aceita | `INVALID_URL` |
| `http://bücher.de/` | mantém (documentado) | `xn--bcher-kva.de` |
| `http://example.com/?` e `/#` | descarta `?`/`#` vazios | mantém |
| caracteres não ASCII, `"<>` no caminho/consulta | mantém | codifica em `%XX` |

**Consequência de segurança:** o HTML gerado é seguro nos dois lados (ver "O que passou"). Mas qualquer política baseada em host (lista de permissão/bloqueio de IPs) aplicada à saída Python seria contornável por `127.1`/`0x7f.1`/decimal, porque o Python não canonicaliza IPv4.
**O caso histórico `[::1]` está correto nos dois lados** (id 364: MATCH, host `[::1]`).
**Recomendação:** decidir qual é a referência (WHATWG, como os navegadores) e implementar o mesmo algoritmo nos dois lados, ou definir contrato mais estrito (aceitar só hosts ASCII em forma canônica) e rejeitar o resto em ambos.

## F-06 — MÉDIA — `svg_chart`: texto dos rótulos difere
- Rótulo numérico: Python formata com 2 casas, JS usa o número como está. `3.14159` → Python `3.14`, JS `3.14159` (id 255); `1.005` → Python `1`, JS `1.005`; `2.675` → Python `2.68` (id 261); `1e-7` → Python `0`, JS `1e-7` (id 257); `1e21` → Python **`99999999999999986892`** (dígitos errados), JS `1e+21` (id 256).
- Limpeza de espaços: `U+0085` é espaço para o Python e não para o JS (id 219); `U+FEFF` é o contrário (id 220).
- Truncamento a 20/120 caracteres: Python conta pontos de código, JS conta unidades UTF-16 (emoji conta 2) (ids 224, 358, 359).
- Rótulos de eixo para valores ≥ 1e21: Python escreve dígitos, JS escreve notação científica (ids 313, 314).

## F-03 — MÉDIA — `parse_duration`: Unicode
Python aceita dígitos Unicode (`"١٢"` → 12, `"１２"` → 12, `"١٢m"` → 720; ids 22–24) e apara `U+001F` (id 26); JS recusa os três. JS apara `U+FEFF` e aceita `"\ufeff5"` (id 27); Python recusa. **Recomendação:** usar `[0-9]` e uma lista explícita de espaços permitidos.

## F-08 — MÉDIA — `svg_chart`: `width`/`height` inteiros em formato decimal
`640.0`, `1e3`, `200.0`, `2000.0` (ids 324, 325, 342, 343, 352–355): JS aceita (`Number.isInteger`), Python recusa (`INVALID_SIZE`), porque o `json` do Python lê `640.0` como `float`. O mesmo JSON dá resultados diferentes.

## F-11 — MÉDIA — Limites e tipos
- **Sem limites** (aceitos nos dois lados, verificado): receita com 5.000 ingredientes (id 143), quiz com 5.000 perguntas (175) ou 5.000 opções (176), título de quiz de 200 KB (177), texto de duração sem teto de tamanho (F-02). Só `svg_chart` (50 rótulos, 6 séries, 200–2000 px) e `link_card` (2048 caracteres, título 120, descrição 300) têm limites. Não há teto de payload nem de chamadas por período.
- **Tipos errados em campos opcionais são descartados em silêncio** em vez de rejeitados: `title: 5` e `name: 5` no gráfico, `title`/`description` não texto no link, `title` da receita, `explanation` do quiz. Campos desconhecidos são ignorados (não alteram a saída; verificado). A missão pede rejeição previsível.
- **O que está correto:** valores `null`, texto, listas, objetos, booleanos, negativos, zero e NaN/Infinity nos campos obrigatórios são recusados com códigos estáveis nos dois lados (centenas de casos MATCH).

## F-07 — BAIXA — SVG pode não ser XML bem formado
`U+FFFE`/`U+FFFF` (id 221) passam para a saída nos dois lados e tornam o SVG inválido para um parser XML. Substituto solitário (`\ud800`, id 222) passa nos dois lados e não é codificável em UTF-8. No JS, o `slice` pode cortar um emoji ao meio e gerar substituto solitário (ids 358, 359). Não permite injeção; pode quebrar quem consome o SVG como XML.

## F-04, F-05, F-10, F-12, F-13, F-17 — resumo
- **F-04:** `format_duration(3600, null)` → Python `INVALID_FORMAT`, JS `01:00:00` (id 61); segundos `1e300` → Python escreve centenas de dígitos, JS notação científica (ids 65, 66); sem teto (o limite de 7 dias só vale em `parse`).
- **F-05:** `format_amount(1e21)` → Python `1000000000000000000000`, JS `1e+21` (id 147).
- **F-10:** chamada com argumentos faltando/sobrando: Python `TypeError`, JS usa `undefined` (ids 70, 71, 100, 101). Um adapter precisaria padronizar.
- **F-12:** `quiz.explanation`, nomes e títulos de receita voltam como texto bruto (ex.: `<img src=x onerror=…>` volta intacto; id 197, MATCH) — quem exibe deve usar `textContent`. A demo usa `innerHTML` em **um** ponto (`app.js:134`, saída do gráfico). A CSP da demo tem só `connect-src 'none'; form-action 'none'; base-uri 'none'`: sem `script-src`/`default-src`, o que não bloqueia scripts nem imagens como o `PERMISSOES.md` sugere ("Rede: nenhuma… bloqueia requisições de rede").
- **F-13:** `API.md` diz que o comportamento é o mesmo nas duas linguagens; `LIMITACOES.md` §5 admite diferenças e o corpus mostra 90 divergências em 516 casos.
- **F-17:** `localhost`, `127.0.0.1`, `192.168.0.1`, `169.254.169.254` são aceitos nos dois lados (MATCH). Tudo bem enquanto a ferramenta não acessa a rede; se alguém acrescentar busca de título, será preciso uma política de hosts.

---

## O que passou (evidência executada agora)

- **svg_chart — injeção:** 28 textos hostis (`<script>`, `"/><script>`, `]]>`, `<!ENTITY …>`, `<foreignObject>`, `onload=`, `javascript:`, `xlink:href`, `<style>`, `\x00`, RTL, 10.000 caracteres etc.) em título, rótulos e nome de série, em barras e linhas, mais campos extras (`href`, `style`, `onload`, `__proto__`, `color` com `</style><script>`). **Todas as saídas ok** (77 Python + 88 JS) foram analisadas com parser XML e lista branca: só `svg, title, rect, text, line, polyline, circle`; só atributos geométricos/de estilo esperados; nenhum `href`, `on*`, `script`, URL em atributo. As únicas falhas da checagem são as de boa formação XML (F-07), não de injeção. As cores vêm de uma paleta fixa; nenhum texto do usuário entra em atributo.
- **link_card — HTML:** 100 saídas Python + 96 JS analisadas: sempre um `<a>` com exatamente `class, href, rel, target`; `href` só `http(s)`; `rel="noopener noreferrer nofollow"`; filhos só `strong/span/p` sem atributos. `javascript:`, `data:`, `file:`, `ftp:`, `blob:`, `vbscript:`, `mailto:`, `//host`, sem esquema, com espaços/controles, 2049 caracteres, credenciais embutidas: recusados nos dois lados com o mesmo código.
- **quiz_engine:** 44/44 casos MATCH, incluindo ids `__proto__`, `constructor`, `toString`, respostas com `__proto__`, tipos errados e arredondamento da pontuação.
- **recipe_scaler:** chaves de protótipo (`__proto__`, `constructor`, `toString`, `hasOwnProperty`) como unidade: recusadas nos dois lados (`UNKNOWN_UNIT`).
