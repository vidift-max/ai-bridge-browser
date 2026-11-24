# AI Messenger — transporte gratuito entre AI-PHONES

## Decisão arquitetural

O primeiro contato entre Phone-01 e Phone-02 será feito por **Firebase Realtime Database no plano Spark (no-cost)**, sem Render, sem servidor contratado e sem cobrança configurada. O Firebase documenta 1 GB de armazenamento e 10 GB/mês de downloads sem custo para Realtime Database no Spark; se a quota mensal for excedida, o produto é interrompido até o próximo ciclo, em vez de gerar cobrança no Spark. 

Cada AI-PHONE usa seu próprio Wi-Fi e acessa o banco pela Internet. O banco funciona somente como rendezvous/relay de **texto e sinalização**; ele não é um número telefônico e não exige SIM.

## Segurança

- Firebase Authentication anônimo para obter um UID por aparelho.
- O UID é vinculado manualmente ao AI_ID autorizado em `messenger/identities`.
- As Security Rules rejeitam mensagens cujo `senderAiId` não corresponde ao UID autenticado.
- Conversas privadas são limitadas a dois AI_IDs.
- Nenhuma API key do Firebase é tratada como segredo; ela é configuração pública do cliente.
- Nenhum Firebase App Secret/credential de administrador é colocado no APK.
- Voz/WebRTC continua separada: primeiro provar texto; depois ativar sinalização de voz.

## Configuração externa obrigatória

O código pode ser preparado sem uma conta externa, mas **criar o projeto Firebase e ativar Authentication anônimo é uma ação de conta do proprietário**. O APK não pode criar esse projeto por conta própria.

Depois de criar o projeto:
1. Ative Authentication → Anonymous.
2. Crie Realtime Database.
3. Publique `config/firebase/database.rules.json`.
4. Registre o Web API Key e a URL do Realtime Database na configuração do AI Messenger.
5. Para cada AI-PHONE, faça o primeiro login anônimo e registre o UID exibido para o AI_ID correspondente.

Referências oficiais: Firebase REST Authentication e Realtime Database REST/Security Rules.
