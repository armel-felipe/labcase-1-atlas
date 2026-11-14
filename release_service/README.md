# Case Atlas Release Service

Serviço para registrar pedidos e disponibilizar cópias autorizadas dos CSVs. O custom skill carrega apenas a política geral e o perfil da persona escolhida; o modelo do workspace executa avaliações separadas do facilitador e do stakeholder. O serviço exige que ambos permitam o escopo, aplica a interseção de dados e nunca altera os arquivos originais.

## Estado

O backend e o custom skill estão instalados e ativos na VPS. O skill lê `workspace.name`, `user_id` e `trackedChatId` do contexto interno do AnythingLLM 1.19.0; esses metadados não são argumentos do modelo. A documentação pública não promete esses campos, então falta validar uma invocação real e repetir esse teste após atualizações do AnythingLLM. Sem workspace, usuário ou chat no contexto, o skill falha fechado.

Para julgar um pedido novo, o skill busca no serviço a política geral e somente o perfil da persona selecionada. O texto da política/perfil e as últimas 12 mensagens do chat são enviados ao modelo configurado no workspace para duas avaliações separadas. O CSV original e suas linhas não são enviados ao modelo. O serviço recebe apenas a requisição estruturada e as decisões finais.

No ambiente verificado, o provider do AnythingLLM é `generic-openai` com endpoint `router.hostinger.com`. Assim, a política/perfil selecionados e as últimas 12 mensagens usadas na negociação passam por esse provider durante as duas avaliações. O CSV original e suas linhas não são enviados ao modelo. Essa transferência foi autorizada para a ativação atual.

O Caddy publica a rota de download com autenticação Basic individual e encaminha o token interno esperado pelo serviço. O contêiner do serviço não publica porta no host; executado fora do Compose, o servidor escuta em `127.0.0.1` por padrão.

## Executar localmente

Requer Python 3.12; usa somente a biblioteca padrão.

```bash
export CASE_RELEASE_SOURCE_DIR=/opt/agent-projects/case_lab/99_Facilitador/data_room_seed
export CASE_RELEASE_STORAGE_DIR=/opt/agent-projects/case_lab/case_release_storage
export CASE_RELEASE_API_TOKEN='<segredo aleatório com pelo menos 32 caracteres>'
export CASE_RELEASE_DOWNLOAD_TOKEN='<outro segredo aleatório com pelo menos 32 caracteres>'
export CASE_RELEASE_HOST=127.0.0.1
export CASE_RELEASE_PORT=8091
python3 -m release_service
```

Mantenha `CASE_RELEASE_STORAGE_DIR` fora do Git e faça backup de `releases.sqlite3` e `artifacts/` juntos. O mount de `99_Facilitador/data_room_seed` no processo/contêiner do serviço deve ser somente leitura. Nunca monte `99_Facilitador/` no AnythingLLM dos consultores.

Gere os dois segredos fora do repositório, por exemplo com `python3 -c 'import secrets; print(secrets.token_urlsafe(48))'`. Não reutilize o token de API do AnythingLLM.

## Container preparado para a VPS

[`compose.release.yml`](../compose.release.yml) conecta o serviço às redes Docker `anythingllm-ykt4_default` e `casa-girassois_default`, sem publicar porta no host. O diretório reservado entra somente em leitura; banco e artefatos ficam em armazenamento persistente fora do Git. O serviço está ativo na VPS como `case_lab-case-release-1`.

Os segredos ficam em `.env` (ignorado pelo Git, modo `0600`), e o diretório persistente pertence ao UID/GID `10001`. Para reconstruir após uma mudança de código, use `docker compose -f compose.release.yml up -d --build`. O skill chama `http://case-release:8091` pela rede do AnythingLLM; Caddy alcança o mesmo alias pela rede dele.

O skill está instalado em `/app/server/storage/plugins/agent-skills/case-atlas-release/` no contêiner AnythingLLM, ativo e configurado com `CASE_RELEASE_SERVICE_URL`, `CASE_RELEASE_API_TOKEN` e `CASE_RELEASE_DOWNLOAD_BASE_URL`. O token de API é usado apenas entre contêineres; não aparece no link entregue ao consultor. O `CASE_RELEASE_DOWNLOAD_TOKEN` fica somente no serviço e no Caddy. O formato do runtime de identidade/chat é interno à versão 1.19.0; valide uma invocação real após atualizações do AnythingLLM.

## API privada

Envie `Authorization: Bearer $CASE_RELEASE_API_TOKEN` para criar pedidos, enviar decisões e consultar registros. Todas as mudanças são autenticadas; o token não deve aparecer no navegador, no link de download, nem em arquivos versionados.

