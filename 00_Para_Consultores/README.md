# Laboratório de Consultoria — Caso 001

## Indústria Atlas

Vocês são a equipe de consultoria chamada para diagnosticar uma fabricante fictícia de componentes para refrigeração industrial. O cliente relata piora das entregas, fretes emergenciais, falhas em máquinas, custos crescentes e pressão de caixa. As causas ainda precisam ser investigadas.

Comecem por [`index.html`](index.html), com o briefing executivo, os indicadores e a primeira missão. O roteiro está em [`briefing_inicial.md`](briefing_inicial.md), os relatos iniciais em [`entrevistas_iniciais.md`](entrevistas_iniciais.md), as personas em [`MAPA_DE_PERSONAS.md`](MAPA_DE_PERSONAS.md) e o catálogo de dados em [`data_room/README.md`](data_room/README.md).

## Como trabalhar no AnythingLLM

Use o workspace **Case Atlas** e converse naturalmente, por exemplo: “Quero entrevistar Ana Paiva sobre os atrasos de produção.” O contexto e as regras devem estar configurados no workspace; não é necessário pedir ao assistente que leia cada arquivo. Ao encerrar, revise a ata e confirme se deseja gravá-la na memória compartilhada.

As instruções usadas pelo workspace estão em [`INSTRUCOES_WORKSPACE_ANYTHINGLLM.md`](INSTRUCOES_WORKSPACE_ANYTHINGLLM.md). O fluxo de configuração fica em [`../CONFIGURAR_ANYTHINGLLM.md`](../CONFIGURAR_ANYTHINGLLM.md).

## Primeira entrega

Em até 72 horas simuladas, preparem uma página com: problema de negócio; sintomas versus hipóteses; evidências disponíveis e ainda necessárias; pedidos de dados priorizados; ação emergencial reversível; plano de trabalho e responsáveis. Não tratem depoimentos como fatos comprovados. Cada afirmação causal precisa de evidência ou deve permanecer explicitamente como hipótese.

## Limite de acesso

Dados e gabarito foram preparados fora desta pasta. A configuração do AnythingLLM deve montar esta pasta como fonte de leitura e a pasta `memoria/` como local compartilhado de leitura/escrita. `99_Facilitador/` deve ficar fora dos mounts e fora dos arquivos adicionados ao workspace.

Tudo neste case é sintético. Pessoas, empresa, clientes, fornecedores e registros não correspondem a uma organização real.
