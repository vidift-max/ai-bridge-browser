# Missão 18 — Local AI Engine & Free Multi-AI Communication

## Dez rodadas executadas
1. Rechecamos a CI da Missão 17: 345/346 testes passaram; a única falha era uma expectativa antiga por `REQUEST_SUCCEEDED`.
2. Corrigimos o contrato do teste para exigir `DISABLED_BY_POLICY` quando a política gratuita está fechada. A correção foi commitada na branch da Missão 17.
3. Criamos branch isolada da Missão 18 baseada no commit de correção.
4. Auditamos o mensageiro existente: autenticação individual, salas privadas/grupo, destinatários limitados aos membros e fila persistente de mensagens.
5. Auditamos o verificador WebGPU existente: ele só consulta capacidades locais e não baixa modelos nem chama endpoints externos.
6. Criamos um catálogo de engines locais que não presume runtime instalado nem inferência disponível.
7. Expusemos o catálogo por endpoint autenticado `GET /v1/local-ai`, com auditoria.
8. Integramos botão manual de verificação local à Central de Salas; não executa automaticamente nem baixa modelos.
9. Reforçamos testes de fan-out de mensagens em grupo e bloqueio de destinatários fora da sala.
10. Documentamos limites, escopo de execução e workflow de CI. PR draft será aberta após revisão do diff.

## Limites
- Browser WebGPU: apenas candidato de capacidade; nenhum modelo carregado e nenhuma inferência.
- Ollama e llama.cpp: catalogados como não implementados.
- Um Ollama em loopback do servidor seria local ao host servidor, não ao tablet do usuário.
- Mensageiro suporta transporte interno autenticado, mas não faz o modelo de cada IA pensar ou responder automaticamente.
- Nenhum download de modelo, instalação, chamada de API paga, chave, custo, merge ou deploy.
