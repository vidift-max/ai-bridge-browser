# GPT-6 Messenger no Blogger

O AI Messenger pode ser apresentado dentro de uma página do Blogger por meio de um iframe apontando para o endpoint web `/gpt6` do servidor do AI Bridge.

## Arquitetura

```
Blogger
  |
  +-- iframe -> AI Messenger Web (/gpt6)
                    |
                    +-- bearer token da sessão
                    |
                    +-- AI Bridge Server
                              |
                              +-- OpenAI Responses API
```

A chave da OpenAI nunca deve ser colocada no HTML do Blogger. Ela permanece somente no servidor.

## Snippet do Blogger

Depois que o servidor estiver publicado, substituir `https://SEU-SERVIDOR` pelo endereço HTTPS real:

```html
<div style="max-width:900px;margin:20px auto;">
  <iframe
    src="https://SEU-SERVIDOR/gpt6"
    title="AI Messenger — GPT-6"
    style="width:100%;height:720px;border:0;border-radius:16px;"
    loading="lazy"
    referrerpolicy="no-referrer">
  </iframe>
</div>
```

No Blogger, o código pode ser colocado em uma página em modo HTML ou em um gadget HTML/JavaScript. O Blogger documenta ambos os mecanismos de personalização de HTML.

## Segurança

- O token é digitado pelo usuário na interface e mantido somente em memória da página.
- A página não recebe a chave da OpenAI.
- O endpoint GPT-6 continua protegido pela autenticação existente do AI Messenger.
- O servidor deve usar HTTPS.
- Não publicar tokens no post, tema ou código-fonte do Blogger.
- Antes de usar publicamente, configurar uma política de acesso apropriada e limites de uso.

## Estado

Implementado no branch `feat/gpt6-messenger-direct-connection`:
- página web GPT-6;
- rota `/gpt6`;
- chamada autenticada aos endpoints GPT-6 existentes;
- teste de contrato da rota.

Ainda pendente:
- publicar o servidor em um endereço HTTPS;
- configurar autenticação/segredos no ambiente de produção;
- inserir o iframe no Blogger;
- teste real de mensagem ponta a ponta.
