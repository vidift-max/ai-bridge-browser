# Missão 17 — Modo Gratuito e Bloqueio de APIs Pagas

## Dez rodadas
1. Rechecamos a PR #14 e investigamos a CI: o teste falhou por uma chave `}` extra em `server/openai_text_adapter.py`.
2. Confirmamos que a falha impedia a importação de seis módulos de teste; os demais testes continuaram executando.
3. Criamos a branch isolada `feat/mission-17-free-mode-paid-api-guard`, baseada no head da Missão 16.
4. Corrigimos o erro de sintaxe herdado da Missão 16.
5. Criamos a configuração `OPENAI_API_CALLS_ENABLED`, com padrão `false` e validação estrita.
6. Bloqueamos chamadas pagas na própria camada do adaptador, tanto Responses quanto Realtime.
7. Bloqueamos as rotas HTTP de resposta e geração de client secret antes de qualquer acesso à rede.
8. Atualizamos o catálogo: com a política fechada, capacidades pagas ficam vazias e o estado é `DISABLED_BY_POLICY`.
9. Adicionamos testes de bloqueio sem rede, validação de configuração e visibilidade das capacidades.
10. Atualizamos a documentação e abrimos PR draft para CI e revisão; nenhum merge ou deploy.

## Política de custo
- `OPENAI_API_CALLS_ENABLED=false` por padrão.
- Chave API configurada não habilita chamadas.
- Responses API e Realtime API falham antes de abrir conexão de rede quando o gate está fechado.
- Nenhuma chave foi criada, armazenada ou exibida.
- Nenhuma chamada real, simulada como faturamento, ou cobrança foi feita nesta missão.
- A chave `OPENAI_API_CALLS_ENABLED=true` é apenas um interruptor técnico de configuração; não equivale à autorização do usuário. A política atual do projeto continua sendo não habilitar nem usar serviços pagos sem autorização explícita.

## Limitações
Este trabalho não torna a OpenAI API gratuita. Ele evita que o AI Bridge faça chamadas a ela por acidente. O modo gratuito continua dependendo dos recursos locais, Wi-Fi e serviços cujos planos gratuitos sejam suficientes. Limites e termos de terceiros podem mudar.

## Validação
`python -m unittest discover -s server -p 'test_*.py' -v`


# Missão 17 — Modo gratuito e bloqueio de APIs pagas

O AI Bridge adota modo gratuito por padrão. A variável `OPENAI_API_CALLS_ENABLED` assume `false` quando ausente. Mesmo que exista `OPENAI_API_KEY`, as chamadas Responses e Realtime são recusadas pelo adaptador antes de qualquer conexão de rede. As rotas HTTP também recusam a operação com `503 openai_api_calls_disabled`.

O catálogo informa `DISABLED_BY_POLICY`, `apiCallsEnabled=false` e lista capacidades pagas vazias. Claude e Gemini continuam não implementados. Nenhuma chave ou chamada paga é necessária para desenvolvimento local, mensagens internas e testes automatizados.

O interruptor técnico `OPENAI_API_CALLS_ENABLED=true` não constitui autorização do usuário nem deve ser habilitado sob a regra atual de custo zero. Esta missão não habilitou o interruptor, não configurou credenciais e não fez chamadas reais.
