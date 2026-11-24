# Missão 20 — Contrato Seguro de Inferência Local

## Objetivo
Preparar a fronteira de integração para modelos locais sem instalar, baixar, iniciar ou conectar a qualquer runtime. O trabalho não presume que o tablet Android tenha memória, GPU ou espaço suficientes.

## 10 rodadas
1. Revalidar a distinção entre mensageiro autenticado, execução de modelo e sessão de conta externa.
2. Auditar o catálogo atual: WebGPU é apenas sondagem; Ollama e llama.cpp não estão implementados.
3. Definir contrato de adaptador estritamente local no host do servidor.
4. Criar controlador com política desativada por padrão.
5. Exigir opt-in explícito por execução e engine injetado por código confiável.
6. Bloquear engine que declare rede, downloads, escopo incorreto ou ausência de método de inferência.
7. Aplicar limites de tamanho de prompt, tokens e resposta, com erros sem detalhes sensíveis.
8. Expor apenas o estado do contrato no catálogo autenticado `GET /v1/local-ai`; nenhuma rota de execução remota foi criada.
9. Criar testes para política default-off, consentimento, isolamento local, limites e falhas.
10. Adicionar workflow same-HEAD para suíte backend e testes/compilação Android.

## Contrato implementado
- `LocalInferenceController` recebe um adaptador injetado; não descobre processos ou portas.
- `LocalInferencePolicy.enabled` é `false` por padrão.
- `allow_network` e `allow_model_downloads` precisam permanecer `false`.
- O adaptador deve declarar `runtime_scope=server_host`, `local_only=True`, `network_access=NONE`, `downloads_allowed=False` e implementar `generate`.
- Cada execução exige `user_opt_in=True`.
- Limites de prompt, saída e tokens são verificados.
- Exceções do engine são convertidas em códigos estáveis, sem vazar detalhes.

## Limitações explícitas
- Nenhum adaptador real foi instalado ou conectado; testes usam engine falso controlado.
- Nenhum modelo foi carregado e nenhuma inferência real foi executada.
- O contrato do servidor não executa no tablet; WebGPU continua apenas como sondagem no navegador.
- Não existe endpoint HTTP para executar prompts, nem comunicação automática de modelos entre identidades.
- Sem chamadas pagas, downloads, serviços externos, deploy ou ativação de runtime.

## Critério de validação
Backend tests e Android tests/build devem passar no mesmo SHA final. Isso valida o contrato e a compilação, não a execução em dispositivo físico.
