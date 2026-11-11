# Dicionário e modelo de dados — Atlas

Todos os dados são sintéticos. Janela operacional: 4/5/2026 a 1/11/2026; pedidos da carteira de abertura foram criados em 20/4 para representar as 600 unidades iniciais. IDs são estáveis dentro de uma execução; datas ISO `AAAA-MM-DD`; quantidades em unidades salvo indicação. Seed `20261111` torna a geração reproduzível.

## Arquivos e campos

| Arquivo | Grão | Chave(s) e campos principais |
|---|---|---|
| `cadastro_skus.csv` | Uma linha por SKU | `sku_id` (PK), `familia`, preço e custo variável de referência, `material_principal`, consumo de referência em kg/unidade |
| `cadastro_maquinas.csv` | Uma linha por máquina | `maquina_id` (PK), `linha`, família preferencial, capacidade teórica e horas programadas/semana |
| `cadastro_clientes.csv` | Um cliente | `cliente_id` (PK), segmento, região, classe de serviço, prazo de pagamento |
| `cadastro_materiais.csv` | Um material | `material_id` (PK), família, custo, fornecedor, estoque de segurança, lead time contratual |
| `pedidos.csv` | Uma linha de pedido | `linha_pedido_id` (PK), `pedido_id`, `cliente_id`, `sku_id`, pedido/promessa, quantidade, preço e canal. `pedido_abertura=sim` identifica as 600 unidades iniciais; exclua essas linhas do cálculo de novos pedidos. |
| `alteracoes_programacao.csv` | Um pedido de mudança solicitado | `evento_programacao_id` (PK), `linha_pedido_id`, origem, motivo, datas do plano original/revisado e decisão. Solicitação não significa aceitação nem execução. |
| `producao.csv` | SKU × dia útil × turno | `ordem_producao_id` (PK), data, semana (`W01`–`W26`), turno, `sku_id`, máquina, boas, refugo, horas programadas/run, setup e indicador de prioridade manual. A quantidade boa por semana bate com o resumo, mas o detalhe diário/turno é sintético. |
| `paradas.csv` | Um evento apontado | `parada_id` (PK), máquina, ordem de produção associada na mesma semana, tipo, categoria informada, duração e origem do registro. Categoria é a descrição registrada, não causa-raiz validada. |
| `manutencao.csv` | Uma ordem/intervenção | `ordem_manutencao_id` (PK), `parada_id` (pode estar vazio para preventiva pendente), máquina, tipo, status de execução, horas e custo de peças. Preventiva pendente usa `Aguardando janela`; ação corretiva/ajuste realizada usa `Executada`. `causa_confirmada` não é uma conclusão técnica. |
| `movimentos_estoque.csv` | Um movimento | `movimento_id` (PK), data, material, tipo, quantidade com sinal (consumo negativo), `documento_id` ligado a OP ou OC. Consumo da OP usa o material principal e o fator kg/unidade do cadastro; recebimento concilia data e quantidade com a OC. |
| `compras.csv` | Uma ordem de compra | `pedido_compra_id` (PK), datas do pedido/promessa/recebimento, fornecedor/material, quantidade, lead time real, preço e status. Compras recebidas têm movimento de estoque conciliado; as ainda em trânsito não têm data de recebimento. |
| `previsoes.csv` | SKU × semana-alvo × versão | `previsao_id` (PK), emissão, semana, SKU/família, versão, quantidade e responsável. O nome da versão é um rótulo sintético; defina baseline antes de calcular erro. |
| `expedicoes.csv` | Uma parcela expedida de linha de pedido | `expedicao_id` (PK), `linha_pedido_id`, pedido, data, quantidade, tipo e custo de frete. Linhas podem ter expedição parcial. |
| `logistica.csv` | Um comprovante por expedição | `expedicao_id` (PK/FK), transportadora, modal, coleta, entrega, custo e ocorrência. O custo concilia por expedição com `expedicoes.csv`. |
| `financeiro_mensal.csv` | Conta gerencial × ciclo de quatro semanas | `periodo_gerencial`, `data_inicio`, `data_fim`, conta, valor em reais, observação. Ciclos M-2 (10/8–6/9), M-1 (7/9–4/10) e Atual (5/10–1/11); EBITDA = receita + custos variáveis + despesas fixas + frete emergencial. Frete emergencial concilia com lançamentos de expedição marcados como emergenciais no ciclo. |

## Relacionamentos

```text
clientes 1 ── N pedidos N ── 1 SKUs
pedidos 1 ── N alterações de programação
pedidos/linhas 1 ── N expedições 1 ── 1 logistica
SKUs 1 ── N produção N ── 1 máquinas
paradas N ── 1 máquinas; paradas N ── 1 ordem de produção (quando preenchida)
manutenção N ── 1 máquinas; manutenção N ── 0..1 parada
materiais 1 ── N compras; materiais 1 ── N movimentos de estoque
previsões N ── 1 SKU; movimentos N ── 0..1 OP/OC via documento_id
```

## Limites de interpretação

- A única série em nível de serviço fornecida no briefing é o OTIF semanal agregado. Os registros sintéticos de logística não incluem uma coluna confiável de completude do pedido e não devem ser usados para recalcular OTIF.
- `data_entrega_cliente` e ocorrências logísticas são dados simulados. O custo por expedição concilia ao resumo de fretes; preço e custo variável por SKU são referências, não uma DRE transacional completa. Receita líquida e custos variáveis são controles gerenciais sintéticos e não se reconciliam exatamente a quantidade expedida × preço/custo de referência; não há notas fiscais, descontos, devoluções nem regras de reconhecimento para essa ponte.
- A alteração registrada pode ser recusada; não a conte como mudança realizada sem condição adicional. Compare com `prioridade_manual`, data, máquina e entrevista.
- O saldo físico de estoque não é uma série diária de snapshots: os movimentos e a BOM de referência permitem calcular consumo e recebimentos, mas não reconstituir saldo por endereço nem declarar que toda parada foi por falta de material.
- Capacidades de cadastro são nominais. Não somem tempos de forma a inferir capacidade recuperável sem validar calendários e sobreposições.
