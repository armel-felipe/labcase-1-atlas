# Guia reservado do facilitador

> Material exclusivamente para facilitar o caso. Não abrir no Work dos consultores. A separação de pastas organiza o pacote, não garante sigilo real.

## Verdade-base fixa do cenário

O cenário tem deterioração interdependente, não um culpado único. A linha canônica para avaliação é:

1. **Governança de prioridades instável.** A Atlas não mantém uma janela congelada comum entre Comercial, PCP e Produção. Pedidos de alteração, urgências e revisões de previsão entram por canais diferentes; algumas alterações são aceitas e algumas recusadas, mas o plano-base, a decisão e o sequenciamento efetivamente executado nem sempre ficam reconciliados. A consequência prevista é maior retrabalho de programação, setups e dificuldade de prometer datas confiáveis.
2. **Confiabilidade e execução preventiva frágeis.** Parte das preventivas fica aguardando janela; o histórico de falhas mistura falhas, ajustes de processo e setups longos. O ativo A tem relevância econômica maior pela margem de contribuição, mas ainda precisa quantificar sua perda de disponibilidade. Manutenção e produção descrevem reciprocamente o gargalo de liberação/resposta.
3. **Suprimento mais lento e contenção cara.** O lead time realizado de compras piora em parte do período final. O mix de urgências e a carteira em atraso aumentam a pressão para expedir por modalidade emergencial. O frete urgente torna-se material para caixa e EBITDA.
4. **Efeito de negócio:** pedidos crescem de 2.200 para 2.750 unidades semanais no resumo, enquanto expedição e produção não acompanham. Backlog chega a 3.500; OTIF cai de 88% para 54%; receita cai e EBITDA chega a −R$ 800 mil.

Essa é a verdade de base que o facilitador manterá estável. O diagnóstico final dos consultores pode ser diferente e ainda receber boa avaliação se fizer distinção entre dado, inferência e lacuna, priorizar testes e propuser ações reversíveis. Os CSVs oferecem sinais e algumas associações, **não prova experimental de causalidade**. Não trate proximidade temporal ou correlação como prova de causa. A entrevista bem conduzida permite reconhecer rotinas, responsabilidades e limites de registro; isso não converte depoimento em dado auditado.

## Evidências preparadas e lacunas deliberadas

- `pedidos.csv`: carteira de abertura = 600; demanda e mix semanal; canal identifica parte dos pedidos de urgência, não todos os compromissos informais.
- `alteracoes_programacao.csv`: pedido, origem, motivo, decisão e datas propostas. Nas oito semanas W19–W26 há 152 solicitações (99 aceitas, 53 recusadas); 72 vieram de Comercial, 46 de Produção e 34 de PCP. Nas 18 semanas anteriores houve 192 solicitações. A taxa por semana aumenta, mas as decisões ainda precisam ser comparadas com o plano realmente executado. O evento pode ser recusado e não comprova que a sequência mudou.
- `producao.csv`: produção boa bate as oito semanas resumidas; grão SKU × dia útil × turno; 470 de 2.640 linhas recentes (17,8%) têm prioridade manual, ante 510 de 5.940 (8,6%) nas 18 semanas anteriores. O indicador não identifica por si só o solicitante nem o efeito de cada mudança.
- `paradas.csv` + `manutencao.csv`: liga paradas a uma ordem na mesma semana/máquina. Nas oito semanas recentes foram 74 eventos e 115,1 horas; linha A teve 47,2 horas (5,90 h/semana), B 34,6 (4,33 h/semana) e C 33,3 (4,16 h/semana). Nas 18 semanas anteriores A tinha 81,9 horas (4,55 h/semana), B 77,2 (4,29 h/semana) e C 71,6 (3,98 h/semana). A exposição recente da linha A cresceu, mas é um sinal a investigar, não prova de causa raiz. Categoria informada tem ruído e não confirma causa. Duas ordens preventivas recentes com zero hora representam janela pendente.
- `previsoes.csv`: seis versões para cada SKU/semana; comparar baseline congelado (primeira emissão ou a que entrevistado confirmar) com revisões e demanda. O rótulo de versão não identifica qual foi oficialmente aprovado.
- `compras.csv` + `movimentos_estoque.csv`: nas ordens emitidas em W01–W18 e recebidas até o corte, 32/72 chegaram após a data prometida (atraso médio de 7,1 dias entre as atrasadas); em W19–W26, 7/17 (7,3 dias). A incidência não aumenta nesse recorte; não sustente que suprimentos isoladamente causaram a crise. Compras e movimentos são ligados por IDs, mas não há saldo diário por endereço nem prova de falta na máquina.
- `expedicoes.csv` + `logistica.csv`: IDs e valores conciliam; os lançamentos emergenciais fecham os três valores do resumo financeiro por janela gerencial. O tipo de frete foi preparado para reconciliar os controles sintéticos; não é evidência independente de que a urgência ou atraso específico causou o custo. OTIF continua sendo o resumo gerencial independente.
- `financeiro_mensal.csv`: os três ciclos de quatro semanas fecham aritmeticamente. Receita e custos variáveis são controles gerenciais sintéticos, não rollups das unidades expedidas × preço/custo de referência. Não há faturamento, descontos, devoluções nem apropriação de custo transacional para fechar essa ponte. Os custos por SKU são parâmetros de referência; não suportam ROI detalhado sem premissas adicionais.

