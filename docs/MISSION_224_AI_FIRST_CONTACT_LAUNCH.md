# M224 — AI-01 ↔ AI-02: botão de primeiro contato pronto para uso

## Objetivo

Deixar o acesso ao primeiro contato sempre visível e acionável no AI Bridge Browser, com pré-verificação fail-closed e confirmação explícita do usuário antes de enviar qualquer mensagem.

## Dez rodadas de engenharia

1. Auditar o botão AI ↔ AI existente e o fluxo de inicialização do orquestrador.
2. Confirmar o limite operacional de duas identidades: AI-01 e AI-02.
3. Identificar que o botão abria apenas uma sequência de verificações e não explicava como resolver os bloqueios.
4. Manter o botão permanentemente visível e habilitado para abrir a preparação/início do primeiro contato.
5. Criar política determinística que exige duas identidades, abas distintas, perfis distintos, isolamento verificado, páginas carregadas e ChatGPT aberto nas duas abas.
6. Acrescentar pré-verificação DOM independente em cada WebView, exigindo composer e botão Enviar disponíveis e ausência de geração em andamento.
7. Exigir confirmação manual separada de que AI-01 e AI-02 estão nas contas ChatGPT corretas; não ler nem armazenar e-mail, senha ou credenciais.
8. Iniciar apenas após mensagem inicial preenchida e confirmação dos dois perfis; limitar o ciclo a 10 turnos alternados.
9. Adicionar testes JVM para a política, testes estáticos Python para o contrato da interface e documentação operacional.
10. Executar CI no SHA final; manter PR Draft, sem merge, publicação, instalação ou ativação física.

## Comportamento no aplicativo

- O botão **AI ↔ AI · Começar** permanece sempre visível e habilitado quando não há conversa em execução; durante os 10 turnos, fica temporariamente desabilitado para impedir duplicidade.
- Ao tocar, o app verifica AI-01 e AI-02, abas diferentes, perfis WebView diferentes, isolamento confirmado e páginas ChatGPT prontas.
- O DOM de cada aba precisa apresentar campo de mensagem e botão Enviar habilitado, sem geração em andamento.
- Se alguma condição falhar, o app mostra o motivo e orienta a preparação; nenhum envio é feito.
- Se as verificações passarem, o app pede a mensagem inicial e duas confirmações explícitas, uma por conta.
- Só então o usuário autoriza o início dos 10 turnos alternados.
- Durante a execução, o botão fica temporariamente desabilitado para evitar iniciar duas conversas simultâneas; volta a ficar habilitado ao terminar ou falhar.

## Privacidade e segurança

- Nenhum campo de e-mail ou senha é criado.
- O aplicativo não automatiza login, não contorna MFA e não tenta selecionar contas por meio de credenciais.
- A seleção/login de cada conta continua manual dentro da aba correspondente.
- O escopo atual permanece em AI-01 e AI-02; AI-03 não é ativada.
- A confirmação do usuário identifica a conta escolhida, mas não prova identidade de conta por evidência independente.

## Limites da prova

Testes JVM e estáticos não comprovam que o WebView instalado no dispositivo suporta Multi-Profile, que duas contas reais estão autenticadas ou que o ChatGPT permitirá o envio/retorno. A primeira conversa real só será comprovada quando o APK adequado for instalado e o teste for executado no dispositivo, com evidência dos 10 turnos. Nenhum contato real foi iniciado por esta missão.

## Critérios de aceitação

- [ ] CI push e PR verdes no mesmo SHA final.
- [ ] Botão visível e habilitado no APK gerado.
- [ ] Duas contas reais autenticadas em perfis independentes.
- [ ] Usuário confirma ambas as contas.
- [ ] 10 turnos alternados executados e auditados no dispositivo.
