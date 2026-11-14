"""Closed source catalog used by the release exporter."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Source:
    columns: tuple[str, ...]
    date_column: str | None = None


CATALOG: dict[str, Source] = {
    "alteracoes_programacao.csv": Source(("evento_programacao_id", "linha_pedido_id", "pedido_id", "data_solicitacao", "origem_solicitacao", "motivo_declarado", "inicio_planejado_original", "inicio_planejado_revisado", "decisao", "data_decisao"), "data_solicitacao"),
    "cadastro_clientes.csv": Source(("cliente_id", "segmento", "regiao", "classe_servico", "prazo_pagamento_dias")),
    "cadastro_maquinas.csv": Source(("maquina_id", "linha", "familia_preferencial", "horas_semanais_programadas", "capacidade_teorica_semanal", "data_inicio_operacao")),
    "cadastro_materiais.csv": Source(("material_id", "familia", "descricao", "unidade", "custo_unitario", "fornecedor_id", "estoque_seguranca", "lead_time_contratual_dias")),
    "cadastro_skus.csv": Source(("sku_id", "familia", "descricao", "preco_lista", "custo_variavel_ref", "material_principal", "consumo_ref_kg_por_unidade", "unidade")),
    "compras.csv": Source(("pedido_compra_id", "data_pedido", "data_prometida", "data_recebimento", "fornecedor_id", "material_id", "quantidade", "lead_time_real_dias", "status", "preco_unitario"), "data_pedido"),
    "expedicoes.csv": Source(("expedicao_id", "linha_pedido_id", "pedido_id", "data_expedicao", "quantidade_expedida", "frete_tipo", "custo_frete", "entrega_completa_linha"), "data_expedicao"),
    "financeiro_mensal.csv": Source(("periodo_gerencial", "data_inicio", "data_fim", "conta_gerencial", "valor_reais", "observacao"), "data_inicio"),
    "logistica.csv": Source(("expedicao_id", "transportadora_id", "modal", "data_coleta", "data_entrega_cliente", "custo_frete", "ocorrencia"), "data_coleta"),
    "manutencao.csv": Source(("ordem_manutencao_id", "parada_id", "maquina_id", "data_abertura", "tipo_intervencao", "status_execucao", "horas_execucao", "custo_pecas", "causa_confirmada"), "data_abertura"),
    "movimentos_estoque.csv": Source(("movimento_id", "data_movimento", "material_id", "tipo_movimento", "quantidade", "documento_id"), "data_movimento"),
    "paradas.csv": Source(("parada_id", "data_inicio", "maquina_id", "tipo", "categoria_informada", "duracao_horas", "ordem_producao_id", "registrado_por"), "data_inicio"),
    "pedidos.csv": Source(("pedido_id", "linha_pedido_id", "cliente_id", "sku_id", "data_pedido", "data_prometida", "quantidade_pedida", "preco_unitario", "canal", "pedido_abertura"), "data_pedido"),
    "previsoes.csv": Source(("previsao_id", "data_emissao", "semana_alvo_inicio", "familia", "sku_id", "versao", "quantidade_prevista", "responsavel"), "data_emissao"),
    "producao.csv": Source(("ordem_producao_id", "data_producao", "semana_id", "turno", "sku_id", "maquina_id", "quantidade_boas", "quantidade_refugo", "horas_programadas", "horas_run", "setup_horas", "prioridade_manual"), "data_producao"),
}
