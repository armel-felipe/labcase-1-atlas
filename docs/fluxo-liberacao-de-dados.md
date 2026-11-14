# Fluxo de liberação de dados do Case Atlas

## Objetivo e limites

Este fluxo libera somente arquivos CSV do data room do facilitador. A conversa de entrevista continua acontecendo no workspace Case Atlas do AnythingLLM. Não há aprovação humana posterior: a publicação depende da decisão lógica do facilitador e da persona entrevistada, representados em duas avaliações separadas.

O AnythingLLM usado pelos consultores não monta `99_Facilitador/`. Um serviço privado é o único componente com acesso a essa pasta, montada em leitura. O serviço valida o arquivo e o escopo, exporta uma cópia autorizada e preserva os CSVs originais.

## Componentes e fronteiras

| Componente | Responsabilidade | Acesso aos dados |
|---|---|---|
| AnythingLLM — workspace Case Atlas | Conversa com consultores, entrevistas e chamada do custom Agent Skill | Briefing público e `memoria/`; sem acesso a `99_Facilitador/` |
| Custom Agent Skill | Cria o pedido, carrega o contexto escolhido, encaminha as decisões e retorna o link | Não lê arquivos nem recebe linhas do CSV |
| Provedor LLM do workspace | Avalia separadamente o facilitador e a persona entrevistada | Recebe a política geral, apenas o perfil selecionado e as últimas 12 mensagens; não recebe linhas do CSV |
| Serviço `case-release` | Lê a fonte, valida o consenso e o escopo, registra a proveniência e exporta a cópia | Lê `99_Facilitador/` em modo somente leitura |
| SQLite e armazenamento de artefatos | Mantêm pedidos, decisões, hashes, CSVs liberados e revogações | Volume persistente fora do Git |
| Caddy | Protege o link de download com Basic Auth individual e token interno de gateway | Encaminha apenas a rota de download ao serviço |

O serviço não publica porta no host. `99_Facilitador/` não aparece nos mounts do AnythingLLM; somente o serviço de liberação pode ler essa pasta.

## Sequência do pedido

1. O consultor pede um arquivo ou recorte no chat. O agente coleta arquivo, finalidade, colunas, período e salvaguardas; informação insuficiente deve levar a perguntas.
2. O custom skill lê do contexto interno do AnythingLLM o workspace, o usuário autenticado e o chat original. Não aceita esses identificadores como argumentos livres do modelo e falha fechado se não conseguir obtê-los.
3. O skill cria o pedido no serviço privado. O serviço confere o catálogo fechado de CSVs e colunas e verifica se existe uma liberação reutilizável.
4. Para um pedido novo, o serviço devolve a política geral de liberação e somente o perfil da persona selecionada. O skill envia esse contexto e as últimas 12 mensagens do chat ao provedor configurado no workspace.
5. O modelo faz duas avaliações de role-play separadas: primeiro como facilitador, depois como a pessoa entrevistada. Cada uma pode permitir, limitar, pedir esclarecimento ou recusar.
6. O serviço valida os resultados, calcula a interseção dos escopos permitidos e só exporta dados se ambas as avaliações permitirem. Recusa, dúvida, conflito, resultado inválido ou escopo vazio não gera arquivo. Filtros que o exportador não consegue aplicar também levam a esclarecimento; não são descartados silenciosamente.
7. O exportador gera uma cópia determinística com as colunas autorizadas e, quando aplicável, o período autorizado. A fonte não é modificada. O serviço registra solicitante, chat de origem, data, justificativas, escopo, hash da fonte e hash do artefato.
8. O skill retorna ao chat o resultado e, quando houver liberação, um link estável de download.
9. O consultor baixa pelo Caddy com uma credencial Basic individual. A autenticação do download é separada do login e da permissão de acesso ao chat do AnythingLLM.

## Reutilização e disponibilidade

- Uma liberação pode ser reutilizada entre conversas e por qualquer consultor com credencial de download válida, mesmo sem acesso ao chat original.
- A reutilização automática exige a mesma finalidade, escopo, salvaguardas e hash atual da fonte. Um escopo mais estreito pode gerar uma cópia derivada sob as mesmas condições.
- Mudança de finalidade, salvaguardas, fonte ou pedido mais amplo exige nova avaliação.
- O link não expira automaticamente. Uma liberação pode ser revogada explicitamente; a revogação impede novos downloads.
- O chat original permanece no histórico do AnythingLLM. O registro de liberação guarda a referência da conversa, sem duplicar toda a transcrição.

## Dados enviados ao provedor LLM

Para avaliar um pedido novo, o skill envia ao provedor do workspace a política geral, o perfil da persona escolhida e as últimas 12 mensagens do chat. No ambiente implantado, o provedor é `generic-openai` com endpoint `router.hostinger.com`. O CSV original e suas linhas não são enviados ao modelo.

## Estado da implantação

O serviço, o skill e a rota de download autenticada estão ativos na VPS. O serviço está saudável, não publica porta no host e lê a pasta do facilitador somente em modo leitura. O Caddy exige autenticação individual e encaminha a rota protegida ao serviço. Os testes de unidade e de fronteira de autenticação passaram.

Ainda falta o piloto em uma conversa autenticada na interface para confirmar a captura real dos IDs de usuário/chat e o comportamento do provedor ao acionar a ferramenta. Nenhum CSV foi liberado por esse fluxo até o momento. O primeiro teste deve usar um pedido vago e confirmar que o agente pede esclarecimento sem gerar link.