Criar um pedido:

```http
POST /v1/requests
Content-Type: application/json
Authorization: Bearer <token>

{
  "origin_thread_id": "<referência confiável fornecida pelo adaptador>",
  "requester_id": "<identidade autenticada fornecida pelo adaptador>",
  "workspace": "Case Atlas",
  "file": "pedidos.csv",
  "purpose": "investigar atraso por semana",
  "safeguards": "somente campos necessários ao recorte",
  "columns": ["pedido_id", "data_pedido", "quantidade_pedida"],
  "date_from": "2026-08-01",
  "date_to": "2026-10-31"
}
```

O catálogo limita o arquivo e as colunas. Filtros de período usam o campo de data definido no catálogo; filtros por valores de linha, SQL, campos desconhecidos e caminhos fornecidos pelo modelo não são aceitos. Se a finalidade depender de outro filtro, a avaliação deve pedir esclarecimento. O serviço intersecta o pedido com os escopos propostos pelo facilitador e pelo stakeholder e rejeita propriedades de escopo não suportadas. Recusa, esclarecimento, conflito ou escopo vazio não geram arquivo. `requester_id` e `origin_thread_id` só têm valor de auditoria confiável quando vierem do adaptador autenticado; não os preencha com texto inferido pelo modelo.

Enviar decisão:

```http
POST /v1/requests/<request_id>/decision
Authorization: Bearer <token>
Content-Type: application/json

{
  "facilitator": {
    "outcome": "partial",
    "reason": "O período completo mistura ciclos não comparáveis.",
    "scope": {
      "file": "pedidos.csv",
      "columns": ["pedido_id", "data_pedido", "quantidade_pedida"],
      "date_from": "2026-09-01",
      "date_to": "2026-10-31"
    }
  },
  "stakeholder": {
    "outcome": "partial",
    "reason": "Aceito o recorte recente para essa análise.",
    "scope": {
      "file": "pedidos.csv",
      "columns": ["pedido_id", "data_pedido", "quantidade_pedida"],
      "date_from": "2026-09-01",
      "date_to": "2026-10-31"
    }
  }
}
```

Uma liberação bem-sucedida retorna `release_id`, escopo, hashes e número de linhas. O endereço de download é estável: `https://llm.armelfelipe.com.br/v1/releases/<release_id>/download`. Pedidos com o mesmo propósito, escopo, salvaguardas e hash atual da fonte reutilizam o artefato ativo; um escopo mais restrito pode gerar uma cópia derivada do mesmo snapshot da fonte nessas mesmas condições. Se as salvaguardas ou a fonte mudarem, ou se o pedido for mais amplo ou tiver outra finalidade, haverá nova negociação. As liberações antigas mantêm seus próprios snapshots e permanecem disponíveis até revogação explícita.

## Fronteira de download no Caddy

O endpoint de download exige `X-Case-Atlas-Gateway-Token`, além do login individual da equipe feito pelo Caddy. O trecho ativo separa a rota de download do proxy do AnythingLLM:

```caddyfile
@case_release_download path_regexp release ^/v1/releases/[a-f0-9]{32}/download$
handle @case_release_download {
	basic_auth argon2id {
		<consultor> <hash-argon2id-individual>
	}
	reverse_proxy case-release:8091 {
		header_up X-Case-Atlas-Gateway-Token {$CASE_RELEASE_DOWNLOAD_TOKEN}
	}
}
```

`CASE_RELEASE_DOWNLOAD_TOKEN` está no ambiente do contêiner Caddy. O Caddy exige credencial Basic individual para cada conta ativa do AnythingLLM; os hashes Argon2id ficam em `/etc/caddy-local/proxies.caddy`, e as senhas iniciais estão no arquivo root-only `/root/case-atlas-download-credentials.txt` para distribuição pelo administrador. O teste público retornou `401` sem Basic Auth e encaminhou as três credenciais válidas ao serviço. Ao adicionar uma conta AnythingLLM, provisionar também uma credencial Caddy; a lista não é sincronizada automaticamente. Esse mecanismo é separado do login do AnythingLLM; o SSO/sessão do AnythingLLM não está ligado ao endpoint.

As operações administrativas de revogação usam `POST /v1/releases/<release_id>/revoke` com o token de API; não publique essa rota no Caddy. A configuração ativa expõe somente a rota protegida de download.

## Verificação local

Na raiz do projeto:

```bash
python3 -m unittest discover -s tests -v
```

Os testes cobrem catálogo/escopo CSV, consenso, persistência, reutilização, revogação e autenticação HTTP. Eles não substituem o piloto integrado no AnythingLLM e no Caddy.
