# Mission Loop — AI Bridge Browser

## Objetivo
Manter um ciclo contínuo de missão → execução → relatório → revisão → próxima missão, usando o GitHub como fonte de estado.

## Regra
O navegador não interpreta o conteúdo técnico da missão. Ele acompanha estados e locais declarados pelo coordenador.

## Estados
- ASSIGNED — missão criada e aguardando entrega à aba.
- WAITING_PAGE — aba ainda carregando.
- READY — página carregada e sessão alvo disponível.
- MESSAGE_QUEUED — mensagem aguardando entrega.
- WORKING — IA trabalhando; o conteúdo do trabalho permanece no chat/GitHub.
- REPORT_PENDING — relatório esperado ainda não apareceu.
- REPORT_RECEIVED — relatório esperado foi encontrado.
- WAITING_COORDINATOR — aguardando GPT-6 revisar.
- COMPLETED — ciclo encerrado ou substituído por nova missão.
- PAUSED — automação temporariamente suspensa pelo usuário.

## Regra de carregamento
Uma mensagem não deve ser perdida porque uma aba demora para abrir. A mensagem permanece em fila até a aba atingir READY.

## Regra de escala
Até 5 participantes contando GPT-6: áudio pode ser disponibilizado quando o protótipo técnico for comprovado.
Com mais de 5 participantes: operação padrão passa para mensagens; áudio global é desativado.

## Limite atual
A fila e o estado de carregamento foram preparados no código, mas a injeção/submissão automática no DOM do ChatGPT ainda NÃO está implementada. Não declarar envio automático como PASS antes de teste reproduzível.
