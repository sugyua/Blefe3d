# Publicação automática do Blefe Color no Render

O serviço de produção existente é **[blefe3d-teste](https://dashboard.render.com/web/srv-dbtidj5g1s2s73b789hg)**, usando a branch `main` do repositório **[sugyua/Blefe3d](https://github.com/sugyua/Blefe3d)**.

**Endereço público do jogo:** https://blefe3d-teste.onrender.com/

## Por que configurar uma segunda forma de disparar deploys?

Em 17/11/2026, a configuração do Render reportava `autoDeploy=yes` e `autoDeployTrigger=commit`, mas os últimos commits incorporados à `main` não haviam produzido novos deploys. O motivo exato da falha de notificação GitHub→Render ainda não foi confirmado. Causas possíveis incluem conexão criada por URL pública em vez do aplicativo GitHub do Render, permissão insuficiente da integração GitHub, ou perda de notificações do repositório.

Em vez de depender somente dessa integração, este projeto inclui um segundo caminho explícito de implantação via **GitHub Actions + Deploy Hook do Render**, baseado na documentação oficial: https://render.com/docs/deploy-hooks.

## Ativação única (necessita acesso de proprietário ao GitHub e Render)

O workflow já foi incluído em `.github/workflows/test-regras.yml`, mas **não fará nenhum deploy até existir um segredo de repositório com a URL do hook**.

1. No Render, abra o serviço [blefe3d-teste](https://dashboard.render.com/web/srv-dbtidj5g1s2s73b789hg), entre em **Settings** e procure **Deploy Hook**. Copie a URL usando o botão do painel. A URL é uma **credencial secreta**: qualquer pessoa com esse endereço pode solicitar publicações.
2. No GitHub, abra [Settings → Secrets and variables → Actions](https://github.com/sugyua/Blefe3d/settings/secrets/actions). Em **Repository secrets**, clique em **New repository secret**.
3. Nome exato do segredo: `RENDER_DEPLOY_HOOK_URL`. Cole o **Deploy Hook URL completo** como valor, incluindo seus parâmetros, sem aspas ou espaços extras. Clique em **Add secret**. **Não coloque essa URL no README, em issues, prints, comentários ou mensagens do chat.**
4. Confirme em [Actions](https://github.com/sugyua/Blefe3d/actions) que o workflow **Testar regras do Blefe Color** está habilitado. O job `publicar_render` precisa aparecer quando houver push/merge na branch `main`.
5. Para fazer um primeiro teste sem novo commit, entre em **Actions → Testar regras do Blefe Color → Run workflow**, selecione `main` e execute. Primeiro o job `regras` roda os testes. Somente após aprovação, `publicar_render` solicitará uma publicação no Render.
6. Em [Render → Events/Deploys](https://dashboard.render.com/web/srv-dbtidj5g1s2s73b789hg), confirme que o deploy iniciou e terminou com **Live**, exibindo o SHA esperado. Em seguida, abra o jogo e teste a funcionalidade nova em navegador e celular.
7. **Depois de confirmar que o GitHub Actions + Deploy Hook funciona**, configure em **Render → Settings → Auto-Deploy** o modo **Off** se a integração nativa passar a publicar o mesmo commit duas vezes. Com o hook funcionando, o Render continuará recebendo deploys do job do GitHub, mesmo com Auto-Deploy nativo desligado. Evite duas fontes simultâneas de deploy.

## Funcionamento após ativação

```text
Criar uma branch de alteração
        |
        v
Abrir pull request para main
        |
        v
GitHub Actions valida Python, JS, PostgreSQL e  regras
        |
   Falha +----> Corrigir sem publicar
        |
   Sucesso
        |
        v
Merge do PR em main
        |
        v
GitHub Actions roda novamente os testes no push de main
        |
   Sucesso
        |
        v
Job publicar_render envia POST ao Deploy Hook secreto
        |
        v
Render compila e inicia a nova versão
        |
        v
Verificar status Live e testar no navegador
```

**Salvaguardas:** o job de deploy não executa em PRs, apenas em `push` ou `workflow_dispatch` na branch `main`; depende do job `regras` passar; o hook nunca é escrito em arquivos versionados; e a chamada não inclui o parâmetro `ref`, para que o Render utilize o HEAD da branch vinculada.

**Atenção:** sucesso na etapa `publicar_render` significa que o Render **aceitou o pedido**, não que o deploy já está `Live`. Consulte o painel Render antes de dizer a usuários que a versão está publicada.

## Como conferir se a automação está realmente ativa

- Se o secret `RENDER_DEPLOY_HOOK_URL` estiver ausente, o job publicará um **aviso amarelo nos logs/resumo** e **não solicitará deploy**. O workflow não inventa um sucesso.
- Se a chamada HTTP falhar, o job de deploy terminará com **erro** e não marcará uma publicação como concluída.
- Se o job passar e o Render não chegar a **Live**, inspecione os logs de build e execução no Render: o gatilho só inicia o processo; não garante que o servidor sobe com sucesso.
- Não colocar esse segredo em variáveis públicas nem em arquivos do repositório. Para revogá-lo, regenere o Deploy Hook no Render e atualize o segredo no GitHub.

## Alternativa: corrigir a integração nativa do Render

O Render normalmente pode publicar automaticamente novos commits sem deploy hook quando o serviço está corretamente **conectado a uma conta GitHub**, em vez de estar ligado apenas a uma URL de repositório público. Na configuração Render/GitHub, confira:

1. A [instalação do aplicativo Render no GitHub](https://github.com/apps/render/installations/new) tem permissão para acessar o repositório `sugyua/Blefe3d`.
2. O serviço Render aponta para esse repositório e branch `main` usando as **Git Credentials** corretas.
3. **Auto-Deploy** está configurado para **On Commit** ou **After CI Checks Pass**. No segundo caso, os testes do GitHub precisam reportar `success`; sem checks o Render pode não disparar deploy.
4. Confirme um commit de teste e compare os eventos do Render com o SHA publicado.

Documentação Render: https://render.com/docs/git-provider e https://render.com/docs/deploys.

**Escolha uma única forma de disparar publicação em produção.** É válido usar o GitHub Actions com Deploy Hook enquanto a integração nativa estiver com falha; se depois a integração nativa for corrigida, decida qual manter para evitar dois deploys a cada commit.
