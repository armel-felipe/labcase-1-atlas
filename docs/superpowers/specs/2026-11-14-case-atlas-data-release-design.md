# Case Atlas — liberação automática de dados pelo facilitador

**Status:** aprovado; serviço, custom skill e rota autenticada ativos na VPS; piloto de conversa pendente
**Data:** 2026-11-14

## Intenção

Adicionar ao workspace Case Atlas do AnythingLLM um mecanismo de liberação de arquivos de dados. O fluxo de entrevistas existente não muda. O material reservado continua fora do alcance direto do AnythingLLM usado pelos consultores. Quando a negociação do caso autorizar um arquivo ou recorte, o sistema registra a decisão, gera uma cópia controlada e disponibiliza um link permanente para toda a equipe.

A permissão de liberação é uma decisão de role-play, produzida automaticamente conforme o guia do caso. Não existe aprovação humana posterior.

## Objetivos

- Manter a interface de conversa dos consultores no AnythingLLM.
- Avaliar pedidos de dados conforme finalidade, escopo, campos, período e salvaguardas; permitir liberação completa, parcial, pedido de esclarecimento ou recusa.
- Gerar arquivos a partir de originais imutáveis com filtros determinísticos.
- Registrar a decisão, a conversa de origem e o artefato liberado.
- Permitir que qualquer consultor do Case Atlas baixe uma liberação publicada mesmo sem acesso ao chat original.
- Entregar CSV por URL estável, sem expiração automática.

## Abordagens consideradas

1. **Montar `99_Facilitador` no AnythingLLM principal e confiar nas instruções do agente.** Rejeitada. Os agentes compartilham ferramentas entre workspaces; o File System Agent teria acesso ao material reservado e instruções do modelo não são uma barreira de dados.
2. **Custom Agent Skill no AnythingLLM mais um serviço interno privilegiado.** **Selecionada.** O skill recebe pedidos e consulta resultados; um serviço separado lê os arquivos reservados, aplica a política simulada, cria os artefatos e registra decisões. Mantém a interface em AnythingLLM e separa o acesso aos dados.
3. **Segunda instância do AnythingLLM exclusiva do facilitador.** Tecnicamente possível, mas aumenta manutenção. Uma segunda instância não elimina a necessidade de um registro de liberações, exportador determinístico e canal de entrega integrado ao chat principal.

## Arquitetura escolhida

A instância consultora continua em Docker e mantém somente os mounts já existentes:

- `00_Para_Consultores/` em somente leitura;
- `memoria/` em leitura e escrita;
- nenhum mount de `99_Facilitador/`.

Um custom Agent Skill confiável, instalado na instância consultora, envia pedidos estruturados e consulta status/artefatos. O skill **não** lê arquivos locais, não recebe chave administrativa da API do AnythingLLM e não decide caminhos de arquivo.

Um serviço interno separado recebe os pedidos. Só esse serviço monta `/opt/agent-projects/case_lab/99_Facilitador` em somente leitura. O backend local implementado recebe duas decisões estruturadas do adaptador e aplica o consenso:

1. **Facilitador:** verifica se há objetivo, período, campos e salvaguardas suficientes e propõe liberação completa, parcial, esclarecimento ou recusa segundo o guia reservado.
2. **Stakeholder:** responde como a persona entrevistada no role-play de negociação, podendo aceitar, limitar ou recusar conforme seu perfil e o contexto da conversa.

O serviço só publica dados quando a decisão estruturada autoriza a liberação e passa pelas validações determinísticas. Essas funções podem usar o mesmo provedor/modelo, mas são etapas separadas e registradas. Não há pessoa aprovando o resultado.

## Fluxo

### Pedidos de arquivos

1. O consultor descreve arquivo, finalidade, período, colunas e salvaguardas. Se faltarem informações, o agente pergunta antes de avaliar.
2. O serviço consulta o guia e produz uma decisão estruturada: `complete`, `partial`, `clarify` ou `refuse`, com justificativa e escopo permitido.
3. Um validador limita a decisão a nomes de arquivo, colunas, períodos e operações permitidos. O modelo nunca fornece um caminho arbitrário, SQL livre ou conteúdo CSV para ser publicado diretamente.
4. Se a decisão autorizar dados, um exportador determinístico filtra uma cópia dos CSVs originais. O original nunca é alterado.
5. O arquivo recebe um identificador de liberação, versão/hash da fonte e hash do resultado. A cópia aprovada fica no armazenamento persistente de liberações.
6. O skill informa a decisão e, quando houver arquivo, devolve o link de download no chat.

### Regras de decisão propostas

