# M218 — Revalidação do tamanho do APK antes da instalação

## Objetivo
Manter o vínculo entre o tamanho anunciado pelo asset da Release oficial e o arquivo efetivamente entregue ao instalador Android.

## Implementação
- A política de instalação agora exige tamanho esperado positivo e dentro do limite máximo de 250 MiB.
- O arquivo precisa continuar sendo o mesmo candidato verificado, com nome exato e dentro da pasta privada do atualizador.
- O tamanho físico em disco deve ser exatamente igual ao tamanho do asset da Release.
- A regra é aplicada no primeiro aceite do botão de instalação e novamente no worker imediatamente antes da verificação SHA-256, pacote/certificado e abertura do instalador Android.
- O hash SHA-256 e a verificação de identidade/assinatura continuam obrigatórios; a nova checagem não os substitui.

## Testes
- Aceita somente o tamanho exato.
- Rejeita arquivo truncado ou maior que o tamanho anunciado.
- Rejeita tamanho esperado zero, limite zero ou asset acima do limite.
- Rejeita arquivo diferente do candidato verificado, nome incorreto e caminho fora da pasta privada.

## Limites de segurança
Sem merge, publicação de Release, assinatura, acesso/alteração de Secrets, instalação física, ativação de AI-03 ou alegação de comunicação real entre AI-01 e AI-02.
