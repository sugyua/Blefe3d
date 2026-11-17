# Contas de jogadores e saldo de teste — Blefe Color

## Situação desta mudança

Esta implementação foi preparada em uma **pull request**. Ela **não deve ser publicada em produção** antes de configurar `DATABASE_URL`, testar cadastro/login em navegador real e verificar o histórico da carteira.

### Objetivo

- Barra fixa no topo com **saldo de teste** e entrada/saída da conta.
- Cadastro com **nome de usuário e senha**, login e logout.
- Senhas protegidas por **Argon2id** (hash com sal aleatório) e nunca armazenadas em texto puro.
- Sessão com token aleatório de alta entropia em cookie **HttpOnly**, **Secure** (em HTTPS) e **SameSite=Lax**. Apenas o hash SHA-256 do token é salvo no banco.
- Toda conexão WebSocket do jogo exige autenticação pelo cookie, ignorando o antigo token do `localStorage`.
- Um único bônus inicial de **R$ 50,00 fictícios** por conta; lançamentos de entrada e prêmio com chaves idempotentes e transações PostgreSQL.
- Saldo real, saques, depósitos e jogos com dinheiro real continuam **indisponíveis**.

## Configurar no Render

Banco gratuito de testes criado para este projeto:

- **Nome:** `blefe-color-accounts`
- **ID Render:** `dpg-dbu501bm8hqs73e4tfh0-a`
- **Região:** Virginia (mesma do serviço web).
- **Expiração do plano gratuito:** **17/12/2026**, conforme o próprio Render informou.

**Passos para conectar sem divulgar a senha:**

1. Entre no [painel do banco no Render](https://dashboard.render.com/d/dpg-dbu501bm8hqs73e4tfh0-a).
2. Em **Connections**, copie **Internal Database URL** (não a URL pública), usando o botão de cópia do Render. A URL inclui credenciais; **não cole em chat, issues, commits ou documentação**.
3. Entre no [serviço Blefe Color no Render](https://dashboard.render.com/web/srv-dbtidj5g1s2s73b789hg) em **Environment**.
4. Adicione uma variável **secreta** com chave `DATABASE_URL` e o valor da Internal Database URL. Salve.
5. Antes de fazer merge da PR, confirme que o teste do GitHub Actions `regras` passou.
6. Faça merge e acompanhe o deploy. `/api/auth/me` deve devolver 401 antes do login; após registrar, retorna a conta autenticada sem senha.
7. No iPhone e Android, teste criar conta, sair, entrar novamente, recuperar o mesmo saldo e tentar abrir uma partida sem login (acesso deve ser negado).
8. Teste uma partida de entrada fictícia, registre o valor, faça logout e login e confira se o histórico e saldo são preservados.

O servidor retorna 503 em cadastros/logins sem banco e **não permite jogar anonimamente**, evitando creditar saldo temporário sem proteção.

## Limitações e pendências antes de abrir o beta

- **O banco grátis tem prazo de expiração.** Antes de 17/12/2026, será necessário migrar com cuidado para armazenamento persistente adequado, com backup e custo previamente aprovado. A implementação atual **não promete retenção após a expiração**.
- Ainda não existe **recuperação de senha por e-mail**; cadastros devem comunicar isso claramente.
- Limites de login/cadastro por IP são **em memória**, não compartilhados entre instâncias. Para escala, usar camada de proteção/rate limit distribuído.
- O banco salva saldos e eventos, mas o estado das **salas ainda fica na memória do processo**. Uma queda do servidor durante a partida pode perder o pote pendente; precisamos de recuperação/reembolso de partidas interrompidas de modo verificável antes de lançar o beta.
- Não associar contas novas a antigos tokens anônimos do navegador: o token anterior não comprovava identidade e não deve servir para apropriar-se do saldo de outra pessoa.
- Não considerar usuário/senha um sistema pronto para apostas reais; dinheiro real continua permanentemente desativado nesta fase.

## Desenvolvimento local

Defina a variável `DATABASE_URL` para seu PostgreSQL de desenvolvimento (não use o banco de produção nos testes). Depois:

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python server.py
```

Sem `DATABASE_URL`, o site é servido para diagnóstico, mas os endpoints de autenticação não liberam partidas.
