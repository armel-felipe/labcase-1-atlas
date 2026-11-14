# Memória compartilhada do Case Atlas

Esta pasta guarda o histórico de entrevistas e decisões disponível para todos os consultores do workspace. Cada sessão aprovada vira um arquivo Markdown novo. O assistente só grava depois de mostrar o rascunho ao consultor e receber uma confirmação explícita.

## Arquivos

```text
memoria/
├── README.md
├── INDEX.md
├── estado_atual.md
├── entrevistas/
└── decisoes/
```

O AnythingLLM deve montar esta pasta com leitura e escrita pelo File System Agent. `99_Facilitador/` não fica nesta pasta e não deve ser montada no workspace.

## Modelo da ata

Use um nome novo no formato `AAAA-MM-DD_persona_nome_curto.md`. Nunca sobrescreva uma entrevista existente. Se precisar corrigir algo, crie uma nota complementar e aponte para o registro original.

```markdown
# Entrevista: [nome da persona]

- ID: INT-AAAA-MM-DD-01
- Início: [data e hora, se conhecidas]
- Registro: [data e hora]
- Entrevistador: [nome informado pelo consultor ou “não informado”]
- Entrevistado: [nome e cargo da persona]
- Objetivo: [objetivo declarado]

## Perguntas e respostas
1. **Pergunta:** ...
   **Resposta da persona:** ...

## Síntese
- **Relatos da persona:** declarações atribuídas à pessoa; não são fatos auditados.
- **Fatos documentados citados:** informação e origem do arquivo/seção.
- **Hipóteses discutidas:** explicações ainda não comprovadas.
- **Dados solicitados/liberados:** base, período, campos e resultado; ou “nenhum”.
- **Decisões tomadas:** decisões explícitas; ou “nenhuma”.
- **Pendências e próximos passos:** ação, responsável e prazo, se informados.
```

## Índice e estado do case

Depois de criar uma ata, acrescente uma linha em `INDEX.md` com data, persona, entrevistador, objetivo e nome do arquivo. Não reescreva linhas anteriores.

Atualize `estado_atual.md` somente quando a conversa tiver produzido uma decisão explícita ou mudança de hipótese/pendência. Preserve a data e anote a origem (ID da entrevista); não transforme uma opinião isolada em decisão do grupo.

## Regras de gravação

- Não registre uma sessão sem confirmar com o consultor.
- Se a pessoa não quiser confirmar seu nome, use “não informado”. Não invente identidade a partir do login.
- Não inclua credenciais, informações pessoais reais ou arquivos reservados.
- A sincronização com GitHub é manual e não acontece ao salvar a ata.
- A gravação pelo File System Agent segue as instruções do workspace, mas não tem validação rígida de esquema. O mantenedor revisa o piloto e adiciona validação técnica somente se necessário.
