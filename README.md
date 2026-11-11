# Projeto local — Laboratório de Consultoria

Este é o pacote completo do **Caso 001: Indústria Atlas**. Os materiais estão divididos em duas áreas:

- [`00_Para_Consultores/`](00_Para_Consultores/) contém o briefing, entrevistas iniciais e instruções próprias para os participantes.
- [`99_Facilitador/`](99_Facilitador/) contém o gabarito, o protocolo de facilitação, os scripts de geração/verificação e todos os dados sintéticos preparados.

## Para abrir e vincular ao Work

Abra esta pasta no Mac para revisar o pacote. Para conduzir o exercício com consultores no Work, selecione **somente** a subpasta `00_Para_Consultores` no fluxo de escolha de pasta local do Work. Não vincule a pasta do projeto inteira nem `99_Facilitador` à sessão dos participantes.

Diretórios separados não são uma barreira de segurança. Se os participantes conseguirem ler a pasta-pai, o mesmo usuário do Mac ou uma cópia dos dados, podem encontrar o gabarito. Controle de acesso real exigiria permissões e armazenamento fora do alcance deles.

## Dados

O Data Room já foi materializado em `99_Facilitador/data_room_seed/`. O total gerado está no `manifesto.txt`. Para reproduzir os mesmos arquivos, rode:

```sh
python3 99_Facilitador/gerar_data_room.py
python3 99_Facilitador/verificar_data_room.py
```

O gerador não exige pacotes de terceiros e usa a seed fixa `20261111`. O verificador confere volume, chaves, referências cruzadas, quantidades das oito semanas do briefing, mix da semana 8, backlog semanal, capacidade-horas, vínculos de recebimento/consumo, expedições e fechamento financeiro em três ciclos de quatro semanas. Não copie os CSVs para a pasta dos consultores até decidir qual pacote liberar.

## Condução recomendada

Leia `99_Facilitador/guia_facilitador.md` e `99_Facilitador/protocolo_e_log.md` antes de iniciar. Mantenha um único log de continuidade e atualize após cada pedido de dados, entrevista, decisão e evento. O ChatGPT pode não conservar estado entre sessões; o log e os fatos imutáveis do caso devem ser reapresentados quando a conversa mudar.
