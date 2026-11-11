#!/usr/bin/env python3
"""Gera o Data Room sintético da Indústria Atlas com seed fixa.

Uso: python3 gerar_data_room.py [--output data_room_seed]
Sem dependências externas. Datas e relacionamentos são reproduzíveis.
"""
from __future__ import annotations
import argparse, csv, random
from collections import defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

SEED = 20261111
R = random.Random(SEED)
OUT_DEFAULT = Path(__file__).resolve().parent / "data_room_seed"
FAMILIES = {"A": [1800,1230], "B": [1100,840], "C": [800,730]}
CAPACITY = {"A":1450, "B":1000, "C":650}
WEEK_START = date(2026,5,4)
DEMAND = [
 {'A': 1020, 'B': 850, 'C': 510},
 {'A': 1050, 'B': 880, 'C': 540},
 {'A': 1010, 'B': 910, 'C': 560},
 {'A': 1080, 'B': 900, 'C': 570},
 {'A': 1060, 'B': 920, 'C': 580},
 {'A': 1100, 'B': 900, 'C': 590},
 {'A': 1090, 'B': 930, 'C': 600},
 {'A': 1080, 'B': 950, 'C': 620},
 {'A': 1080, 'B': 940, 'C': 630},
 {'A': 1100, 'B': 950, 'C': 630},
 {'A': 1120, 'B': 960, 'C': 640},
 {'A': 1110, 'B': 970, 'C': 640},
 {'A': 1100, 'B': 980, 'C': 640},
 {'A': 1120, 'B': 970, 'C': 660},
 {'A': 1120, 'B': 970, 'C': 660},
 {'A': 1120, 'B': 970, 'C': 660},
 {'A': 1120, 'B': 970, 'C': 660},
 {'A': 1120, 'B': 970, 'C': 660},
 {'A': 880, 'B': 800, 'C': 520},
 {'A': 950, 'B': 850, 'C': 550},
 {'A': 990, 'B': 900, 'C': 560},
 {'A': 1010, 'B': 910, 'C': 580},
 {'A': 1050, 'B': 950, 'C': 600},
 {'A': 1060, 'B': 950, 'C': 590},
 {'A': 1100, 'B': 960, 'C': 640},
 {'A': 1120, 'B': 970, 'C': 660}]
PRODUCTION = [2300,2250,2150,2180,2200,2300,2150,2100]
SHIPMENTS = [2200,2180,2150,2140,2180,2240,2100,2060]
OTIF = [88,84,79,74,68,65,60,54]
REVENUE_M = [12.40,11.70,10.90]
VARIABLE_M = [8.70,8.40,8.05]
FIXED_M = [3.00,3.00,3.00]
EXPEDITE_M = [.15,.38,.65]

def write_csv(folder: Path, name: str, rows: list[dict]):
    if not rows: return
    with (folder / name).open("w", newline="", encoding="utf-8-sig") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),extrasaction="ignore"); w.writeheader(); w.writerows(rows)

