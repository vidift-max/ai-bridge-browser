# Privacidade e segurança do AI Bridge Browser

## Dados tratados

O protótipo carrega páginas web inseridas pelo usuário. Credenciais e conteúdo das conversas permanecem sob controle dos sites carregados e do armazenamento WebView do Android. O aplicativo não possui servidor próprio nem coleta remota configurada.

## Proteções atuais

- Permissão INTERNET apenas.
- Nenhuma permissão RECORD_AUDIO ou CAMERA declarada.
- Pedidos de microfone/câmera das páginas são negados.
- Acesso a arquivos locais e conteúdo local desativado.
- Conteúdo misto bloqueado.
- Abertura de múltiplas janelas desativada.
- Esquemas não HTTP/HTTPS rejeitados.
- Certificados TLS inválidos cancelam o carregamento.
- Safe Browsing habilitado.

## Limites

- As abas compartilham o perfil padrão WebView.
- A política de navegação não substitui uma lista completa de domínios permitidos.
- O usuário ainda precisa avaliar a confiabilidade dos sites que abre.
- Nenhuma captura de áudio está ativa.

## Princípios para futuras versões

- Pedir consentimento contextual antes de microfone, projeção ou captura.
- Exibir claramente quais fontes de áudio estão ativas.
- Fornecer botão global de parar.
- Não enviar áudio a servidor remoto sem consentimento informado.
- Não persistir gravações por padrão.
