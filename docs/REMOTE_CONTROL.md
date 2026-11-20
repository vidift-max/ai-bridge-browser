# Remote AI Control

## Modelo
GPT-6 é o coordenador. O AI Bridge Browser executa apenas ações explicitamente autorizadas e registradas.

Fluxo:
1. GPT-6 cria a missão e o local esperado do relatório.
2. O registro da missão é publicado no GitHub.
3. O navegador identifica a aba participante.
4. A mensagem fica em fila enquanto a página carrega.
5. Quando a sessão estiver pronta, uma camada de automação validada poderá preencher e enviar a mensagem.
6. O navegador registra o estado.
7. O relatório é verificado no local declarado.
8. GPT-6 revisa e cria a próxima missão.

## Segurança
O navegador não deve inventar missões, conceder permissões novas ou assumir identidade do GPT-6. Ações de envio automático exigem autorização explícita e testes.

## Estado atual
A estrutura de controle e fila está preparada. A escrita/submissão automática dentro do DOM do ChatGPT permanece pendente de implementação e validação.
