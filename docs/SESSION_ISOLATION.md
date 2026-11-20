# Isolamento de sessões — decisão técnica pendente

## Estado atual

As abas atuais usam WebViews no mesmo processo e perfil padrão. Portanto, cookies, armazenamento e autenticação podem ser compartilhados. Não abrir duas contas distintas esperando isolamento.

## Caminhos a avaliar

1. **Perfis WebView suportados pela AndroidX WebKit**, se a versão disponível oferecer perfil separado com suporte estável no Android 12.
2. **Processos Android separados**, cada um inicializando WebView com um sufixo de diretório de dados distinto antes de criar qualquer WebView. Isso aumenta consumo de memória e exige arquitetura IPC.
3. Manter um único perfil e declarar explicitamente que as abas são apenas páginas diferentes da mesma sessão.

## Critérios antes de implementar

- Verificar API oficial disponível na versão mínima Android 12.
- Confirmar suporte a cookies/storage separados.
- Testar login simultâneo em duas contas de teste.
- Confirmar que logout/limpeza de dados de uma sessão não afeta a outra.
- Medir RAM e estabilidade com duas e cinco sessões.

## Decisão provisória

Não implementar uma falsa separação por aba. A independência de contas permanece BLOCKED até teste reproduzível.
