# Instalação rápida — Case Atlas no AnythingLLM

## Situação atual

O AnythingLLM já consegue ler os arquivos dos consultores:

`/opt/agent-projects/case_lab/00_Para_Consultores` → `/app/server/storage/anythingllm-fs/case_lab` (somente leitura)

Vamos deixar isso como está e acrescentar apenas a pasta compartilhada de memória:

`/opt/agent-projects/case_lab/memoria` → `/app/server/storage/anythingllm-fs/memoria` (leitura e escrita)

O Compose está em `/docker/anythingllm-ykt4/docker-compose.yml`; o serviço chama-se `anythingllm`; o usuário do container é `1000:1000`. O modo multiusuário já está ativo e o modelo informado é Gemma 4:31B. Não vamos instalar outros serviços, alterar o mount existente nem mexer no modo multiusuário.

## 1. Preparar a alteração

No terminal da VPS, copie e cole este bloco inteiro. Ele faz uma cópia do Compose, cria as pastas de memória, dá acesso ao usuário do AnythingLLM e acrescenta o mount novo **sem duplicá-lo caso já exista**. No final, valida o Compose, mas ainda não reinicia o AnythingLLM.

```bash
set -e
compose_file=/docker/anythingllm-ykt4/docker-compose.yml
backup_file="${compose_file}.bak-case-atlas-$(date +%Y%m%d-%H%M%S)"
cp -a "$compose_file" "$backup_file"
mkdir -p /opt/agent-projects/case_lab/memoria/entrevistas /opt/agent-projects/case_lab/memoria/decisoes
chown -R 1000:1000 /opt/agent-projects/case_lab/memoria
memory_mount='/opt/agent-projects/case_lab/memoria:/app/server/storage/anythingllm-fs/memoria:rw'
if ! grep -qF "$memory_mount" "$compose_file"; then
  sed -i '/00_Para_Consultores/a\      - /opt/agent-projects/case_lab/memoria:/app/server/storage/anythingllm-fs/memoria:rw' "$compose_file"
fi
docker compose -f "$compose_file" config --quiet
echo "Configuração válida. Backup salvo em: $backup_file"
```

Se houver uma mensagem de erro, pare e me envie a mensagem. Não rode o próximo comando até o primeiro terminar sem erro.

## 2. Aplicar o mount

Depois que o passo 1 disser **“Configuração válida”**, copie e cole:

```bash
docker compose -f /docker/anythingllm-ykt4/docker-compose.yml up -d --no-deps --force-recreate anythingllm
```

Esse comando recria somente o serviço AnythingLLM. Os outros containers não são recriados.

## 3. Confirmar os dois mounts

Copie e cole:

```bash
docker inspect anythingllm-ykt4-anythingllm-1 --format='{{range .Mounts}}{{printf "%s -> %s (rw=%v)\n" .Source .Destination .RW}}{{end}}'
```

Na saída, confirme estas duas linhas:

```text
/opt/agent-projects/case_lab/00_Para_Consultores -> /app/server/storage/anythingllm-fs/case_lab (rw=false)
/opt/agent-projects/case_lab/memoria -> /app/server/storage/anythingllm-fs/memoria (rw=true)
```

`99_Facilitador` continua fora do AnythingLLM.

## 4. Configurar e testar no AnythingLLM

Na interface:

1. Abra o workspace **Case Atlas**.
2. Em **Chat Settings**, selecione **Agent Mode**.
3. Em **Agent Skills**, habilite **File System Agent**.
4. Permita leitura da pasta `/app/server/storage/anythingllm-fs/case_lab`.
5. Permita leitura e escrita da pasta `/app/server/storage/anythingllm-fs/memoria`.
6. Cole as instruções de [`00_Para_Consultores/INSTRUCOES_WORKSPACE_ANYTHINGLLM.md`](00_Para_Consultores/INSTRUCOES_WORKSPACE_ANYTHINGLLM.md) nas instruções do workspace.
7. Escreva: “Quero entrevistar Ana Paiva sobre os atrasos de produção.”

O assistente deve consultar o material, conduzir a entrevista como a persona e, ao final, oferecer uma ata. Confirme a gravação e verifique se surgiu um Markdown em `/opt/agent-projects/case_lab/memoria/entrevistas/`. Esse teste também confirma se o Gemma 4:31B consegue acionar as ferramentas sem exigir `@agent`.

A sincronização para o GitHub continua manual. Em 13/11/2026, o conteúdo de `00_Para_Consultores/` e a estrutura inicial de `memoria/` foram copiados deste checkout para `/opt/agent-projects/case_lab/`. O mount está aplicado; faltam os passos de configuração na interface e o piloto descritos no item 4.