- O facilitador e o stakeholder responsável precisam concordar com a liberação. O facilitador determina a elegibilidade e o escopo; a persona entrevistada expressa a disposição de compartilhar. Se qualquer um recusar, não há arquivo. Se divergirem ou faltar contexto, o sistema pede esclarecimento em vez de ampliar a liberação.
- O stakeholder é escolhido pelo consultor ou por um mapa versionado entre domínios de dados e personas. Pedidos que cruzem domínios precisam de concordância das personas envolvidas; o facilitador coordena a negociação.
- A elegibilidade segue a política existente em `99_Facilitador/guia_facilitador.md`. Arquivos e colunas vêm de um catálogo fechado baseado no esquema real dos CSVs. Não se aceitam caminhos, colunas ou consultas SQL arbitrárias. Campos técnicos necessários para cruzamentos podem ser liberados quando o escopo e o propósito os justificarem.
- `complete` significa que todos os campos e o período pedidos foram autorizados; `partial` deve declarar exatamente o subconjunto permitido. O exportador nunca acrescenta campos nem linhas fora da decisão. Resultado inválido, ambíguo ou incompatível com o catálogo falha fechado.
- Agent Mode deve aceitar pedidos em linguagem natural como experiência principal. Chamadas de ferramenta dependem do modelo/provedor; o piloto valida o provider atual. Se a chamada natural não funcionar, `@agent` é o fallback operacional até que se resolva a compatibilidade.

### Reutilização de liberações

A equipe pode reutilizar uma liberação registrada em qualquer conversa. Um pedido com o mesmo propósito, escopo, salvaguardas e hash atual da fonte recebe o mesmo artefato. Um pedido mais restrito pode gerar uma cópia derivada menor sob essas mesmas condições, nunca receber o arquivo mais amplo sem necessidade. Um pedido mais amplo, com finalidade ou salvaguardas diferentes, ou baseado em outra versão da fonte, passa por nova negociação. Conversas em andamento não são transferidas implicitamente entre threads; somente liberações concluídas são estado compartilhado. Mudanças nos arquivos-fonte criam uma nova versão e não alteram retroativamente liberações já registradas.

## Registro de decisões

Cada solicitação registra:

- identificador do pedido;
- workspace e referência/ID do chat original;
- identidade do consultor solicitante;
- tipo: entrevista ou dados;
- persona ou arquivo solicitado;
- finalidade, período, campos e salvaguardas informados;
- perguntas de esclarecimento e decisões de role-play;
- resultado: completa, parcial, esclarecimento ou recusa;
- justificativa e escopo efetivamente liberado;
- versão/hash dos dados-fonte e hash do artefato;
- data/hora UTC, status da publicação e URL estável;
- estado opcional de revogação.

O pedido, as justificativas, os esclarecimentos e a negociação ficam no histórico do chat original do AnythingLLM. Além desse histórico, o registro de liberação é separado e durável: guarda a decisão e a referência/ID do chat de origem, para que o pedido conste como origem da liberação e o artefato continue localizável mesmo se outro consultor não puder abrir aquela conversa. O registro não substitui nem precisa duplicar a transcrição completa do chat.

O backend já armazena `requester_id` e `origin_thread_id`. O custom skill obtém `user_id` e `trackedChatId` do contexto interno do AnythingLLM 1.19.0, não de argumentos produzidos pelo modelo. Essa forma foi confirmada por inspeção do código da versão em execução, mas não é uma interface pública garantida; o skill falha fechado quando esses campos faltam. Antes do uso real, validar por invocação no workspace e repetir após atualizações do AnythingLLM.

O skill encaminha ao avaliador as últimas 12 mensagens da conversa junto com a política geral e somente o perfil da persona selecionada. No ambiente inspecionado, o AnythingLLM usa provider `generic-openai` em `router.hostinger.com`; portanto esse conteúdo passa por esse provider. CSVs e linhas da fonte não são enviados ao modelo. O responsável pelo projeto precisa confirmar que esse tratamento é aceitável antes de ativar o skill.

## Download permanente

O URL do CSV não expira automaticamente e não depende do chat original. A decisão padrão deste desenho é que o link funcione para membros autenticados do workspace/equipe Case Atlas, mesmo em outro chat. A URL pode ser revogada explicitamente por administração; isso não é expiração automática.

O endereço é estável por identificador de liberação e nome do arquivo. A resposta HTTP deve forçar download com nome legível. Compartilhar a URL dentro da equipe não deve exigir que a pessoa tenha acesso à thread de origem.

## Limites do AnythingLLM e fronteiras de segurança

