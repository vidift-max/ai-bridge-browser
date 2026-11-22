# AI-PHONE — Wi-Fi, internet, RAM e armazenamento

## Objetivo
Preparar cada AI-PHONE para acompanhar sua IA em diferentes locais e usar a internet disponível, sem presumir que o aplicativo possa descobrir senhas ou controlar redes sem autorização.

## Fluxo de conexão no aparelho
1. Na primeira entrega, a pessoa responsável abre **Configurar Wi-Fi no Android**.
2. Seleciona a rede local e informa a senha diretamente na tela de sistema do Android.
3. Ativa **Conectar automaticamente** para essa rede, quando a opção existir.
4. O Android guarda a credencial no armazenamento protegido do sistema e administra a reconexão quando a rede conhecida estiver ao alcance.
5. Em outro local, se houver uma rede nova, a IA ou o responsável deverá escolher a rede e autorizar a senha. O aplicativo não pode ler senhas Wi-Fi salvas nem descobrir senhas de redes próximas.
6. Ao voltar ao AI-PHONE, usar **Atualizar diagnóstico** para conferir se o Wi-Fi está conectado e se o Android validou acesso à internet.

## O que o app verifica
A tela inicial mostra:
- Se a rede ativa usa Wi-Fi.
- Se existe capacidade de internet e se o Android validou a conectividade.
- RAM física total e RAM atualmente disponível.
- Armazenamento interno total e espaço livre.

A leitura é somente diagnóstica. O espaço livre exibido é do armazenamento interno do dispositivo, não uma garantia de espaço exclusivo do app.

## Limites do Android
- O Android é responsável por armazenar senhas e reconectar redes previamente autorizadas.
- O app não tenta extrair senhas, contornar telas de permissão, ligar o Wi-Fi à força ou conectar-se a redes protegidas sem autorização.
- APIs de sugestão de rede podem exigir permissões, aprovação do sistema e comportamento diferente conforme versão/fabricante; não prometemos conexão silenciosa ou imediata.
- O AI-PHONE necessita de internet funcional para recursos remotos. Sem internet, apenas recursos locais/offline poderão funcionar.
- Chamadas e mensagens remotas ainda exigem backend acessível, autenticação, notificações e implementação de voz; Wi-Fi por si só não fornece esses serviços.

## Requisitos de hardware recomendados para aparelhos a comprar
Estes são alvos de compra, não medições de um aparelho já testado:
- Android 10 ou superior (o app atual declara minSdk 29).
- **Mínimo prático recomendado:** 4 GB de RAM e 64 GB de armazenamento.
- **Preferível para uma experiência profissional:** 6–8 GB de RAM e 128 GB de armazenamento.
- Wi-Fi dual-band 2,4/5 GHz (Wi-Fi 5 ou superior).
- Bateria em bom estado e atualizações de segurança do fabricante.
- Internet estável; 10 Mbps ou mais é uma meta confortável para uso geral, mas chamadas podem exigir estabilidade/latência melhores.

Como as IAs usarão serviços remotos, a RAM do telefone não executará necessariamente o modelo de IA. Se futuramente houver inferência local, os requisitos deverão ser reavaliados e serão significativamente maiores.

## Estado de implementação
- Diagnóstico de rede ativa, RAM e armazenamento: implementado na tela inicial.
- Atalho para configurações Wi-Fi do Android: implementado.
- Reconexão de redes já salvas: responsabilidade do Android, depende da configuração do sistema.
- Descoberta de senhas ou conexão sem autorização: não implementada e não será implementada.
- Teste em aparelho físico: pendente.
- Mensagens remotas, chamadas e funcionamento contínuo em segundo plano: não comprovados por esta entrega.
