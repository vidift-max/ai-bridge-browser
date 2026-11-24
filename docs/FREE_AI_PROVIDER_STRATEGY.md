# Estratégia de IA exclusivamente gratuita

## Objetivo

Permitir que o AI Messenger obtenha respostas de modelos de IA sem configurar a API paga da OpenAI, sem cartão cadastrado, sem teste pago e sem ultrapassar cotas gratuitas. O sistema deve funcionar de forma honesta quando nenhuma opção gratuita estiver disponível.

## Decisão de arquitetura

Adotar uma arquitetura com adaptadores substituíveis, nesta ordem:

1. **Inferência local no navegador (prioridade de longo prazo):** avaliar WebLLM/WebGPU e Transformers.js/ONNX. O processamento ocorre no dispositivo, sem cobrança por token e sem enviar o prompt a um provedor de inferência. A capacidade depende do navegador, GPU, RAM e tamanho do modelo. WebLLM exige WebGPU; Transformers.js pode executar em CPU/WASM, mas modelos generativos podem ser lentos e consumir memória. O navegador deve detectar capacidades antes de oferecer essa opção.
2. **Provedor remoto com plano gratuito (opção prática de teste):** GroqCloud Free é o primeiro candidato a avaliação. A API é compatível com o formato de chat OpenAI, e a documentação oficial descreve limites por modelo e informa que a atualização para o plano Developer exige método de pagamento. O sistema deve permanecer no plano Free, sem adicionar método de pagamento ou habilitar Developer.
3. **Alternativa secundária:** Google Gemini API Free. A página oficial confirma modelos/cotas gratuitas, mas informa que dados enviados no nível gratuito podem ser usados para melhorar produtos do Google. Por isso, não enviar conteúdo privado, credenciais, dados pessoais ou material não publicado sem decisão consciente do usuário.

## Regras que impedem custos

- Não usar OPENAI_API_KEY, OpenAI Responses API ou Realtime API neste modo.
- Não adicionar cartão, método de pagamento, créditos, assinatura ou plano Developer.
- Não implementar fallback automático para provedor pago.
- Não alternar para plano pago quando a cota gratuita acabar; retornar estado FREE_QUOTA_EXHAUSTED e aguardar a renovação da cota ou escolha explícita de outro modo gratuito.
- Não executar chamadas de inferência durante testes automatizados.
- Não afirmar que um provedor está em plano gratuito apenas porque uma chave existe. A situação da conta deve ser confirmada pelo titular no painel oficial.
- Limites e modelos devem ser configuráveis e revistos na documentação oficial antes de cada ativação; nunca codificar cotas de páginas de terceiros como garantias.
- Manter limites locais conservadores por agente, por dia e por tamanho de prompt; os limites locais complementam, mas não substituem, os limites do provedor.
- Chaves de provedores ficam somente no servidor, nunca no Blogger, HTML, JavaScript do navegador, logs ou Git.

## Política de dados

- **Inferência local:** preferida para conteúdo privado, se o dispositivo suportar o modelo.
- **Groq Free:** a documentação informa que entradas/saídas de inferência não são retidas por padrão, mas pode haver retenção temporária por até 30 dias para confiabilidade/abuso, salvo controles de retenção aplicáveis. Tratar qualquer prompt enviado como compartilhamento com terceiro.
- **Gemini Free:** a documentação oficial informa uso do conteúdo gratuito para melhorar produtos. Não usar para conteúdo confidencial ou rascunhos sensíveis sem consentimento informado.
- Não enviar tokens OAuth do Blogger, chaves, senhas, dados pessoais desnecessários ou arquivos completos do blog para modelos remotos.
- Enviar somente o trecho mínimo necessário para a tarefa editorial.

## Estados do adaptador

- LOCAL_READY: modelo local carregado e pronto.
- LOCAL_UNSUPPORTED: WebGPU/recursos insuficientes ou modelo indisponível.
- FREE_PROVIDER_READY: provedor gratuito configurado e verificado pelo administrador.
- FREE_QUOTA_EXHAUSTED: cota gratuita atingida; não tentar plano pago.
- PROVIDER_NOT_CONFIGURED: nenhum adaptador disponível.
- PROVIDER_ERROR: falha externa; não simular resposta.
- PAUSED_BY_USER: inferência suspensa pelo usuário.

## Próximos passos de implementação

1. Definir uma interface comum AIProvider com status() e respond().
2. Remover o acoplamento dos endpoints HTTP ao adaptador OpenAI único, sem apagar o adaptador existente até sua remoção ser aprovada.
3. Implementar detecção de capacidade local no frontend e um protótipo pequeno de inferência no navegador.
4. Medir download inicial, RAM, tempo de resposta e qualidade em português no navegador/dispositivo real antes de escolher modelo padrão.
5. Somente se necessário, adicionar adaptador Groq com chave exclusivamente server-side, limite de uso local, sem método de pagamento e sem fallback pago.
6. Criar testes com transporte HTTP mockado para provar que testes não fazem chamadas externas e que cota esgotada bloqueia novas requisições.
7. Conectar o AI Messenger ao Blogger SEO Intelligence apenas por API autenticada e escopada. Agentes podem produzir rascunhos/prévias; publicação continua exigindo aprovação humana.

## Fontes oficiais consultadas

- WebLLM local inference: https://webllm.io/docs/guides/local-inference/
- WebLLM browser support: https://webllm.io/docs/faq/
- Transformers.js: https://huggingface.co/docs/transformers.js/
- Transformers.js WebGPU: https://huggingface.co/docs/transformers.js/guides/webgpu
- Groq rate limits: https://console.groq.com/docs/rate-limits
- Groq data retention: https://console.groq.com/docs/your-data
- Groq billing FAQ: https://console.groq.com/docs/billing-faqs
- Gemini API pricing and free-tier data use: https://ai.google.dev/gemini-api/docs/pricing

## Estado atual

Este documento é uma decisão de arquitetura e pesquisa, não uma integração concluída. Nenhuma conta de provedor foi criada ou alterada, nenhuma chave foi solicitada ou configurada, nenhuma chamada de inferência foi feita e nenhum custo foi gerado. O adaptador OpenAI já existente permanece no código, mas não deve ser configurado ou utilizado sob a regra atual de modo gratuito.
