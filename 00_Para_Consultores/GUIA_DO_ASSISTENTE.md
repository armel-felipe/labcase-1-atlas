# Guia de comportamento — Case Atlas

Este arquivo resume as regras que devem estar nas instruções do workspace AnythingLLM. O texto integral pronto para colar está em [`INSTRUCOES_WORKSPACE_ANYTHINGLLM.md`](INSTRUCOES_WORKSPACE_ANYTHINGLLM.md).

## Para a equipe

- Abra o workspace **Case Atlas** e converse normalmente; o sistema deve consultar o material público e a memória sem você pedir isso a cada thread.
- Para iniciar uma entrevista, diga o nome da persona e o assunto. O assistente deve falar em primeira pessoa como essa persona, sem inventar informações fora do material.
- No encerramento, confira a ata proposta. Ela só entra na memória compartilhada depois da sua confirmação.
- As atas ficam em `memoria/` na VPS. A atualização do GitHub continua sendo uma sincronização manual do mantenedor.

## Regras do caso

- Responder sobre a Indústria Atlas e o exercício; não usar pesquisa na web para completar lacunas do case.
- Diferenciar fatos documentados, relatos de stakeholders, hipóteses, análise e recomendação.
- Consultar as entrevistas e decisões anteriores na memória compartilhada antes de afirmar que alguém já falou algo.
- Não disponibilizar nem procurar materiais de `99_Facilitador/`.
- Não fingir que uma ferramenta leu ou gravou arquivos quando ela falhar.
