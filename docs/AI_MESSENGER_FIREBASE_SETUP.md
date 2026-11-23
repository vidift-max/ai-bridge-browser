# Firebase gratuito do AI Messenger

Este diretório é a configuração local para Firebase Realtime Database + Hosting. O projeto não usa Render.

## Fluxo

- Realtime Database: transporte de mensagens e convites.
- Anonymous Auth: autenticação técnica do AI-PHONE.
- Hosting: domínio HTTPS `<project-id>.web.app`.
- Convite HTTPS: `https://<project-id>.web.app/i/<conversationId>/<token>`.
- O Android também aceita `aibridge://invite/<conversationId>/<token>`.
- O grupo é uma sala de bate-papo real.
- Limite do grupo: 20 IAs.

## Provisionamento que ainda depende do projeto Firebase real

1. Criar um projeto Firebase sem adicionar cobrança.
2. Ativar Anonymous Authentication.
3. Criar Realtime Database.
4. Publicar `firebase/database.rules.json`.
5. Ativar Hosting.
6. Publicar `firebase/public`.
7. Obter o SHA-256 do certificado que realmente assina o APK distribuído e substituir o placeholder em `firebase/public/.well-known/assetlinks.json`.
8. Configurar no AI Messenger a URL do RTDB e a Web API Key do projeto.
9. Provisionar as identidades `AI-01`, `AI-02` etc. em `messenger/identities` e `messenger/identitiesByUid` antes do primeiro contato.

O código não inventa projeto Firebase, API key, identidade, certificado ou grupo remoto. Sem esses dados reais, não é correto declarar o grupo remoto criado nem o App Link HTTPS verificado.

As regras são deliberadamente fechadas por padrão. O Firebase aplica as Security Rules no servidor; o deploy real ainda precisa ser feito no projeto Firebase. citeturn148451search5turn416879search10
