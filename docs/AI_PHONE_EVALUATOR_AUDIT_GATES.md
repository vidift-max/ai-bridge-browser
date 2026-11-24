# AI-PHONE — Auditoria do avaliador externo e gates de evidência

Este documento registra como interpretar uma auditoria estática do APK sem transformar código encontrado em prova de funcionamento físico.

## Gates

1. **Instalação** — só PASSA com instalação real em Android.
2. **Abertura** — só PASSA com o aplicativo iniciado no dispositivo.
3. **Documentos** — PASSA quando os documentos oficiais estão presentes e legíveis.
4. **Wi‑Fi/Internet** — implementação pode ser inspecionada; funcionamento exige evidência do dispositivo.
5. **Identidade/AI_ID** — classes de registro não provam autorização central; é necessário retorno autenticado coerente com o AI_ID.
6. **Messenger remoto** — código de cliente não prova entrega entre aparelhos.
7. **ACK/leitura** — estado aceito pelo servidor não equivale a leitura pelo destinatário.
8. **Áudio** — gravação local não prova upload/download/reprodução remota.
9. **Voz aberta/chamada** — só PASSA após teste E2E entre dispositivos físicos.
10. **Segurança/distribuição** — Debug pode ser analisado estaticamente; a distribuição participante deve usar Release assinado quando as credenciais de assinatura estiverem configuradas.

## Decisões desta rodada

- WifiDeviceDiagnostics usa ConnectivityManager/NetworkCapabilities e não lê senhas nem faz varredura de redes; portanto não foi adicionada uma permissão Wi‑Fi apenas para satisfazer uma inferência estática.
- Endereços de exemplo (example.com, .example, .test, .invalid e localhost) agora são rejeitados pelo validador de configuração remota, reduzindo o risco de um placeholder ser tratado como servidor real.
- Os campos visuais de servidor usam texto explicitamente não operacional; o endereço real só deve ser informado por configuração autorizada.
- O cofre de credencial usa Android Keystore + AES-GCM; isso é evidência de implementação, não substitui um teste dinâmico em aparelho.
- O build Debug continua sendo tratado como build de teste. O Release assinado permanece bloqueado até que as quatro credenciais de assinatura sejam configuradas com segurança.

## Regra principal

**Implementado ≠ testado ≠ instalado ≠ comunicação E2E comprovada.**

Nenhum PASS operacional deve ser declarado somente porque uma classe, endpoint ou botão foi encontrado no APK.