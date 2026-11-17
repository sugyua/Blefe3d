# Loja visual e cosméticos — Fase 1

**Status:** primeira implementação no jogo, com demonstração visual e equipamento gratuito. **Não há checkout nem aquisição paga.** A carteira fictícia do Blefe Color não compra cosméticos e nunca se transforma em dinheiro.

## Objetivo

Permitir que jogadores experimentem estilos visuais próprios, sem gerar vantagens sobre as regras de cartas, blefes, recompensas fictícias, ordem de turnos ou resultados de partidas.

## Entregas desta fase

- Botão **Loja de skins** no lobby.
- Loja modal responsiva, com abas **Cartas**, **Mesas** e **Molduras**.
- Visualização dos itens sem baixar fotos externas: todos os modelos são composições CSS e tipografia original.
- **12 itens** no catálogo: **9 liberados gratuitamente** e **3 prévias premium** bloqueadas. Os valores associados às prévias premium são apenas hipóteses de preços futuros; não há compra nem ativação via navegador.
- Botão **Equipar gratuitamente** para itens gratuitos.
- Persistência de escolhas em PostgreSQL para contas cadastradas e visitantes (estes precisam manter o cookie de sessão).
- Personalizações aplicadas à experiência: escolha de verso nas cartas de face oculta, tema da mesa visto pelo jogador e molduras no quadro de avatar/câmera de cada participante. Molduras são divulgadas no estado público da sala e visíveis pelos outros jogadores.
- Inventário protegido por sessão HTTP `HttpOnly` + `Secure` + validação de origem em requisições de escrita.
- Atualizações que não alteram saldos fictícios, ganhos, cartas, vídeos ou microfones.

## Catálogo inicial

| Categoria | Item | Disponibilidade | Valor futuro ilustrativo |
| --- | --- | --- | --- |
| Versos | Clássico | Grátis, padrão | — |
| Versos | Neon Azul | Grátis | — |
| Versos | Pôr do Sol | Grátis | — |
| Versos | Ouro Real | Apenas prévia, bloqueado | R$ 4,90 |
| Mesas | Esmeralda | Grátis, padrão | — |
| Mesas | Oceano | Grátis | — |
| Mesas | Brasa | Grátis | — |
| Mesas | Galáxia | Apenas prévia, bloqueado | R$ 9,90 |
| Molduras | Aço | Grátis, padrão | — |
| Molduras | Verde Menta | Grátis | — |
| Molduras | Violeta | Grátis | — |
| Molduras | Coroa Dourada | Apenas prévia, bloqueado | R$ 6,90 |

Os preços são hipóteses de teste visual, **não são ofertas e não geram pedidos ou cobranças**. O inventário pode ganhar direitos comerciais apenas numa fase posterior, depois da revisão legal, técnica, de pagamentos, segurança e condições da loja.

## Arquitetura

- `cosmetics.py`: catálogo aprovado pelo servidor e padrões de cada slot.
- `accounts.py`: cria as tabelas `game_cosmetic_entitlements` e `game_cosmetic_equipped`, valida propriedade, persiste a seleção e monta o estado da loja.
- `server.py`: endpoints REST e divulgação de molduras nos estados WebSocket.
- `public/index.html`, `public/shop.css`, `public/shop.js`: interface da loja, prévia, abas e aplicação de temas. `public/app.js` exibe molduras dos jogadores na sala.
- `tests/test_cosmetics.py`: testes de catálogo, endpoint com sessão, bloqueio dos itens premium e persistência PostgreSQL.
- `.github/workflows/test-regras.yml`: verifica os scripts da loja e roda a suíte de regras existente.

### Endpoints

| Método | Rota | Autorização | Função |
| --- | --- | --- | --- |
| GET | `/api/shop/catalog` | Público | Consulta catálogo, categorias e status `payments_enabled=false` |
| GET | `/api/shop/me` | Cookie de conta ou visitante | Consulta direitos e itens equipados **da própria identidade** |
| POST | `/api/shop/equip` | Cookie protegido e mesmo Origin | Equipa somente item grátis ou previamente concedido **no servidor** |

Exemplo de payload de equipamento:

```json
{"slot":"table","product_id":"table_ocean"}
```

Não há endpoint `/purchase`, aprovação de pagamentos, grant público de itens premium nem meio de alterar `owned` pelo navegador. O servidor ignora qualquer tentativa de forçar preço, compra ou autorização administrativa na requisição.

## Como testar

1. Abra `https://blefe3d-teste.onrender.com/`, clique em **Loja de skins** e percorra as três abas.
2. Escolha **Neon Azul** e clique **Equipar gratuitamente**. Inicie um treino e observe o verso das cartas ocultas.
3. Volte ao lobby, equipe **Oceano** e observe a mudança do estilo da mesa na partida.
4. Equipe **Verde Menta**, entre numa sala com outro jogador e confirme que a moldura é exibida no quadro de vídeo/avatar de quem a equipou.
5. Recarregue a página: as três escolhas devem continuar ativas.
6. Tente equipar uma prévia premium: o botão não deve habilitar compra ou troca por saldo fictício.
7. Abra outro navegador no mesmo IP: ele terá seu próprio inventário, não conseguirá equipar itens em nome da primeira pessoa.
8. Cadastre e entre com senha para carregar o inventário daquela conta em diferentes dispositivos. O inventário de visitante não é transferido automaticamente.
9. Execute `python -m unittest discover -s tests -v` e valide uma partida humana após personalizar os itens.

## Próximas etapas

- Testes visuais em iPhone, Android e desktop, com revisão de acessibilidade e desempenho da loja e mesa.
- Evoluir artes finais e criar previews estáticas revisadas, mantendo direitos autorais e consistência visual.
- Exibir no futuro itens comprados apenas após confirmação de um provedor compatível por webhook autenticado e idempotente, nunca por sucesso no cliente.
- Painel de catálogo e inventário administrativo com auditoria de ações, sem atribuir o cargo de criador por apelido.
- Migração do banco gratuito do Render antes de **17/12/2026**, com backup e preservação do inventário.
- Estudar política de compras digitais, suporte, reembolsos e provedor legalmente permitido **somente para cosméticos**, não para apostas.

**Fora de escopo:** pagamentos, Pix, planos VIP, passe de temporada, transferência de itens, sorteios de itens, saques e qualquer aposta de dinheiro real.
