# Blefe Color — Visitantes, login, saldo de teste e depósitos

## Implementado nesta atualização

- Qualquer visitante pode jogar partidas de **teste**, inclusive salas públicas e privadas, sem cadastrar usuário e senha.
- A primeira visita cria uma identidade aleatória e uma carteira exclusiva de **R$ 50 fictícios**, persistidas no PostgreSQL.
- A identidade de visitante fica em um cookie aleatório, com `Secure` (HTTPS), `HttpOnly` e `SameSite=Lax`. Somente o hash SHA-256 do segredo é armazenado no banco.
- **Não atrelar identidade financeira ao IP:** muitas pessoas compartilham o mesmo IP (rede doméstica, escola, CGNAT) e um mesmo usuário pode mudar de IP entre Wi-Fi e 4G. Tratar o IP somente como parâmetro auxiliar de mitigação de abuso e limitação de criação de visitantes.
- O saldo de visitante pertence à **sessão desse navegador**. Limpar cookies, usar outro aparelho ou trocar de navegador pode impedir a recuperação dessa carteira sem conta.
- Após fazer login, usa-se a carteira separada da **conta registrada**. O saldo de visitante não é transferido nem convertido automaticamente.
- O botão **Depositar** aparece apenas quando o jogador está registrado e logado, e abre uma explicação de indisponibilidade. **Nenhum pagamento real, Pix, cartão, saldo real, saque ou aposta real é executado.**
- A página do jogo apresenta o crédito **“Criado por Sugya”**. Isso é crédito editorial, não prova de identidade nem atribuição de privilégios de administração. Uma futura atribuição de papel de proprietário deve vincular o ID imutável de uma conta após verificação de propriedade, nunca apenas a string `sugya`.

## Regras importantes

- Bots somente em treinos. Salas públicas e privadas continuam sem bots.
- O saldo de teste é separado do dinheiro real e não pode ser sacado.
- A desconexão/abandono durante treino encerra a sala sem devolver a entrada fictícia já cobrada.
- Não prometer depósito habilitado nem solicitar pagamento por Pix para jogar.
- O status jurídico de jogos entre jogadores com valores reais no Brasil exige análise especializada; não ativar pagamento/entrada real por meio de alteração apenas visual.

## Testar antes de divulgar

1. Abrir o site em uma janela anônima. Deve aparecer saldo fictício sem tela obrigatória de login.
2. Entrar em treino gratuito e depois numa sala pública de entrada fictícia.
3. Atualizar a aba: o visitante deve recuperar o mesmo saldo (com cookies preservados).
4. Usar outro navegador ou dispositivo na mesma rede/IP: cada visitante deverá ter um **saldo separado**.
5. Criar conta: após login, a barra mostrará o botão **Depositar**.
6. Clicar no botão: somente abrirá a janela “Depósitos ainda não disponíveis”.
7. Fazer logout: a sessão volta ao visitante (quando o cookie do visitante ainda existir).
8. Testar uma aposta de teste contra bots e verificar o débito e o histórico da carteira de visitante no PostgreSQL.
9. Confirmar que o servidor rejeita jogos com `wallet_type='real'` e que nunca credita carteira real.
10. Não mostrar o selo **Criador** como privilégio administrativo baseado apenas em nome de usuário.

## Limitações

- Não existe garantia de "um bônus por pessoa" para visitantes sem identificação: remover cookies pode gerar nova carteira. O IP não resolve esse problema sem prejudicar pessoas que compartilham a conexão.
- O estado das salas ainda fica na memória do servidor, apesar de as carteiras estarem no banco.
- O PostgreSQL gratuito existente no Render expira em **17 de dezembro de 2026**. Planejar backup e migração antes disso.
