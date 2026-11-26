# M210 — AI-01 ↔ AI-02: preparação da atualização

## Objetivo
Corrigir a validação de build para o layout real do repositório e produzir um APK debug verificável para o primeiro teste físico controlado.

## Escopo e limites
- Somente AI-01 e AI-02.
- Não iniciar conversa automaticamente.
- Não ativar AI-03.
- Não executar login, preencher credenciais ou contornar MFA.
- Não fazer merge, publicar Release oficial ou instalar no dispositivo.
- APK debug não é atualização garantida de uma instalação assinada com outra chave.

## Diagnóstico confirmado
O workflow M209 falhou no passo `chmod +x ./gradlew`: o repositório não contém `gradlew` nem Gradle Wrapper. O workflow Android existente usa Gradle 9.6.0 via `gradle/actions/setup-gradle@v4` e comandos `gradle :app:...`. M210 adota o mesmo método conhecido.

## Dez rodadas
1. Conferir o resultado real do workflow M209.
2. Inspecionar logs e identificar a falha antes da compilação.
3. Auditar a árvore Git e confirmar ausência de `gradlew`/wrapper.
4. Comparar com o workflow Android já existente no repositório.
5. Criar branch isolada a partir do HEAD M209.
6. Corrigir o workflow para configurar Gradle 9.6.0.
7. Executar testes JVM/Android e montagem do APK debug no CI.
8. Exigir que o APK exista e não esteja vazio.
9. Publicar o APK somente como artefato temporário do GitHub Actions, com hash a conferir; sem Release oficial.
10. Manter PR Draft e aguardar CI; não declarar pronto para atualizar sem CI verde, artefato conferido e compatibilidade de assinatura/dispositivo esclarecida.

## Critério de aprovação
PASS de build somente com testes e assembleDebug concluídos com sucesso e artefato APK disponível. Isso não prova instalação física, preservação de dados, autenticação das duas contas ou conversa AI↔AI real.

## Estado inicial
Em andamento. O botão AI ↔ AI permanece sujeito ao teste físico com duas sessões autenticadas e isoladas.
