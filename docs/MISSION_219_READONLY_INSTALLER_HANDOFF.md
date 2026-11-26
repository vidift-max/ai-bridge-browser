# M219 — Bloqueio de gravação no handoff do instalador

## Objetivo
Reduzir a janela entre a última verificação do APK e a entrega do URI ao instalador Android, impedindo gravações acidentais no arquivo já validado.

## Implementação
- Depois de validar tamanho oficial, SHA-256, versão interna, pacote e certificado, o atualizador marca o APK verificado como somente leitura.
- A política confirma novamente identidade do arquivo, diretório privado, nome, tamanho esperado e limite máximo após aplicar o bloqueio.
- O SHA-256 é recalculado depois do bloqueio de escrita.
- Na fronteira final de abertura do instalador, o atualizador exige que o mesmo arquivo permaneça somente leitura e dentro do tamanho esperado.
- Ao descartar um candidato, o atualizador tenta restaurar permissão de escrita antes de removê-lo.

## Testes
- Bloqueio de escrita aplicado somente ao APK elegível.
- Confirmação de arquivo somente leitura no handoff final.
- Rejeição de arquivo com tamanho divergente antes de aplicar o bloqueio.

## Limites
A proteção reduz alterações acidentais pelo próprio aplicativo; não é uma garantia criptográfica contra processos privilegiados/root nem substitui SHA-256, validação de pacote e certificado. Sem merge, Release, assinatura, acesso/alteração de Secrets, instalação física ou ativação de AI-03.