### Inconsistências propositais

Não inserir nem inventar inconsistências de registros como “pegadinha”. Os arquivos atuais passaram pelos controles automáticos. Há **limitações de medição deliberadas** descritas acima — pedido de mudança não significa execução; OTIF não tem microdados suficientes; baseline de previsão requer validação. Estas lacunas estão explícitas no gabarito e no dicionário. Se uma futura edição inserir discrepância real, documentar aqui o campo, extensão, motivo e pista antes de liberá-la.

## Política de liberação de informação

Materialize e preserve os CSVs originais. Conceda dados conforme a equipe peça, anote cópia/recorte e não reescreva a verdade-base para favorecer a hipótese apresentada. Requisição vaga pode receber pergunta de escopo. Para cada pacote, classifique: completo, parcial ou não concedido, com a razão em linguagem de stakeholder. Toda recusa admite reengajamento: a equipe pode explicar propósito, limitar período/campos, oferecer salvaguarda ou trazer evidência que reduza o risco percebido.

### Seis perfis e respostas

| Stakeholder | O que tende a compartilhar | Parcial ou recusa quando | Reengajamento útil |
|---|---|---|---|
| CEO Helena Duarte | mandato, decisões, reclamações e limites de caixa em nível executivo | pedem opinião de culpa ou prometem recuperação sem evidência | mostrar decisão que a informação apoiará e separar decisão reversível de capex |
| Diretor industrial Roberto Nogueira | capacidade teórica, turnos, produção agregada e necessidade percebida de máquina | pedem causa individual de falha sem ordem ou congelamento de operação | pedir um recorte de semanas/linha e comparar versão do plano com realizado |
| Manutenção Marcos Vieira | backlog, preventiva, peças e registros de falha por ativo | atribuem falha à equipe sem contexto, ou ignoram bloqueio/segurança | reconhecer restrição, pedir cronologia e validar amostra com produção |
| Comercial Ana Paiva | clientes em risco, promessas, urgências e reclamações com recorte | pedem margem confidencial por cliente ou tratam toda urgência como erro comercial | solicitar dados agregados/anonimizados e distinguir exceção de carteira normal |
| PCP Lucas Mendes | versões de previsão e programação, regras conhecidas, alterações | pedem “a causa” ou acusam falta de disciplina sem comparar baseline | trazer janela, granularidade e decisão específica; perguntar quem aprovou/executou |
| Financeiro Beatriz Campos | resumo gerencial, fretes, caixa e regra de aprovação | proposta não tem custo, benefício, prazo, risco ou fonte | apresentar premissas, intervalo, sensibilidade e piloto limitado ao teto |

### Critérios de concessão

- **Completa:** finalidade clara, escopo proporcional, IDs necessários, tratamento adequado de informação sensível e análise sem acusação prematura.
- **Parcial:** a pergunta tem valor, mas está ampla, inclui dado sensível ou mistura hipóteses. Entregar agregado, período curto, campos mínimos ou explicar a lacuna.
- **Recusa fundamentada:** pedido não tem objetivo, busca informação pessoal/confidencial desnecessária, viola segurança operacional ou tenta responsabilizar alguém sem evidência. Explicar a razão e sugerir caminho seguro.
- **Reengajamento:** sempre possível. A resposta muda de nível se o grupo reformular, demonstrar salvaguarda ou cruzar uma evidência pertinente. Não criar novos fatos para recompensar eloquência.

## Entrevistas — segredos de personagem

Use somente ao responder à solicitação. O papel dá perspectiva e limitação, não onisciência.