def split_qty(total:int, n:int, minimum:int=1)->list[int]:
    vals=[minimum]*n
    for _ in range(total-n): vals[R.randrange(n)]+=1
    return vals

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,default=OUT_DEFAULT); a=ap.parse_args()
    out=a.output.resolve(); out.mkdir(parents=True,exist_ok=True)
    # Cadastros compartilhados
    skus=[]
    for fam,count in [("A",8),("B",8),("C",6)]:
        for i in range(1,count+1):
            bom={"A":0.65,"B":0.45,"C":0.60}[fam]
            skus.append({"sku_id":f"SKU-{fam}{i:02d}","familia":fam,"descricao":f"Componente {fam}-{i:02d}","preco_lista":FAMILIES[fam][0],"custo_variavel_ref":FAMILIES[fam][1],"material_principal":f"MAT-{fam}{(i%4)+1:02d}","consumo_ref_kg_por_unidade":bom,"unidade":"un"})
    machines=[{"maquina_id":f"M-{x}","linha":x,"familia_preferencial":fam,"horas_semanais_programadas":80,"capacidade_teorica_semanal":cap,"data_inicio_operacao":"2018-01-01"} for x,fam,cap in [("A1","A",1450),("B1","B",1000),("C1","C",650)]]
    customers=[{"cliente_id":f"CLI-{i:03d}","segmento":["OEM","Distribuidor","Serviços"][i%3],"regiao":["Sudeste","Sul","Centro-Oeste","Nordeste"][i%4],"classe_servico":"A" if i<12 else "B" if i<30 else "C","prazo_pagamento_dias":[28,35,42][i%3]} for i in range(1,41)]
    materials=[]
    for fam in "ABC":
        for j in range(1,5): materials.append({"material_id":f"MAT-{fam}{j:02d}","familia":fam,"descricao":f"Insumo {fam}-{j:02d}","unidade":"kg","custo_unitario":round((18 if fam=="A" else 12 if fam=="B" else 9)*(1+j*.025),2),"fornecedor_id":f"FOR-{j:02d}","estoque_seguranca":300+j*25,"lead_time_contratual_dias":14+j*3})
    write_csv(out,"cadastro_skus.csv",skus); write_csv(out,"cadastro_maquinas.csv",machines); write_csv(out,"cadastro_clientes.csv",customers); write_csv(out,"cadastro_materiais.csv",materials)

    # Pedidos: 26 semanas; os 8 dados do briefing são preservados exatamente.
    orders=[]; line_to_order={}; order_seq=0
    weekly_line_ids=[]
    opening=[]
    for i in range(15):
        qty=40
        line=f"LIN-AB-{i+1:03d}"; oid=f"PED-AB-{i+1:03d}"
        opening.append({"pedido_id":oid,"linha_pedido_id":line,"cliente_id":f"CLI-{i+1:03d}","sku_id":f"SKU-A{(i%8)+1:02d}","data_pedido":"2026-04-20","data_prometida":"2026-05-08","quantidade_pedida":qty,"preco_unitario":1800,"canal":"Carteira inicial","pedido_abertura":"sim"})
        line_to_order[line]={"qty":qty,"shipped":0,"created":date(2026,4,20),"due":date(2026,5,8)}
    orders.extend(opening)
    weekly_demands=[]
    for wi, famqty in enumerate(DEMAND):
        start=WEEK_START+timedelta(days=7*wi); weekly_demands.append(sum(famqty.values()))
        for fam,total in famqty.items():
            n=45
            quantities=split_qty(total,n,minimum=1)
            for k,q in enumerate(quantities):
                order_seq+=1; line=f"LIN-{order_seq:06d}"; oid=f"PED-{order_seq:06d}"
                sku=f"SKU-{fam}{R.randint(1,8 if fam!='C' else 6):02d}"
                cli=R.randint(1,40); promised=start+timedelta(days=R.choice([7,10,14,21]))
                # Pressões comerciais nos últimos dois meses aumentam revisões e datas curtas, sem efeito determinístico.
                rush="sim" if R.random()<(.035+.13*wi/25) else "não"
                row={"pedido_id":oid,"linha_pedido_id":line,"cliente_id":f"CLI-{cli:03d}","sku_id":sku,"data_pedido":start.isoformat(),"data_prometida":promised.isoformat(),"quantidade_pedida":q,"preco_unitario":FAMILIES[fam][0],"canal":"Comercial" if rush=="sim" else "Carteira","pedido_abertura":"não"}
                orders.append(row); line_to_order[line]={"qty":q,"shipped":0,"created":start,"due":promised,"fam":fam,"wi":wi,"rush":rush}
                weekly_line_ids.append((wi,line,q))
    # Log de pedidos de mudança do plano; pedidos não implicam mudança aceita ou executada.
    plan_changes=[]
    for row in orders:
        if row["pedido_abertura"]=="sim": continue
        wi=(date.fromisoformat(row["data_pedido"])-WEEK_START).days//7
        severity=wi/25
        probability=.035+.16*(severity**1.3)
        if R.random()<probability:
            created=date.fromisoformat(row["data_pedido"]); request_date=created+timedelta(days=R.randint(1,5))
            commercial=.36+.14*severity; production=.36-.08*severity
            origin=R.choices(["Comercial","Produção","PCP"],[commercial,production,1-commercial-production])[0]
            reason=R.choices(["Proteção de conta","Recomposição de sequência","Material pendente","Janela de manutenção","Ajuste de qualidade"],[.30,.30,.18,.14,.08])[0]
            base=created+timedelta(days=7); revised=base+timedelta(days=R.choice([-7,-3,3,7]))
            approved="sim" if R.random()<(.74-.07*severity) else "não"
            plan_changes.append({"evento_programacao_id":f"ALT-{len(plan_changes)+1:05d}","linha_pedido_id":row["linha_pedido_id"],"pedido_id":row["pedido_id"],"data_solicitacao":request_date.isoformat(),"origem_solicitacao":origin,"motivo_declarado":reason,"inicio_planejado_original":base.isoformat(),"inicio_planejado_revisado":revised.isoformat(),"decisao":"Aceita" if approved=="sim" else "Recusada","data_decisao":(request_date+timedelta(days=R.randint(0,2))).isoformat()})
    # Expedição semanal controlada para bater o briefing, com aging FIFO e quantidades fracionadas por linha.
    shipments=[]; shipped_by_week=[]; remain=[SHIPMENTS[i] for i in range(8)]
    all_lines=[r["linha_pedido_id"] for r in orders]
    for wi in range(26):
        target=SHIPMENTS[wi-18] if wi>=18 else max(1800,round(weekly_demands[wi]*.90))
        shipped=0; current=WEEK_START+timedelta(days=wi*7+5)
        elig=[l for l in all_lines if line_to_order[l]["created"]<=current and line_to_order[l]["shipped"]<line_to_order[l]["qty"]]
        elig.sort(key=lambda l:(line_to_order[l]["due"],line_to_order[l]["created"],l))
        for line in elig:
            if shipped>=target: break
            state=line_to_order[line]; q=min(state["qty"]-state["shipped"],target-shipped)
            if q<=0: continue
            state["shipped"]+=q; shipped+=q
            shipments.append({"expedicao_id":f"EXP-{len(shipments)+1:06d}","linha_pedido_id":line,"pedido_id":next(r["pedido_id"] for r in orders if r["linha_pedido_id"]==line),"data_expedicao":current.isoformat(),"quantidade_expedida":q,"frete_tipo":"Emergencial" if (current.strftime("%Y-%m") in {"2026-08","2026-09","2026-10"} and R.random()<({"2026-08":.16,"2026-09":.19,"2026-10":.23}[current.strftime("%Y-%m")])) else "Regular","custo_frete":round(q*(2.5 if wi<18 else 3.8),2),"entrega_completa_linha":"sim" if state["shipped"]>=state["qty"] else "não"})
        shipped_by_week.append(shipped)

    # Produção: totais semanais do briefing para semanas 19-26, distribuídos em lotes e linhas.
    production=[]; work_order=0; family_prod=[]
    for wi in range(26):
        if wi>=18: totals=[820,820,460][0:]
        else: totals=[round(weekly_demands[wi]*.40),round(weekly_demands[wi]*.38),round(weekly_demands[wi]*.22)]
        if wi>=18: # perfil de produção deteriorado, soma exata conforme briefing nas últimas oito semanas
            recent=[2300,2250,2150,2180,2200,2300,2150,2100]
            # Mix compatível com capacidades e semana 8 exatamente A820/B820/C460
            if wi==25: totals=[820,820,460]
            else:
                total=recent[wi-18]; totals=[round(total*.40),round(total*.39),total-round(total*.40)-round(total*.39)]
        else:
            total=round(weekly_demands[wi]*(.94-.06*wi/25))
            weights=[.40,.38,.22]
            totals=[round(total*weights[0]),round(total*weights[1]),total-round(total*weights[0])-round(total*weights[1])]
        if wi>=18: totals_sum=[2300,2250,2150,2180,2200,2300,2150,2100][wi-18]; total_now=sum(totals); totals[0]+=totals_sum-total_now
        family_prod.append(totals)
        for fi,fam in enumerate("ABC"):
            # Grão do arquivo: SKU x turno x dia útil (não uma linha por unidade).
            family_skus=[s["sku_id"] for s in skus if s["familia"]==fam]
            cells=[(sku,d,shift) for sku in family_skus for d in range(5) for shift in range(3)]
            qs=split_qty(totals[fi],len(cells))
            for (sku,d,shift),q in zip(cells,qs):
                work_order+=1; machine=f"M-{fam}1"; day=WEEK_START+timedelta(days=wi*7+d); run=round(q/(CAPACITY[fam]/80),2)
                scrap=max(0,round(q*R.uniform(.005,.035)))
                production.append({"ordem_producao_id":f"OP-{work_order:06d}","data_producao":day.isoformat(),"semana_id":f"W{wi+1:02d}","turno":shift+1,"sku_id":sku,"maquina_id":machine,"quantidade_boas":q,"quantidade_refugo":scrap,"horas_programadas":run,"horas_run":run,"setup_horas":0,"prioridade_manual":"sim" if R.random()<(.035+.18*(wi/25)**1.25) else "não"})

    # Paradas e ordens de manutenção; eventos por classe e duração, com mistura de falhas.
    downtime=[]; maint=[]
    for wi in range(26):
        severity=wi/25
        for line in "ABC":
            count=R.randint(2,4)+(1 if R.random()<(.04+.20*severity) else 0)
            for j in range(count):
                dt=WEEK_START+timedelta(days=wi*7+R.randint(0,6)); h=round(R.uniform(.4,2.2)+(max(0,severity-.15)*1.0 if line=="A" else 0),2)
                cat=R.choices(["Elétrica","Mecânica","Ajuste de processo","Setup prolongado","Utilidade"],[.22,.30,.20,.20,.08])[0]
                did=f"PAR-{len(downtime)+1:05d}"; downtime.append({"parada_id":did,"data_inicio":datetime.combine(dt,datetime.min.time()).isoformat(),"maquina_id":f"M-{line}1","tipo":"Não planejada" if cat!="Setup prolongado" else "Setup","categoria_informada":cat,"duracao_horas":h,"ordem_producao_id":"","registrado_por":"Turno"})
                maint.append({"ordem_manutencao_id":f"OM-{len(maint)+1:05d}","parada_id":did,"maquina_id":f"M-{line}1","data_abertura":dt.isoformat(),"tipo_intervencao":"Corretiva" if cat!="Setup prolongado" else "Ajuste","status_execucao":"Executada","horas_execucao":round(h*R.uniform(.65,1.15),2),"custo_pecas":round(R.uniform(300,4200),2),"causa_confirmada":"não classificada"})
        # Preventivas omitidas são registradas como ordens vencidas, não como parada.
        if R.random()<(.07+.45*severity):
            line=R.choice("ABC"); maint.append({"ordem_manutencao_id":f"OM-{len(maint)+1:05d}","parada_id":"","maquina_id":f"M-{line}1","data_abertura":(WEEK_START+timedelta(days=wi*7+2)).isoformat(),"tipo_intervencao":"Preventiva","status_execucao":"Aguardando janela","horas_execucao":0,"custo_pecas":0,"causa_confirmada":"aguardando janela"})

    # Associa apontamentos de parada a uma ordem da mesma semana/máquina quando disponível.
    ops_by_week_machine=defaultdict(list)
    for op_row in production: ops_by_week_machine[(op_row["semana_id"],op_row["maquina_id"])].append(op_row["ordem_producao_id"])
    for stop in downtime:
        stop_day=date.fromisoformat(stop["data_inicio"][:10]); stop_week=(stop_day-WEEK_START).days//7+1
        candidates=ops_by_week_machine.get((f"W{stop_week:02d}",stop["maquina_id"]),[])
        if candidates: stop["ordem_producao_id"]=R.choice(candidates)
    # Cada máquina tem 80 h programadas por semana. Run + setup + parada
    # apontada nunca pode exceder esse teto; o saldo fica como tempo disponível.
    for wi in range(26):
        week=f"W{wi+1:02d}"
        for fam in "ABC":
            machine=f"M-{fam}1"
            rows=[r for r in production if r["semana_id"]==week and r["maquina_id"]==machine]
            stops=[r for r in downtime if r["maquina_id"]==machine and (date.fromisoformat(r["data_inicio"][:10])-WEEK_START).days//7==wi]
            run_total=sum(float(r["horas_run"]) for r in rows); stop_total=sum(float(r["duracao_horas"]) for r in stops)
            if wi<18 and run_total+stop_total>80:
                allowed_units=max(0,int((80.0-stop_total-2.0)*(CAPACITY[fam]/80)))
                actual_units=sum(int(r["quantidade_boas"]) for r in rows); excess=max(0,actual_units-allowed_units)
                for row in sorted(rows,key=lambda x:int(x["quantidade_boas"]),reverse=True):
                    cut=min(excess,int(row["quantidade_boas"]))
                    row["quantidade_boas"]=int(row["quantidade_boas"])-cut; excess-=cut
                    if excess==0: break
                    row["horas_run"]=round(int(row["quantidade_boas"])/(CAPACITY[fam]/80),2)
                for row in rows: row["horas_run"]=round(int(row["quantidade_boas"])/(CAPACITY[fam]/80),2)
                run_total=sum(float(r["horas_run"]) for r in rows)
            setup_total=min(12.0,max(0.0,80.0-run_total-stop_total)*.35)
            weights=[R.uniform(.5,1.5) for _ in rows]; weight_total=sum(weights)
            for row,weight in zip(rows,weights):
                setup=round(setup_total*weight/weight_total,3)
                row["setup_horas"]=setup; row["horas_programadas"]=round(float(row["horas_run"])+setup,3)

    # Materiais: movimentos semanais e compras com lead times variados.
    inventory=[]; purchases=[]; forecasts=[]; logistics=[]
    for mi,mat in enumerate(materials):
        for wi in range(26):
            dt=WEEK_START+timedelta(days=wi*7+2)
            if R.random()<.08:
                qty=R.randint(10,45)
                inventory.append({"movimento_id":f"MOV-{len(inventory)+1:06d}","data_movimento":dt.isoformat(),"material_id":mat["material_id"],"tipo_movimento":"Ajuste","quantidade":R.choice([-qty,qty]),"documento_id":f"AJ-{len(inventory)+1:06d}"})
            if wi%3==0:
                oid=f"OC-{len(purchases)+1:05d}"; order_dt=dt-timedelta(days=R.randint(4,15)); lead=R.randint(9,29)+round(4*wi/25)+R.randint(0,2); receipt=order_dt+timedelta(days=lead)
                received=receipt<=date(2026,11,1)
                lot={"A":R.randint(350,650),"B":R.randint(250,500),"C":R.randint(150,350)}[mat["familia"]]
                purchases.append({"pedido_compra_id":oid,"data_pedido":order_dt.isoformat(),"data_prometida":(order_dt+timedelta(days=mat["lead_time_contratual_dias"])).isoformat(),"data_recebimento":receipt.isoformat() if received else "","fornecedor_id":mat["fornecedor_id"],"material_id":mat["material_id"],"quantidade":lot,"lead_time_real_dias":lead if received else "","status":"Recebido" if received else "Em trânsito","preco_unitario":mat["custo_unitario"]})
    # Consumo por OP e material principal do SKU, com fator de referência explícito no cadastro.
    sku_by_id={r["sku_id"]:r for r in skus}
    for op_row in production:
        sku=sku_by_id[op_row["sku_id"]]; quantity=round(int(op_row["quantidade_boas"])*float(sku["consumo_ref_kg_por_unidade"]),3)
        inventory.append({"movimento_id":f"MOV-{len(inventory)+1:06d}","data_movimento":op_row["data_producao"],"material_id":sku["material_principal"],"tipo_movimento":"Consumo","quantidade":-quantity,"documento_id":op_row["ordem_producao_id"]})
    for po in purchases:
        if po["status"]=="Recebido":
            inventory.append({"movimento_id":f"MOV-{len(inventory)+1:06d}","data_movimento":po["data_recebimento"],"material_id":po["material_id"],"tipo_movimento":"Recebimento","quantidade":po["quantidade"],"documento_id":po["pedido_compra_id"]})
    for wi in range(26):
        for fam in "ABC":
            skus_in_family=[s["sku_id"] for s in skus if s["familia"]==fam]
            for sku in skus_in_family:
                sku_share=DEMAND[wi][fam]/len(skus_in_family)
                for k in range(6):
                    dt=WEEK_START+timedelta(days=wi*7); forecasts.append({"previsao_id":f"PREV-{len(forecasts)+1:06d}","data_emissao":(dt-timedelta(days=28-k*3)).isoformat(),"semana_alvo_inicio":dt.isoformat(),"familia":fam,"sku_id":sku,"versao":"consenso_mensal" if k==0 else f"revisao_{k}","quantidade_prevista":max(1,round(sku_share+R.randint(-28,28)+(round(R.randint(0,22)*(wi/25)) if k>3 else 0))),"responsavel":"PCP" if k%2 else "Comercial"})
    # logística agrupada como comprovantes por expedição com timestamps e modal.
    for s in shipments:
        logistics.append({"expedicao_id":s["expedicao_id"],"transportadora_id":f"TR-{R.randint(1,8):02d}","modal":"Rodoviário","data_coleta":s["data_expedicao"],"data_entrega_cliente":(date.fromisoformat(s["data_expedicao"])+timedelta(days=R.randint(1,4))).isoformat(),"custo_frete":s["custo_frete"],"ocorrencia":"Atraso" if R.random()<.14 else "Sem ocorrência"})
    # Frete emergencial conciliado aos três ciclos gerenciais de quatro semanas.
    periods=[("M-2","2026-08-10","2026-09-06",150000.0),
             ("M-1","2026-09-07","2026-10-04",380000.0),
             ("Atual","2026-10-05","2026-11-01",650000.0)]
    for period,start,end,target in periods:
        group=[s for s in shipments if start<=s["data_expedicao"]<=end and s["frete_tipo"]=="Emergencial"]
        if not group: raise RuntimeError(f"Sem expedições emergenciais em {period}")
        total_weight=sum(max(1,s["quantidade_expedida"]) for s in group); allocated=0
        for j,s in enumerate(group):
            value=round(target*max(1,s["quantidade_expedida"])/total_weight,2) if j<len(group)-1 else round(target-allocated,2)
            s["custo_frete"]=value; allocated+=value
    cost_by_expedition={s["expedicao_id"]:s["custo_frete"] for s in shipments}
    for row in logistics: row["custo_frete"]=cost_by_expedition[row["expedicao_id"]]

    # Controles gerenciais por janela de quatro semanas; não são rollups transacionais.
    finance=[]
    for ix,(period,start,end,_) in enumerate(periods):
        m=REVENUE_M[ix]; v=VARIABLE_M[ix]; fx=FIXED_M[ix]; ex=EXPEDITE_M[ix]
        for cat,val in [("Receita líquida",m),("Custos variáveis",-v),("Margem de contribuição",m-v),("Despesas fixas",-fx),("Fretes emergenciais",-ex),("EBITDA",m-v-fx-ex)]:
            finance.append({"periodo_gerencial":period,"data_inicio":start,"data_fim":end,"conta_gerencial":cat,"valor_reais":f"{val:.2f}","observacao":"frete emergencial destacado dos custos variáveis" if cat=="Fretes emergenciais" else "controle gerencial fictício; não transacional"})
    # Dicionário e catálogo de liberação (nenhum dado é copiado à pasta de consultores nesta geração).
    write_csv(out,"pedidos.csv",orders); write_csv(out,"alteracoes_programacao.csv",plan_changes); write_csv(out,"expedicoes.csv",shipments); write_csv(out,"producao.csv",production); write_csv(out,"paradas.csv",downtime); write_csv(out,"manutencao.csv",maint); write_csv(out,"movimentos_estoque.csv",inventory); write_csv(out,"compras.csv",purchases); write_csv(out,"previsoes.csv",forecasts); write_csv(out,"logistica.csv",logistics); write_csv(out,"financeiro_mensal.csv",finance)
    metrics={"pedidos":len(orders),"alteracoes_programacao":len(plan_changes),"expedicoes":len(shipments),"producao":len(production),"paradas":len(downtime),"manutencao":len(maint),"movimentos":len(inventory),"compras":len(purchases),"previsoes":len(forecasts),"logistica":len(logistics),"cadastros":len(skus)+len(machines)+len(customers)+len(materials)+len(finance)}
    (out/"manifesto.txt").write_text("Atlas Data Room sintético\nSeed: %d\nJanela operacional: 2026-05-04 a 2026-11-01 (26 semanas)\n"%SEED+"\n".join(f"{k}: {v:,}" for k,v in metrics.items())+f"\nTotal aproximado de linhas: {sum(metrics.values()):,}\nGerado localmente; todos os nomes e dados são fictícios.\n",encoding="utf-8")
    print(f"Gerado em {out}; linhas aproximadas: {sum(metrics.values()):,}")

if __name__=="__main__": main()
