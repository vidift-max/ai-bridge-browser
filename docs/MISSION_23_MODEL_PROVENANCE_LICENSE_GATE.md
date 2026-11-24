# Missão 23 — Proveniência, Licenças e Aprovação de Modelos

## Objetivo
Definir uma barreira offline para avaliar metadados de candidatos a modelos locais antes de qualquer proposta futura de aquisição. Não integra modelos reais nem autoriza efeitos externos.

## Registro das 10 rodadas
1. Definido escopo offline, separado de aquisição, instalação e execução.
2. Definido schema versionado para identidade, publisher, versão, domínio de origem e checksum.
3. Implementada validação estrita de identificador e domínio textual sem consultar o domínio.
4. Exigido SHA-256 hexadecimal de 64 caracteres.
5. Exigidos identificador de licença e confirmação de leitura do texto exato.
6. Definido estado fechado: somente APPROVED_FOR_REVIEW passa pela revisão de metadados.
7. Exigidas referências de evidência e revisões independentes de proveniência, licença e segurança.
8. Exigida aprovação explícita booleana do usuário; strings e valores truthy não passam.
9. Criado checklist imutável e testes automatizados adversariais.
10. Integrada a suíte ao CI e aberta PR draft; nenhum modelo foi obtido, instalado ou executado.

## Contrato
A função validate aceita somente schemaVersion 1, identificador restrito, publisher, versão, domínio DNS textual, checksum SHA-256, licença identificada e revisada, referência de proveniência, três revisões independentes e userApproval === true.

A saída positiva é METADATA_REVIEW_COMPLETE_PENDING_SEPARATE_ACTION. Mesmo nesse estado, eligibleForAcquisition=false e eligibleForExecution=false.

O gate verifica sintaxe e presença de atestações. Não autentica publisher, não comprova origem, não compara checksum com arquivo real, não interpreta juridicamente licença e não comprova segurança do modelo. Evidências exigem revisão humana independente.

## Segurança e privacidade
- Nenhuma consulta de rede, DNS, fetch, XHR ou WebSocket.
- Nenhuma persistência, telemetria ou coleta de dados do dispositivo.
- Nenhum arquivo de modelo, download, instalação, carregamento, benchmark ou inferência.
- Nenhuma chave, API paga ou infraestrutura adicional.
- Nenhuma ação externa é autorizada pelo módulo.

## Checklist futuro
1. Confirmar publisher e proveniência por fonte independente.
2. Ler versão exata da licença e avaliar uso pretendido.
3. Revisar model card, divulgações de treinamento e restrições.
4. Revisar formato, checksum e riscos de cadeia de suprimentos.
5. Concluir revisão de segurança antes de propor aquisição.
6. Obter aprovação explícita do usuário para ação separada e delimitada.

## Limitações e aceite
Testes simulados em Node.js. Nenhum modelo concreto foi avaliado, licença específica aprovada, arquivo verificado criptograficamente ou modelo executado.

- [x] Gate offline e fail-closed.
- [x] Identidade, origem textual, versão, checksum e licença requeridos.
- [x] Revisões independentes e aprovação explícita exigidas.
- [x] Saída positiva não autoriza aquisição nem execução.
- [x] Testes e workflow integrados.
- [ ] CI completo aprovado no SHA final.
- [ ] Revisão humana de modelo real — não realizada.

**Estado:** implementação em revisão; aguardar CI final para PASS técnico. PR draft; sem merge/deploy.