- Todos os agentes compartilham as ferramentas entre workspaces. Portanto, não usar um workspace “Facilitador” na mesma instância como isolamento do acesso a `99_Facilitador`.
- O File System Agent no Docker pesquisa diretórios montados sob `/app/server/storage/anythingllm-fs`; ele permanece configurado somente com os mounts públicos e a memória atuais.
- Custom Agent Skills executam código Node.js no processo do AnythingLLM e podem chamar APIs. Instalar somente o skill próprio, revisado e de escopo estreito.
- A aprovação nativa de chamadas de ferramenta do AnythingLLM pede confirmação ao usuário que iniciou a chamada; ela não representa a decisão do stakeholder e não é usada como gate deste fluxo.
- Uma chave da API do AnythingLLM permite operações amplas. O skill não recebe chave administrativa. O acesso ao serviço interno usa credencial própria, restrita a criar pedidos e buscar liberações da equipe.
- A URL permanente não deve ser uma URL pública sem controle. O endpoint de download verifica autenticação/membership da equipe, mas não exige acesso ao chat original.
- O modelo pode errar o julgamento de role-play. O validador reduz o impacto limitando arquivo, período, colunas e volume; em decisão incompleta, fora da política ou inválida, não gera arquivo e pede esclarecimento/recusa.
- A documentação dos custom Agent Skills descreve os parâmetros da ferramenta e o retorno de texto, mas não documenta os campos internos usados para obter usuário e chat. O skill depende do runtime observado no AnythingLLM 1.19.0 e falha fechado se mudar. [Guia oficial de custom skills](https://docs.anythingllm.com/agent/custom/developer-guide), [referência do handler](https://docs.anythingllm.com/agent/custom/handler-js).

## Fora de escopo

- Não montar `99_Facilitador` no contêiner AnythingLLM dos consultores.
- Não alterar os CSVs originais nem versionar artefatos de liberação no GitHub.
- Não alterar o fluxo existente de entrevistas.
- Não exigir aprovação humana de arquivos; a liberação depende do consenso lógico no role-play.
- Não disponibilizar arquivos a pessoas fora da equipe Case Atlas por meio do link permanente.
- Não prometer que instruções de prompt, sem validação no serviço, constituem controle de acesso.

## Critérios de aceite

1. Pedido vago resulta em esclarecimento, não em liberação.
2. Pedido aceito gera CSV apenas com linhas/colunas autorizadas; pedido parcial gera um recorte; recusa não produz artefato.
3. Tentativas de usar caminhos `../`, nomes arbitrários, SQL ou instruções de prompt para ignorar a política não ampliam o acesso.
4. Qualquer membro do Case Atlas consegue baixar uma liberação aprovada em outro chat, sem acesso à thread de origem.
5. A URL permanece válida sem expiração automática e pode ser revogada explicitamente.
6. Repetir pedido com o mesmo escopo reutiliza o mesmo artefato; escopo mais amplo exige nova avaliação.
7. O registro aponta ao chat original e preserva decisão, escopo, data, fonte e hash do artefato.
8. Falha do modelo, do serviço, da validação ou do armazenamento não libera dados.

## Implementação e estado atual da integração

O serviço em `release_service/` implementa catálogo fechado, validação de consenso, exportação de um CSV por pedido, persistência SQLite, identidade obtida pelo adaptador, hashes, reutilização e revogação. `compose.release.yml` executa o container sem publicar porta no host, conectado às redes Docker do AnythingLLM e do Caddy, e monta os dados reservados em somente leitura. A API exige token para mutações e token separado no endpoint de download; executada fora do Compose, escuta em loopback por padrão. Os testes locais cobrem essas partes.

O backend está ativo em Compose nas redes internas do AnythingLLM e do Caddy, sem porta publicada; monta `99_Facilitador/` em somente leitura apenas no serviço. O skill está instalado e ativo em `/app/server/storage/plugins/agent-skills/case-atlas-release/`, e o Caddy protege a rota estável com Basic Auth individual e token de gateway. Os testes de health e da fronteira do Caddy passaram. Ainda é necessário realizar um pedido de teste pela interface do workspace para validar a captura de usuário/chat no runtime real e a resposta do provider `router.hostinger.com`.

## Piloto de conversa ainda necessário

- Se o contexto interno do AnythingLLM 1.19.0 fornece `user_id` e `trackedChatId` corretamente durante o piloto real de chat.
- Se a chamada de ferramenta em linguagem natural aciona o skill com o provider atual; caso não, use `@agent` como modo de teste.
- Se uma solicitação vaga resulta em esclarecimento e uma solicitação justificada produz decisão, registro e link conforme o fluxo.
- Se as contas da equipe conseguem baixar em outro chat com as credenciais Basic individuais.
