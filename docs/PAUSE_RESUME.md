# Pause / Resume

## PAUSE
Ao pausar:
- não iniciar novas entregas automáticas;
- preservar o estado das abas;
- preservar a fila em memória durante a execução da Activity;
- interromper a progressão do supervisor;
- manter missões e relatórios no GitHub intactos.

## RESUME
Ao continuar:
1. verificar o estado das abas;
2. verificar mensagens pendentes;
3. verificar o estado registrado das missões;
4. retomar somente ações autorizadas.

## Importante
Persistência completa da fila entre encerramentos do processo ainda precisa ser implementada. O estado de missão no GitHub continua sendo a fonte durável.
