# Missão 217 — vinculação do tamanho do APK ao asset oficial

## Objetivo
Garantir que o tamanho efetivamente baixado corresponda ao tamanho informado pela API da Release oficial, além das verificações de hash, pacote e certificado já existentes.

## Dez rodadas
1. Confirmar M216 PASS nos workflows de push e pull_request no SHA final.
2. Auditar metadados do asset APK retornados pela API de Releases.
3. Identificar que o tamanho era validado como positivo, mas não persistia como expectativa do Candidate.
4. Expor metadados validados do asset (URL oficial e tamanho positivo em bytes).
5. Rejeitar asset maior que o limite máximo do APK antes do download.
6. Guardar o tamanho anunciado no Candidate selecionado.
7. Exigir que Content-Length, quando presente, seja igual ao tamanho da Release.
8. Exigir que o total real de bytes seja exatamente o tamanho anunciado, mesmo quando Content-Length estiver ausente.
9. Adicionar testes para tamanho exato, desconhecido no cabeçalho, truncamento, excesso, tamanho zero e limite máximo.
10. Habilitar CI da branch/PR e documentar os controles; manter PR Draft sem merge.

## Controles
- A URL deve continuar vinculada à tag e ao nome do asset oficiais.
- O tamanho deve ser inteiro positivo e não ultrapassar 250 MiB.
- O hash SHA-256 e a identidade/certificado do APK continuam obrigatórios.
- Um tamanho divergente bloqueia a instalação e remove o arquivo parcial.

## Limites
Nenhum Secret foi lido ou alterado. Nenhuma assinatura ou Release foi produzida/publicada. Nenhum APK foi instalado. AI-03 continua desativada. Nenhuma comunicação real AI-01 ↔ AI-02 é alegada.

## Critério de aprovação
PASS técnico somente após testes Android, testes Python, build Debug e Release Preparation passarem nos workflows do SHA final, tanto no push quanto no pull_request.