- **Helena:** sabe que não há aprovação da máquina e teme perder contas/credibilidade. Se a equipe apresentar um quadro comparativo de serviço, caixa e alternativas, compartilha notas executivas de risco de clientes, ainda não auditadas. Se pressionada por culpado, responde: “Não vou escolher uma área sem cronologia.”
- **Roberto:** defende avaliar máquina, mas reconhece que o pedido nasceu de capacidade nominal, sem OEE medido ou estudo de gargalo. Entrega apontamentos agregados primeiro; pode detalhar uma linha se a equipe comparar tempo programado, parada, setup, velocidade e refugo sem chamar tudo de capacidade perdida.
- **Marcos:** relata manutenção preventiva esperando janela e registros pouco padronizados. Entrega criticidade e ordens; recusa ranking de culpados. Com uma amostra de paradas, ajuda a separar quebra, ajuste e setup e pede validação conjunta de ordem/turno.
- **Ana:** tem mensagens de clientes e urgências, mas não quer expor termos individuais sem necessidade. Entrega carteira anonimizada e datas se a equipe justificar proteção de conta; distingue data solicitada, prometida e revisada.
- **Lucas:** reconhece versões e pedidos de mudança, mas não tem uma trilha única de “solicitado → aceito → comunicado → executado”. Entrega versões por semana; parcial para dados sem filtro. Pode confirmar baseline se perguntado por período e quem aprovou.
- **Beatriz:** os três meses gerenciais fecham, mas não a margem por pedido. Pode abrir uma análise agregada de frete e contribuição após ver hipótese quantificada. Recusa ROI pontual sem faixa de benefício e risco; aceita sensibilidade com premissas explícitas.

## Eventos inesperados e evolução

Dispare um evento por vez, após a rodada de diagnóstico ou uma decisão relevante. Não altere retroativamente os arquivos-base. Marque cada evento como informação recebida e permita que o grupo solicite dados adicionais.

1. **Cliente âncora pede recuperação em 10 dias (dia 3).** Compartilhe que a conta concentra parte relevante da carteira atrasada, sem revelar margem por SKU. Testa segmentação, promessa realista, plano de comunicação e risco de priorizar uma conta em detrimento das demais.
2. **Falha crítica em M-A1 (dia 6).** Parada adicional de 12 horas, ocorrência fora da amostra já entregue. O facilitador pode liberar custo/peça após pedido. Testa segurança, contingência, governança de alocação e impacto econômico marginal; não prova que a manutenção seja a única causa.
3. **Fornecedor informa atraso de 7 dias em material A (dia 9).** Testa estoque de segurança, substituição aprovada, sequência e decisão de cliente. Não permitir substituição sem qualidade/engenharia.

### Regras fixas para evolução

- Recalcule o estado apenas em checkpoint (dias 15 e 90), usando decisões registradas; não improvise resultado no meio de uma apresentação.
- Pontue cada iniciativa proposta em 0–2 para: hipótese/evidência, dono e rotina, dependência, custo ≤ orçamento, métrica e gatilho de correção. Só iniciativas com pelo menos 8/10 entram no cenário implementado.
- Para cada ação, registrar faixa esperada, prazo e confiança. Sem base quantitativa, o resultado segue “não quantificado”; não inventar uplift.
- Se prioridade e freeze window melhorarem, no máximo reduzir em 10–20% a exposição a setups de sequência nas semanas seguintes; se persistir sem governança, manter instabilidade. É uma premissa de simulação a declarar ao grupo, não um fato observado.
- Para preventiva, só reduzir exposição à falha após janela segura aprovada e execução comprovada; uma ordem aberta não muda disponibilidade. Uma intervenção pequena pode consumir orçamento e gerar benefício apenas a partir do checkpoint seguinte.
- Frete, caixa e EBITDA só mudam com redução de expedição emergencial ou custos explicitamente modelados; não converta produção adicional automaticamente em receita ou caixa.
- Para avaliação financeira, utilizar contribuições de referência (A R$570, B R$260, C R$70 por unidade) e apresentar cenário inferior/base/superior, evitando dupla contagem com custos fixos/frete.

## Avaliação da equipe (100 pontos)

| Dimensão | Pontos | Evidência esperada |
|---|---:|---|
| Formulação do problema e árvore de hipóteses | 15 | Sintomas e causas possíveis separados; perguntas testáveis |
| Dados e qualidade de investigação | 20 | IDs/datas cruzados, reconciliação, limites e pedidos proporcionais |
| Entrevistas e gestão de stakeholders | 15 | Escuta, perguntas neutras, negociação de informação e reengajamento |
| Análise operacional e confiabilidade | 15 | Demanda/mix/capacidade, perdas, setups, PM, materiais e segurança |
| Impacto financeiro e priorização | 15 | Premissas, faixa, caixa, custo, prazo, ROI sem falsa precisão |
| Plano de implementação e mudança | 15 | Donos, cadência, comunicação, dependências e gatilhos |
| Comunicação executiva e epistemologia | 5 | Decisão clara, incertezas explícitas, sem culpabilização |

Deduzir até 10 pontos por causalidade afirmada sem teste; até 10 por plano sem dono/métrica; até 10 por proposta que ultrapassa orçamento sem decisão/financiamento. Não penalizar hipóteses refutadas se foram testadas com método.
