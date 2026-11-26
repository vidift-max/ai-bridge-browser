# M219 — Armazenamento interno privado do APK

## Objetivo
Reduzir a exposição do APK verificado antes da instalação, mantendo o arquivo no armazenamento interno privado do aplicativo.

## Implementação
- O atualizador grava o download temporário e o APK final em `getFilesDir()/updates`, em vez de `getExternalFilesDir()`.
- A política confirma que o diretório de staging é exatamente o filho `updates/` do diretório interno do aplicativo.
- A validação do diretório ocorre após a criação da pasta, no pedido de instalação e novamente no worker imediatamente antes do handoff.
- O FileProvider expõe somente `updates/` via `<files-path>`; o mapeamento externo anterior foi removido.
- O provider permanece não exportado e o Intent do instalador concede somente leitura.
- O limite de tamanho, SHA-256, versão, pacote e certificado continuam obrigatórios.

## Testes
- Aceita o diretório interno dedicado `updates/`.
- Rejeita diretórios irmãos, nulos ou inexistentes.
- Mantém testes de identidade do arquivo, caminho permitido e tamanho exato do APK.

## Limites
CI valida o código e os recursos; não prova comportamento em dispositivo físico. Sem merge, Release, assinatura, acesso/alteração de Secrets, instalação física, ativação de AI-03 ou alegação de comunicação real AI-01↔AI-02.
