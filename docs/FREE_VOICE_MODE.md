# Modo gratuito de voz e colaboração

## O que esta etapa oferece

A página `/gpt6` pode usar recursos locais/nativos do navegador:
- Ditado em português do Brasil com `SpeechRecognition` ou `webkitSpeechRecognition`, quando suportado.
- Leitura de respostas com `speechSynthesis`, quando suportado.
- Entrada por texto continua disponível como alternativa.
- O microfone só é iniciado após clique explícito do usuário.
- O token de autenticação continua apenas na memória da página; não é salvo em `localStorage`.

## Limitações importantes

- O suporte a reconhecimento de fala varia por navegador e sistema. Alguns navegadores enviam o áudio a um serviço remoto do próprio fornecedor; portanto, não se deve prometer reconhecimento offline ou privacidade integral.
- Síntese de voz e reconhecimento de fala não são um modelo conversacional. Eles não geram respostas inteligentes por si mesmos.
- As respostas do endpoint `/v1/gpt6/respond` dependem de um provedor configurado no servidor. A assinatura ChatGPT não inclui créditos da API.
- Neste modo, não configurar `OPENAI_API_KEY`, não chamar a API da OpenAI, não criar segredo Realtime e não consumir créditos pagos.
- Se não houver provedor gratuito/autorizado conectado, o chat deve informar a indisponibilidade e nunca inventar respostas como se fossem do GPT-6.

## Regras de custo

1. Priorizar recursos nativos do navegador e ferramentas com plano gratuito real.
2. Não cadastrar cartão, ativar teste pago ou criar serviço pago sem autorização explícita.
3. Não considerar “gratuito” um serviço que exige cartão, limite temporário ou cobrança após franquia sem deixar isso claro.
4. Verificar limites e termos atuais antes de integrar qualquer provedor gratuito.
5. Não realizar publicação automática no Blogger.

## Blogger

Uma página pública do Blogger não deve conter token permanente do AI Messenger, chave de API, segredo de provedor ou credencial de serviço. A incorporação pública fica bloqueada até existir autenticação segura com sessão curta e escopo limitado. A interface de voz pode ser testada separadamente; isso não significa que o Blogger esteja conectado ao Messenger.

## Estado desta implementação

A interface web ganhou controles experimentais de ditado e leitura em voz alta. Isso é uma melhoria de frontend, não prova de reconhecimento funcional em todos os dispositivos, conexão com um provedor gratuito, comunicação multi-IA ou integração com Blogger. Esses pontos exigem testes e implementação separados.
