#!/usr/bin/env python3
"""Verifica vínculos, capacidade e âncoras do briefing Atlas."""
import csv, math, sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parent/"data_room_seed"

def read(name):
    with (ROOT/name).open(encoding="utf-8-sig",newline="") as f: return list(csv.DictReader(f))

def check(condition,message):
    if not condition: raise AssertionError(message)

def main():
    files={p.name:read(p.name) for p in ROOT.glob("*.csv")}
    total=sum(map(len,files.values()))
    check(20000<=total<=100000,f"Volume fora da faixa-alvo: {total}")
    def unique(name,key):
        ids=[r[key] for r in files[name]]; check(len(ids)==len(set(ids)),f"Chave duplicada: {name}.{key}"); return set(ids)
    sku_ids=unique("cadastro_skus.csv","sku_id"); machines=unique("cadastro_maquinas.csv","maquina_id")
    clients=unique("cadastro_clientes.csv","cliente_id"); materials=unique("cadastro_materiais.csv","material_id")
    line_ids=unique("pedidos.csv","linha_pedido_id"); exps=unique("expedicoes.csv","expedicao_id")
    op_ids=unique("producao.csv","ordem_producao_id"); po_ids=unique("compras.csv","pedido_compra_id"); stop_ids=unique("paradas.csv","parada_id")
    order_by_line={r["linha_pedido_id"]:r for r in files["pedidos.csv"]}
    sku_by_id={r["sku_id"]:r for r in files["cadastro_skus.csv"]}
    op_by_id={r["ordem_producao_id"]:r for r in files["producao.csv"]}
    po_by_id={r["pedido_compra_id"]:r for r in files["compras.csv"]}
    for r in files["pedidos.csv"]: check(r["sku_id"] in sku_ids and r["cliente_id"] in clients,"Pedido com SKU/cliente sem cadastro")
    for r in files["alteracoes_programacao.csv"]: check(r["linha_pedido_id"] in line_ids,"Alteração de plano sem linha de pedido")
    for r in files["producao.csv"]:
        check(r["sku_id"] in sku_ids and r["maquina_id"] in machines,"Produção com referência inválida")
        check(math.isclose(float(r["horas_programadas"]),float(r["horas_run"])+float(r["setup_horas"]),abs_tol=.002),"Horas programadas não fecham com run + setup")
    for r in files["expedicoes.csv"]: check(r["linha_pedido_id"] in line_ids and r["pedido_id"]==order_by_line[r["linha_pedido_id"]]["pedido_id"],"Expedição sem pedido correspondente")
    for r in files["manutencao.csv"]: check(r["maquina_id"] in machines and (not r["parada_id"] or r["parada_id"] in stop_ids),"Manutenção com referência inválida")
    for r in files["paradas.csv"]: check(r["maquina_id"] in machines and (not r["ordem_producao_id"] or r["ordem_producao_id"] in op_ids),"Parada sem máquina/ordem correspondente")
    receipt_rows=[r for r in files["movimentos_estoque.csv"] if r["tipo_movimento"]=="Recebimento"]
    receipt_by_po={}
    for r in receipt_rows:
        check(r["documento_id"] in po_ids,"Recebimento sem pedido de compra")
        check(r["documento_id"] not in receipt_by_po,"Pedido de compra recebido em duplicidade")
        receipt_by_po[r["documento_id"]]=r
        po=po_by_id[r["documento_id"]]
        check(po["status"]=="Recebido" and r["material_id"]==po["material_id"] and r["data_movimento"]==po["data_recebimento"],"Recebimento diverge da OC (material/data/status)")
        check(math.isclose(float(r["quantidade"]),float(po["quantidade"]),abs_tol=.001),"Quantidade recebida diverge da OC")
    for po in files["compras.csv"]:
        check(po["material_id"] in materials,"Compra com material sem cadastro")
        if po["status"]=="Recebido": check(po["pedido_compra_id"] in receipt_by_po,"OC recebida sem movimento de estoque")
        else: check(po["status"]=="Em trânsito" and not po["data_recebimento"],"Status de compra incoerente")
    for r in files["movimentos_estoque.csv"]:
        check(r["material_id"] in materials,"Movimento com material sem cadastro")
        if r["tipo_movimento"]=="Consumo":
            check(r["documento_id"] in op_ids,"Consumo sem OP")
            op=op_by_id[r["documento_id"]]; product=sku_by_id[op["sku_id"]]
            check(r["material_id"]==product["material_principal"],"Consumo de material não corresponde ao SKU da OP")
            expected=-int(op["quantidade_boas"])*float(product["consumo_ref_kg_por_unidade"])
            check(math.isclose(float(r["quantidade"]),expected,abs_tol=.002),"Consumo não fecha com fator BOM do cadastro")
    for r in files["previsoes.csv"]: check(r["sku_id"] in sku_ids,"Previsão com SKU sem cadastro")
    log={r["expedicao_id"]:r for r in files["logistica.csv"]}
    check(set(log)==exps,"Logística não cobre exatamente as expedições")
    for r in files["expedicoes.csv"]: check(float(log[r["expedicao_id"]]["custo_frete"])==float(r["custo_frete"]),"Frete diverge entre expedição e logística")

    expected_demand=[2200,2350,2450,2500,2600,2600,2700,2750]
    expected_ship=[2200,2180,2150,2140,2180,2240,2100,2060]
    expected_prod=[2300,2250,2150,2180,2200,2300,2150,2100]
    expected_backlog=[600,770,1070,1430,1850,2210,2810,3500]
    demand=defaultdict(int); shipped=defaultdict(int); produced=defaultdict(int); family_prod=defaultdict(int)
    for r in files["pedidos.csv"]:
        if r["pedido_abertura"]=="não": demand[r["data_pedido"]]+=int(r["quantidade_pedida"])
    for r in files["expedicoes.csv"]: shipped[r["data_expedicao"]]+=int(r["quantidade_expedida"])
    for r in files["producao.csv"]:
        produced[r["semana_id"]]+=int(r["quantidade_boas"])
        if r["semana_id"]=="W26": family_prod[sku_by_id[r["sku_id"]]["familia"]]+=int(r["quantidade_boas"])
    backlog=600
    for i in range(8):
        start=(date(2026,9,7)+timedelta(days=7*i)).isoformat(); ship_day=(date.fromisoformat(start)+timedelta(days=5)).isoformat(); week=f"W{i+19:02d}"
        actual_demand=demand[start]; actual_ship=shipped[ship_day]; actual_prod=produced[week]
        check(actual_demand==expected_demand[i],f"Demanda S{i+1}: {actual_demand} != {expected_demand[i]}")
        check(actual_ship==expected_ship[i],f"Expedição S{i+1}: {actual_ship} != {expected_ship[i]}")
        check(actual_prod==expected_prod[i],f"Produção S{i+1}: {actual_prod} != {expected_prod[i]}")
        backlog+=actual_demand-actual_ship
        check(backlog==expected_backlog[i],f"Backlog S{i+1}: {backlog} != {expected_backlog[i]}")
    check(sum(int(r["quantidade_pedida"]) for r in files["pedidos.csv"] if r["pedido_abertura"]=="sim")==600,"Carteira inicial não soma 600")
    check(family_prod=={"A":820,"B":820,"C":460},f"Mix de produção W26 divergente: {family_prod}")
    demand_s8={fam:0 for fam in "ABC"}
    for r in files["pedidos.csv"]:
        if r["data_pedido"]=="2026-10-26" and r["pedido_abertura"]=="não": demand_s8[sku_by_id[r["sku_id"]]["familia"]]+=int(r["quantidade_pedida"])
    check(demand_s8=={"A":1120,"B":970,"C":660},f"Demanda por família S8 diverge: {demand_s8}")

    stops_by_week_machine=defaultdict(float); scheduled=defaultdict(float)
    for r in files["paradas.csv"]:
        wi=(date.fromisoformat(r["data_inicio"][:10])-date(2026,5,4)).days//7+1
        stops_by_week_machine[(f"W{wi:02d}",r["maquina_id"])]+=float(r["duracao_horas"])
    for r in files["producao.csv"]: scheduled[(r["semana_id"],r["maquina_id"])]+=float(r["horas_programadas"])
    for key,hours in scheduled.items(): check(hours+stops_by_week_machine[key]<=80.02,f"Horas run/setup + parada excedem 80 h em {key}")

    finance=defaultdict(dict)
    for r in files["financeiro_mensal.csv"]: finance[r["periodo_gerencial"]][r["conta_gerencial"]]=round(float(r["valor_reais"]),2)
    periods={"M-2":("2026-08-10","2026-09-06"),"M-1":("2026-09-07","2026-10-04"),"Atual":("2026-10-05","2026-11-01")}
    for period,values in finance.items():
        check(round(values["Receita líquida"]+values["Custos variáveis"]+values["Despesas fixas"]+values["Fretes emergenciais"],2)==values["EBITDA"],f"EBITDA não fecha em {period}")
        check(period in periods,"Período financeiro desconhecido")
        start,end=periods[period]
        rows=[r for r in files["financeiro_mensal.csv"] if r["periodo_gerencial"]==period]
        check(all(r["data_inicio"]==start and r["data_fim"]==end for r in rows),f"Datas inconsistentes em {period}")
        freight=sum(float(r["custo_frete"]) for r in files["expedicoes.csv"] if start<=r["data_expedicao"]<=end and r["frete_tipo"]=="Emergencial")
        check(round(freight,2)==round(-values["Fretes emergenciais"]*1_000_000,2),f"Frete emergencial não concilia em {period}: {freight}")
    check([finance[m]["EBITDA"] for m in ("M-2","M-1","Atual")]==[.55,-.08,-.8],"Âncoras EBITDA divergentes")
    print(f"OK: {total:,} linhas em {len(files)} CSVs; demanda, produção, expedição e backlog S1-S8; horas, compras, estoque e DRE conferidos.")

if __name__=="__main__":
    try: main()
    except Exception as exc: print(f"FALHA: {exc}",file=sys.stderr); sys.exit(1)
