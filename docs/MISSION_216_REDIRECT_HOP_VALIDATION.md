# Missão 216 — validação de cada salto de redirecionamento do atualizador

## Objetivo
Impedir que o atualizador siga automaticamente uma cadeia de redirecionamentos sem validar cada destino intermediário.

## Dez rodadas
1. Confirmar os workflows push e pull_request da M215 no SHA final.
2. Confirmar os jobs Android unit tests, Python manifest tests, Debug build e Release Preparation.
3. Auditar o uso de follow redirects automático no manifesto e no download do APK.
4. Identificar que validar somente a URL final não prova que os saltos intermediários foram confiáveis.
5. Criar política pura para reconhecer somente códigos HTTP de redirecionamento suportados.
6. Resolver destinos relativos e absolutos usando URI, rejeitando destinos fora dos hosts HTTPS permitidos.
7. Impor limite máximo de cinco redirecionamentos e rejeitar Location ausente/malformado.
8. Integrar o seguimento manual de redirecionamentos tanto na leitura da API/manifesto quanto no download do APK.
9. Adicionar testes para destinos confiáveis, host externo, HTTP, userinfo, porta não padrão, Location inválido e limite excedido.
10. Habilitar CI da branch/PR e manter o PR Draft sem merge, assinatura, Release ou instalação.

## Controles
- URL inicial deve ser a API fixa releases/latest ou um asset de Release oficial exato.
- Cada salto deve usar HTTPS e host permitido pela política existente.
- O cliente não segue redirecionamentos automaticamente.
- Limite de cinco saltos; códigos 300, 304 e outros não aceitos como redirect.
- Resposta final continua sujeita à validação de status HTTP e tamanho/hash/certificado existentes.

## Limites
Nenhum Secret foi lido ou alterado. Nenhuma assinatura ou Release foi produzida/publicada. Nenhum APK foi instalado. AI-03 continua desativada. Nenhuma comunicação real AI-01 ↔ AI-02 é alegada.

## Critério de aprovação
PASS técnico somente após testes Android, testes Python, build Debug e Release Preparation passarem nos workflows do SHA final, tanto no push quanto no pull_request. O resultado não comprova instalação física ou atualização publicada.
