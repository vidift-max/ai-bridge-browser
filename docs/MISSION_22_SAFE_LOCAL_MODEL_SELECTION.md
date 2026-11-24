# Missão 22 — Seleção Segura de Modelos Locais

## Objetivo
Criar um catálogo local de perfis de referência e uma avaliação conservadora que cruza seus metadados com o relatório da Missão 21. Não fornece nem instala modelos executáveis.

## Registro das 10 rodadas
1. Definido escopo exclusivamente metadata-only, sem endpoints de download, URLs externas ou execução.
2. Definido esquema de perfil: escala de parâmetros, quantização, faixa mínima heurística e APIs requeridas.
3. Criado catálogo estático com três perfis de referência (0,5B, 1,5B e 3B), não artefatos reais.
4. Implementada consulta por ID com cópias imutáveis e retorno nulo para IDs desconhecidos.
5. Implementada avaliação de schema, escopo browser, contexto seguro, Wi-Fi, WebGPU, Workers e faixa de memória.
6. Implementado bloqueio conservador para hints ausentes, capacidades não prontas e estado de execução não inerte.
7. Implementada ordenação de perfis elegíveis para revisão, sem seleção ou ativação automática.
8. Criados testes Node.js para catálogo, imutabilidade, compatibilidade heurística e cenários fail-closed.
9. Documentados limites de privacidade, custo, licenciamento e impossibilidade de inferir memória realmente disponível.
10. Integrada a missão ao CI e aberta PR draft para revisão; sem merge ou deploy.

## Contrato dos perfis
Os itens são REFERENCE_PROFILE, não nomes de modelos públicos, pesos ou arquivos. artifactAvailable=false, downloadUrl=null, approximateArtifactSize=PROFILE_ONLY, licenseStatus=NOT_ASSESSED e compatibility=UNVERIFIED são invariantes. As escalas e quantizações são referências ilustrativas, não garantia de tamanho ou formato de artefato.

## Avaliação
A função evaluate aceita apenas relatório schemaVersion=1 e runtimeScope=user_device_browser. Exige LOCAL_AI_CANDIDATE_READY, contexto seguro, política Wi-Fi confirmada, adapter WebGPU, Workers e hints de memória suficientes para o limiar heurístico. Também exige que o relatório continue declarando ausência de modelo carregado, download e inferência.

POTENTIAL_CANDIDATE_REQUIRES_BENCHMARK significa somente que os sinais grosseiros não bloquearam uma futura revisão. Não significa que o modelo cabe na memória, que existe compatibilidade de driver, que o navegador oferece backend de inferência, nem que o desempenho será aceitável. Memória total do dispositivo não equivale à memória livre para pesos e KV cache.

## Privacidade e segurança
- Execução local no código do catálogo; nenhum fetch, XHR, WebSocket, URL remota, armazenamento ou telemetria.
- Nenhuma coleta adicional de dados do dispositivo.
- Nenhum download, instalação, descoberta de executáveis, carregamento ou inferência.
- Nenhuma API paga, chave ou infraestrutura criada.
- Nenhuma seleção automática: a saída é uma lista de avaliações explicáveis.

## Licenciamento e disponibilidade
Os perfis não representam modelos específicos. Nenhuma licença foi aprovada; NOT_ASSESSED impede presumir permissão de uso. Uma missão futura que integre modelos reais deverá avaliar licença, proveniência, formato, checksum, origem, compatibilidade e consentimento antes de qualquer aquisição ou execução.

## Limitações e aceite
Testes usam Node.js e dados simulados. Não houve benchmark, teste físico, medição de memória disponível, verificação de drivers, instalação de runtime/modelo ou inferência. O contrato server_host da Missão 20 permanece separado do navegador do usuário.

- [x] Catálogo metadata-only com perfis de referência não baixáveis.
- [x] Avaliação estrita do relatório da Missão 21.
- [x] Bloqueio quando Wi-Fi, WebGPU, Workers ou hints necessários não são confirmados.
- [x] Sem execução, rede, persistência ou telemetria.
- [x] Testes automatizados e workflow de CI adicionados.
- [ ] CI completo aprovado no SHA final.
- [ ] Validação física/benchmark — fora do escopo e não executados.

**Estado:** implementação em revisão; aguardar CI final para PASS técnico. PR draft; não mesclar sem autorização explícita.
