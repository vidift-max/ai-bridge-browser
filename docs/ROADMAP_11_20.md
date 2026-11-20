# Rodadas 11–20 — estabilização do navegador

Objetivo deste ciclo: transformar o scaffold compilável em um navegador de abas mais utilizável, sem fingir que a ponte de áudio já funciona.

| Rodada | Escopo | Critério de aceite |
|---|---|---|
| 11 | Fechar abas e selecionar a aba ativa | Fechar aba não deixa WebView órfã; última aba fechada abre uma nova |
| 12 | Títulos e identificação das abas | Cada aba mostra título/host e indica qual está ativa |
| 13 | Política de navegação | Apenas HTTP/HTTPS válidos; esquemas externos e URLs com userinfo bloqueados |
| 14 | Recuperação após rotação/recriação | URLs das abas e aba ativa são restauradas; histórico completo ainda não garantido |
| 15 | Segurança WebView | Arquivos locais, conteúdo misto, janelas múltiplas e permissões web ficam bloqueados |
| 16 | Ciclo de vida | WebViews são destruídas ao fechar aba e ao encerrar Activity |
| 17 | CI Android | Build debug do commit atual precisa terminar SUCCESS |
| 18 | Sessões independentes | Documentar e projetar perfis separados; não declarar isolamento até teste específico |
| 19 | Plano de protótipo de áudio | Definir teste MediaProjection e entrada de voz autorizada; sem captura silenciosa |
| 20 | Auditoria e relatório | Revalidar arquivos, build e limites; registrar PASS/PARTIAL/BLOCKED |

## Regras de segurança

- Nenhuma instalação no tablet sem autorização do usuário.
- Nenhuma captura de áudio sem consentimento explícito.
- Nenhuma permissão de microfone concedida automaticamente a páginas.
- Nenhum isolamento de contas presumido: WebViews padrão compartilham cookies.
- Nenhum deploy/servidor externo necessário para o navegador básico.
