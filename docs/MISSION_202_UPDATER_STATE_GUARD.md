# Missão 202 — proteção do estado da Central de Atualizações

## Objetivo
Evitar que uma verificação nova reutilize por engano um APK que foi baixado e validado para uma versão anterior. Escopo atual continua limitado a AI-01 e AI-02. Nenhuma publicação, assinatura, instalação ou merge foi autorizado/realizado.

## 10 rodadas

| Rodada | Trabalho | Resultado |
|---|---|---|
| 01/10 | Revalidar PR #204 e CI da M201. | PASS — PR #204 aberta, Draft, não mesclada; HEAD M201 `d125b1f5f410b7dc15e0de2c5e82add3e5b3ac9b`; workflow acionado, ainda em andamento no último snapshot. |
| 02/10 | Inspecionar máquina de estados do updater. | PASS — identificada troca dinâmica do click listener após download verificado. |
| 03/10 | Simular fluxo lógico: baixar versão A, iniciar nova verificação, encontrar versão B. | PASS — identificado risco de manter listener apontando para o APK A. |
| 04/10 | Implementar limpeza do APK previamente validado quando nova consulta começa. | PASS em código — referência antiga é limpa e arquivo anterior é removido do diretório privado do app. |
| 05/10 | Restaurar ação padrão do botão antes de avaliar novo candidato. | PASS em código — botão volta para “Baixar e instalar atualização” e listener chama o fluxo de download. |
| 06/10 | Aplicar a restauração também ao iniciar novo download e em falha. | PASS em código — não mantém botão de instalação apontando para arquivo de tentativa anterior. |
| 07/10 | Revalidar verificações de integridade já existentes. | PASS por inspeção — SHA-256, packageName, versionCode/versionName e certificado instalado continuam obrigatórios antes do instalador. |
| 08/10 | Atualizar filtros de CI para branch M202 e PR baseada em M201. | PASS — push M202 e pull_request base M201 adicionados ao workflow. |
| 09/10 | Verificar o estado de publicação e assinatura. | BLOCKED — sem release estável publicada e sem assinatura final disponibilizada; nenhum segredo acessado ou criado. |
| 10/10 | Registrar relatório e abrir PR Draft. | PASS — PR #205 aberta para revisão; CI do HEAD M202 precisa concluir. |

## Alterações
- `UpdateCenterActivity.java`: adiciona `clearDownloadedCandidate()` e `resetInstallAction()`; nova verificação remove o APK anterior validado e restaura o botão/ação de download.
- `.github/workflows/android-build.yml`: aciona CI na branch M202 e em PR com base M201.
- Este relatório registra limites e evidências.

## Evidências
- PR M201: https://github.com/vidift-max/ai-bridge-browser/pull/204
- Base do código: `d125b1f5f410b7dc15e0de2c5e82add3e5b3ac9b`
- Commits M202: `c572606844d4c48b064b2071313ce43e316bf229`, `8172a392f18353ab69b78eb83382a55b399a27dd`
- Nenhuma release estável existe no canal consultado no último levantamento M200.

## Limites
- A correção foi inspecionada no código, mas ainda depende do CI M202 e teste em dispositivo.
- Não há pausa/retomada de download.
- Não há histórico de versões implementado.
- Não há APK final assinado/publicado nem teste de atualização in-place.
- Seletor de conta Google no login ChatGPT ainda não foi implementado.
- Nenhuma instalação, publicação, merge ou ativação real foi realizada.
