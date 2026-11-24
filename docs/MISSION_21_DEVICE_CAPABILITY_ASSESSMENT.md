# Missão 21 — Avaliação de Capacidade do Dispositivo e Viabilidade de Inferência no Navegador

## Objetivo
Criar uma avaliação local e conservadora dos recursos que o navegador oferece, sem presumir o hardware do usuário e sem confundir suporte de API com capacidade real de executar um modelo.

## Relatório
O botão **Verificar capacidade local** executa uma sondagem sob ação explícita do usuário. O relatório inclui:
- contexto seguro (HTTPS/localhost) e estado da política Wi-Fi;
- disponibilidade da API WebGPU e resposta de requestAdapter();
- presença da API WebNN, sem criar contexto;
- disponibilidade de Workers, IndexedDB e estimativa de armazenamento;
- faixas aproximadas de memória e concorrência de CPU, quando o navegador fornece esses hints.

Os hints de hardware são agrupados em faixas. User-Agent, plataforma, identificadores do dispositivo, detalhes do adaptador gráfico e outros dados brutos não são coletados.

## Privacidade e custo
- A sondagem é executada no navegador e não envia o relatório ao servidor.
- Não grava o relatório em localStorage, sessionStorage, IndexedDB ou outro armazenamento.
- Não usa fetch, XHR, WebSocket nem serviços externos.
- Não baixa ou instala modelos, runtimes ou pacotes de idioma.
- Não inicia inferência, não reserva memória para modelo e não executa benchmark.
- Não habilita APIs pagas nem cria recursos de nuvem.

## Interpretação
LOCAL_AI_CANDIDATE_READY significa apenas que os pré-requisitos observáveis desta sondagem não apresentaram bloqueios. Não significa que o dispositivo suporta determinado modelo, que há memória suficiente para pesos/KV cache, que o navegador sustenta uma sessão longa, ou que a inferência funcionará.

LOCAL_AI_NOT_READY lista motivos conhecidos. Um hint ausente é tratado como desconhecido, não como prova de incapacidade; os requisitos essenciais ausentes ou não confirmados mantêm o resultado conservador.

## Limites de validação
Os testes usam APIs simuladas em Node.js e testes de contrato Python. Não substituem teste físico no tablet/telefone, perfil de memória real, compatibilidade de driver, estabilidade térmica, teste de desempenho nem execução de modelo. Não foi instalado modelo ou runtime. A avaliação não autoriza execução futura automaticamente.

## Separação de ambientes
Este relatório descreve user_device_browser. O contrato da Missão 20 descreve um adaptador no server_host. Um não comprova nem habilita o outro.