# Catálogo de dados sob solicitação

O facilitador preparou um Data Room de seis meses, 4 de maio a 1º de novembro de 2026, com dados sintéticos e chaves relacionais. **Os CSVs não estão liberados nesta pasta.** Solicitem apenas o pacote necessário, com período, objetivo e campos; o facilitador pode liberar o arquivo completo, um recorte, uma extração parcial ou pedir melhor delimitação.

| Arquivo | Conteúdo | Chaves e usos comuns |
|---|---|---|
| `pedidos.csv` | Pedido, item, cliente, SKU, quantidade, data prometida e canal | `pedido_id`, `linha_pedido_id`, `cliente_id`, `sku_id`; carteira e aging |
| `alteracoes_programacao.csv` | Solicitações de mudança do plano, origem, motivo, revisão proposta e decisão | `evento_programacao_id`, `linha_pedido_id`; solicitado não quer dizer executado |
| `producao.csv` | Produção boa/refugo por SKU, turno, máquina e semana | `ordem_producao_id`, `sku_id`, `maquina_id`; produtividade e mix |
| `expedicoes.csv` | Quantidade expedida por item de pedido, data e tipo de frete | `expedicao_id`, `linha_pedido_id`, `pedido_id`; backlog e serviço |
| `logistica.csv` | Coleta, entrega, transportadora, ocorrência e frete | `expedicao_id`; prazo e custo de transporte |
| `paradas.csv` | Evento, duração, equipamento e categoria apontada | `parada_id`, `maquina_id`; disponibilidade e qualidade do apontamento |
| `manutencao.csv` | Intervenções corretivas/preventivas, duração e peças | `ordem_manutencao_id`, `parada_id`, `maquina_id`; execução e backlog |
| `movimentos_estoque.csv` | Consumos, recebimentos e ajustes de materiais | `movimento_id`, `material_id`, `documento_id`; fluxo e rastreabilidade |
| `compras.csv` | Fornecedor, datas prometida/recebida, quantidade e custo | `pedido_compra_id`, `material_id`; lead time |
| `previsoes.csv` | Versões por SKU e semana-alvo | `previsao_id`, `sku_id`; erro e revisões |
| `financeiro_mensal.csv` | Resumo gerencial em três ciclos de quatro semanas (10/8 a 1/11) | `periodo_gerencial`, `data_inicio`, `data_fim`, `conta_gerencial`; DRE e conciliação |
| `cadastro_skus.csv` | Família, descrição, preço e custo variável de referência | `sku_id`; dimensão de produto |
| `cadastro_maquinas.csv` | Linha, capacidade nominal e horário programado | `maquina_id`; dimensão de ativo |
| `cadastro_clientes.csv` | Segmento, região, classe e prazo de pagamento | `cliente_id`; dimensão de conta |
| `cadastro_materiais.csv` | Material, custo, fornecedor e parâmetro de compra | `material_id`; dimensão de suprimento |

## Como pedir

No Work, usem uma requisição específica, por exemplo:

> Liberar `pedidos.csv`, `expedicoes.csv` e `cadastro_clientes.csv` de 7/9 a 1/11. Objetivo: medir backlog por idade, cliente e completude. Precisamos dos IDs, datas prometidas e efetivas, quantidades e tipo de frete. Favor entregar os dados sem diagnóstico ou interpretação.

Registrem a solicitação e o que foi recebido. Os dados foram materializados antes do início do exercício, mas a liberação acontece sob demanda. Pasta separada não é segredo técnico: quem puder ler a máquina/pasta-pai pode encontrar os arquivos.
