# Blefe Color

Jogo online de cartas e blefes para até quatro participantes, com salas públicas e privadas, convites por WhatsApp, treinamento contra bots e câmera/microfone opcionais.

🎮 **[JOGAR BLEFE COLOR — versão atual no Render](https://blefe3d-teste.onrender.com/)**

**Endereço oficial:** https://blefe3d-teste.onrender.com/ · **Criador:** Sugya · **Plataforma:** navegador/PWA

> **Atenção:** projeto em testes, com possíveis falhas. Entradas e prêmios exibidos no jogo são exclusivamente **saldos fictícios**; não existem depósitos, saques ou apostas com dinheiro real. As carteiras de teste ficam no PostgreSQL; as salas ainda ficam na memória do servidor.

## Instalar no celular (PWA)
- **iPhone:** abrir no Safari, tocar em **Compartilhar → Adicionar à Tela de Início**.
- **Android:** abrir no Chrome e escolher **Instalar aplicativo** ou **Adicionar à tela inicial**.
- O modo PWA fornece ícone e experiência sem barras de navegador; **partidas ainda exigem internet**.
- A instalação é gratuita; não está na App Store nem na Google Play.

## Turnos de 30 segundos e mesas com bots

**Tempo de jogo:** cada jogador tem **30 segundos para jogar** ou decidir se acredita/duvida de uma ação. O prazo é controlado pelo servidor e aparece no topo da tela. Quando acaba, o jogo **compra automaticamente 1 carta** para o jogador e **passa a vez**. Se havia uma ação pendente, a ação é aceita por falta de contestação e a pilha é encerrada, sem cobrar cartas adicionais além da penalidade de uma carta. Atualizar a página, entrar outro jogador ou trocar de aba não reinicia o prazo.

**Oito mesas de treino social:** existem salas de bots de códigos exclusivos (de `BLC001` até `BLC008`) com nomes, entradas fictícias de R$ 0 a R$ 20 e **2 ou 3 bots identificados abertamente**. Elas aparecem em **Salas públicas**; salas privadas reais dos usuários **não são listadas**, para preservar os códigos de convite. Os bots realmente jogam e não representam jogadores humanos reais.

**Entrada durante a partida:** um usuário pode selecionar a mesa de bots, aceitar o valor de entrada **fictício** e tomar o lugar de um bot sem reiniciar a rodada. Ele recebe **exatamente a mão e a vez** daquele bot. Se sair, um bot retoma sua mão; a entrada fictícia debitada **não é reembolsada**. É concedida uma breve janela de reconexão após perda de conexão.

> Essas salas são uma forma de praticar enquanto a comunidade cresce. Elas não indicam presença de humanos e **não oferecem depósitos, saques ou apostas reais**. Com a partida encerrada e sem jogadores humanos na mesa, bots começam uma nova rodada.

## Nova regra de blefe: declarar ação **e** cor

Em uma carta de ação colocada virada para baixo, o jogador (e os bots no treinamento) deve declarar **a ação e a cor**. O próximo jogador pode **acreditar** ou **duvidar**. Ao duvidar, o servidor revela a carta e confere a ação **e** a cor declaradas; se qualquer uma for falsa, o blefador compra **1 carta**, e uma pilha +2/+4 é cancelada.

**Exemplo:** sobre um **2 verde**, alguém coloca um **+2 vermelho** virado para baixo e declara **+2 verde**. A ação é verdadeira, mas a cor é falsa: se o próximo jogador duvidar, quem jogou compra **1 carta**. Declarar **+2 vermelho** sobre o 2 verde também constitui um blefe de jogada inválida, pois a declaração não respeita a cor da mesa.

- **Ações normais** (+2, bloqueio e inverter): a declaração só é verdadeira se a ação e a cor forem as reais e, fora de pilhas, a cor declarada for válida para a mesa.
- **+4 (carta selvagem) e coringa comum:** permitem **escolher livremente** a nova cor; essa escolha não é blefe por si só.
- **Pilha de +2/+4:** continua possível empilhar cartas de compra de qualquer cor, mas o jogador precisa declarar corretamente a cor física da carta normal se quiser falar a verdade. O jogador que descobrir uma mentira cancela a pilha; o último declarante compra **1 carta**.
- **Dúvida errada:** quem duvida compra 1 carta nas ações normais, ou toda a pilha de compra acumulada **mais 1**, mantendo o comportamento anterior.
- **Partidas contra bots:** os bots também declaram ação e cor, podendo blefar em ambas as informações.
- Todos os efeitos se aplicam apenas a cartas de jogo e saldos **fictícios**. Depósitos e apostas reais continuam desativados.

## Como jogar
1. Comece no treinamento grátis contra três bots.
2. Jogue uma carta que combine com a cor ou número da mesa.
3. Cartas de ação são ocultas e podem ser declaradas com blefe; o próximo jogador pode acreditar ou duvidar.
4. Empilhe cartas de compra +2/+4 quando possuir uma delas; se a última declaração for falsa, ela pode ser contestada.
5. Convide amigos por WhatsApp ou encontre salas públicas com outras pessoas.

## Desenvolvimento e testes
```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
python server.py
```

O servidor usa **aiohttp** e WebSocket. As salas ainda são mantidas em memória e podem ser encerradas em reinícios; contas e saldos fictícios ficam no PostgreSQL. Antes de qualquer operação com dinheiro real, o projeto exigiria revisão legal e arquitetura adequada.

## Publicação automática no Render

O projeto possui um pipeline de deploy em **GitHub Actions**, que roda os testes antes de solicitar uma publicação no Render **apenas após merge/push em `main`**. O deploy via GitHub Actions não é executado em branches de pull requests.

**Configuração única pendente:** cadastrar o segredo `RENDER_DEPLOY_HOOK_URL` em **GitHub → Settings → Secrets and variables → Actions**, usando a URL privada de **Deploy Hook** obtida em **Render → Settings**. **Não cole o hook em commits ou mensagens.** Sem esse segredo, o workflow avisa que a publicação não foi solicitada.

Instruções de ativação, validação e prevenção de deploy duplicado: **[Publicação automática GitHub → Render](docs/DEPLOY_AUTOMATICO.md)**.

O endereço público permanece **https://blefe3d-teste.onrender.com/**. Um job concluído no GitHub indica somente que o Render recebeu o pedido; confirme o status **Live** no painel antes de considerar a publicação concluída.

## Planejamento e divulgação
- [Roadmap das próximas 20 atualizações (0.10–0.29)](ROADMAP.md)
- [Página e descrição para itch.io](marketing/ITCH_IO.md)
- [Três roteiros de vídeos e textos para redes sociais](marketing/VIDEOS_E_POSTS.md)
- [Plano de beta orgânico com 50 jogadores](marketing/BETA_50.md)
- [Página de apresentação HTML5 para itch.io](marketing/itch_launcher/index.html)

**Os materiais de divulgação estão preparados, mas não foram publicados automaticamente em contas externas.**

## Contas de jogador

A nova interface inclui uma barra superior com o saldo de **teste** e botões de **Entrar / Criar conta / Sair**. A autenticação usa usuário e senha, sessão em cookie protegido e PostgreSQL; as senhas não são armazenadas em texto puro.

A conexão entre o Render e PostgreSQL usa a variável secreta `DATABASE_URL`. Veja o [guia de contas e configuração](docs/CONTAS.md). O banco gratuito atual expira em **17/12/2026**, e é preciso planejar a migração antes dessa data. Os saldos são fictícios, sem depósito ou saque.

## Visitantes e futuros depósitos

- **Jogar com saldo fictício não exige cadastro:** o jogo cria uma sessão exclusiva do navegador com carteira de teste, mantida no PostgreSQL.
- A carteira **não é associada ao IP**, pois IPs são compartilhados e variáveis. O IP só auxilia no controle de abuso; o acesso ao saldo exige cookie seguro.
- Uma conta com login e senha continua separada da carteira de visitante.
- O botão **Depositar** é mostrado apenas ao entrar em uma conta, mas permanece **informativo e desativado para dinheiro real**. O jogo não aceita depósitos, saques ou apostas reais.
- **Criador:** Sugya (crédito do jogo, sem permissões automáticas por nome de usuário).

Veja [regras e testes de visitantes e depósitos](docs/VISITANTES_E_DEPOSITOS.md).

---

## Loja visual — Fase 1 (protótipo funcional, sem pagamentos)

A **Loja de skins** já conta com um catálogo projetado de **12 itens cosméticos** (versos de cartas, mesas temáticas e molduras de avatar), com **9 itens grátis para equipar** e **3 prévias premium ainda bloqueadas**. A escolha é persistida no PostgreSQL em contas e sessões de visitante, sem interferir em cartas, blefes ou saldos.

**Acesso:** abra o [Blefe Color](https://blefe3d-teste.onrender.com/) e selecione **Loja de skins** no lobby depois da publicação do commit correspondente no Render. Itens premium são apenas prévias com preços ilustrativos; **não há checkout, cobranças, Pix, depósitos nem apostas reais** nesta fase.

Documentação e instruções de testes: **[Loja Visual — Fase 1](docs/LOJA_FASE_1.md)**.

## Plano completo de monetização — sete modelos

> **Estado: planejamento de produto, não implementação nem oferta comercial.** Os preços e prazos abaixo são hipóteses para testes, não valores contratados, projeções de faturamento ou recursos já disponíveis. O jogo continua gratuito, e o saldo de teste é **fictício e não conversível**. Nenhuma entrada, prêmio, depósito ou saque em dinheiro real deve ser ativado com base neste plano.
>
> **Princípio:** monetização apenas por conteúdo cosmético, serviços digitais de experiência ou apoio voluntário, **sem alterar probabilidades, cartas recebidas, resultados, ordem de turnos ou vantagens competitivas**. Jogadores sem pagar continuam podendo criar salas, entrar nas partidas e competir em igualdade.
>
> **Criador:** Sugya. O nome público do criador não substitui autenticação administrativa nem autoriza conceder permissões a uma conta apenas porque ela usa o login "Sugya".

### Visão geral e ordem de implantação

| Frente | Como monetiza | Preço inicial para experimentar | Dependências | Prioridade |
| --- | --- | --- | --- | --- |
| **1. Loja cosmética** | Compra avulsa de versos de cartas, temas de mesa, avatares e molduras | R$ 2,90–19,90 por item/pacote | Login, catálogo, inventário, pagamento autorizado | **P1** |
| **2. Blefe Color VIP** | Assinatura de conveniência e estética | R$ 9,90/mês (hipótese) | Benefícios existentes, recorrência/cancelamento, suporte | **P2** |
| **3. Anúncios** | Publicidade discreta entre partidas e rewarded ads opcionais | Receita variável; sem preço garantido | Volume de jogadores, consentimentos, aprovação da rede | **P3** |
| **4. Reações e animações** | Pacotes de emotes e efeitos visuais | R$ 4,90 por pacote (hipótese) | Sistema de cosméticos, controles de spam/acessibilidade | **P1** |
| **5. Temporadas e passe** | Passe cosmético com trilha de recompensas | R$ 14,90/temporada (hipótese) | Estatísticas persistentes, antifraude, calendário e recompensas | **P3** |
| **6. Patrocínios** | Exposição identificada de marcas em conteúdos/eventos gratuitos | Valor negociado por campanha, não fixado | Audiência comprovada, contrato e regras de publicidade | **P4** |
| **7. Apoio ao criador** | Contribuições voluntárias sem qualquer vantagem nas partidas | Sugestões: R$ 5, R$ 10, R$ 20 | Provedor que permita doações, recibo e transparência | **P1** |

**Separação dos produtos:** a *carteira de teste* serve somente para partidas simuladas; pagamentos, caso futuramente aceitos, comprarão serviços/itens cosméticos ou representarão contribuição voluntária. **Não criar uma carteira de dinheiro real para apostas** nem permitir compra, transferência ou resgate de saldo fictício. O botão atual **Depositar** continua informativo/indisponível; o futuro fluxo comercial deve usar **Loja**, **Assinar VIP** ou **Apoiar o criador**, com objeto da compra explícito.

### 1. Loja de personalizações (P1)

**Proposta:** oferecer identidade visual ao jogador, mantendo o mesmo jogo para todos.

**Catálogo inicial sugerido:**
- Versos de cartas: Clássico Escuro (gratuito), Neon Azul (R$ 2,90), Dourado (R$ 4,90).
- Temas de mesa: Madeira, Galáxia, Cassino Cartoon *sem sugerir apostas reais* (R$ 6,90–9,90).
- Avatar e moldura de perfil/câmera: pacotes (R$ 3,90–7,90).
- Conjuntos promocionais, por exemplo 1 mesa + 2 versos + 1 moldura (R$ 14,90–19,90).
- Prévia visual gratuita do item antes da compra; itens claramente identificados como cosméticos.

**Experiência:** botão **Loja** no lobby → categoria → visualização com demonstração → confirmação de preço e conteúdo → checkout seguro hospedado pelo provedor → confirmação no servidor por webhook → item no inventário → botão **Equipar**. Durante uma partida, troca de visual não altera estado do baralho nem regras.

**Desenvolvimento necessário:** tabelas `shop_products`, `user_entitlements` e `purchase_orders`; identificadores de produtos e preços validados pelo servidor; inventário ligado à conta, não ao IP; assets versionados, fallback padrão e sincronização entre dispositivos; histórico de pedidos e suporte para reembolso/cancelamento. O checkout deve ficar no provedor de pagamento, sem capturar dados de cartão no Blefe Color.

**Critérios de aceite:** item não pode ser concedido apenas por mensagem do navegador; webhook assinado e idempotente; compra registrada uma única vez; visitante pode navegar na loja, mas deve criar/entrar numa conta antes de comprar; item permanece após logout/login e reinício do Render. Não vender itens que prometam vitória ou mudança de cartas.

**Métricas:** visitas à loja, visualização de produtos, início de checkout, conclusão de compra, ticket médio, itens mais equipados e pedidos de reembolso.

### 2. Blefe Color VIP (P2)

**Proposta:** assinatura opcional com experiência premium, sem vantagens competitivas.

**Benefícios possíveis:** remover anúncios próprios do jogo, molduras/temas VIP, estatísticas ampliadas, personalização da sala privada, selo cosmético de apoiador e acesso antecipado a temas visuais. A ausência de anúncios só deve ser vendida se anúncios realmente existirem.

**Preço para teste:** R$ 9,90/mês. Não oferecer plano anual antes de conhecer retenção, custos e cancelamentos.

**Jornada:** comparar **Grátis x VIP** → regras de cobrança e renovação → compra via provedor compatível → licença associada à conta → opção visível **Gerenciar assinatura / Cancelar** → manutenção dos benefícios até o término do período pago. Após vencimento, itens do catálogo VIP voltam ao visual gratuito sem afetar cartas ou saldo fictício.

**Implementação:** planos e benefícios versionados; estado da assinatura no banco; webhooks de ativação, renovação, falha, cancelamento, estorno e expiração; tela de faturas e suporte; checagens de benefício sempre no servidor; proteção contra ativação duplicada. Tratar tributos, regras do consumidor e eventual uso em app stores separadamente.

**Critérios de aceite:** cancelamento compreensível; renovação explicitada; falha de cobrança não bloqueia partidas gratuitas; usuário VIP não recebe vantagens nas jogadas; benefício não é perdido indevidamente no redeploy.

**Métricas:** assinantes ativos, conversão de usuários recorrentes, cancelamentos, churn mensal, receita recorrente líquida, falhas e chamados de cobrança.

### 3. Anúncios não intrusivos (P3)

**Proposta:** monetizar usuários gratuitos sem interromper o turno de ninguém nem comprometer a comunicação por câmera/microfone.

**Posicionamentos:** banner discreto em lobby ou tela de resultado; intersticial somente **após** uma partida concluída e com limite de frequência; vídeo recompensado **opcional**, dando recompensa cosmética sem valor financeiro e sem efeito nas probabilidades do jogo. Nunca abrir anúncio no meio de um desafio de blefe, revanche ou chamada de voz.

**Fase experimental:** validar se uma rede de anúncios aceita explicitamente o conteúdo do Blefe Color, sobretudo considerando referências a saldos fictícios e possíveis políticas sobre jogos que lembram apostas. Não instalar SDK antes da avaliação de privacidade, consentimento e desempenho.

**Implementação:** controles de frequência/limitação por sessão e usuário; exibição somente em posições aprovadas; sinalização e consentimento quando necessário; integração de aprovação/negação do anúncio recompensado no servidor; bloqueio de autoplay intrusivo e de coleta de microfone/câmera por SDKs. VIP, se oferecido, deve retirar os anúncios prometidos.

**Critérios de aceite:** anúncios não ocultam cartas nem ações; nenhuma cobrança ou recompensa financeira; tela utilizável com bloqueador de anúncios; nenhuma dependência de anúncios para começar partida; métricas sem coletar áudio/vídeo das partidas.

**Métricas:** DAU/MAU, impressões por usuário, taxa de preenchimento, eCPM, receita por mil sessões, conclusão de vídeo opcional, impacto em retenção e reclamações.

### 4. Reações, emotes e animações exclusivas (P1)

**Proposta:** vender expressão pessoal apropriada para um jogo social, especialmente nas reviravoltas de blefe.

**Primeiros pacotes:** "Peguei no Blefe!", "Duvido!", "Boa Jogada!", efeitos de vitória, confetes e animações curtas de revelação. Pacote ilustrativo de 10 emotes por R$ 4,90; um conjunto básico continuará gratuito.

**Jornada:** experimentar efeito em prévia → adquirir na Loja → equipar no perfil → botão rápido durante partidas → todos veem a reação (se escolherem habilitar efeitos). Disponibilizar opção **Reduzir movimento / Desativar efeitos**.

**Implementação:** sistema comum de inventário cosmético, lista de emotes permitidos validada pelo servidor, controle de frequência para evitar spam, otimização para celular e modo de baixo consumo. Não permitir imagens, áudios ou mensagens personalizadas enviadas livremente por jogadores sem moderação específica.

**Critérios de aceite:** nenhuma reação bloqueia botões, cartas ou vídeo; atraso da reação não afeta turnos; efeitos podem ser silenciados; usuários gratuitos têm ao menos reações básicas.

**Métricas:** uso de emotes por partida, pacotes vendidos, retenção e taxa de desligamento dos efeitos.

### 5. Temporadas, rankings e passe cosmético (P3)

**Proposta:** dar motivos para voltar ao jogo, com progressão e recompensas não financeiras.

**Temporada piloto:** quatro semanas; conquistas públicas opcionais, como partidas concluídas, blefes descobertos e vitórias. Trilha **gratuita** com temas/emotes básicos e trilha **premium** com cosméticos garantidos, sem sorteios pagos, caixas aleatórias ou melhora nas cartas. Passe experimental: R$ 14,90/temporada.

**Integridade competitiva:** rankings apenas de partidas válidas; limite de resultados contra a mesma conta, detecção de colusão e manipulação por contas múltiplas; partidas de bots separadas de rankings humanos. As regras de pontuação precisam ser transparentes e revisáveis.

**Implementação:** `match_results` persistente, eventos de progressão idempotentes, `season_config`, `player_season_progress`, trilhas de recompensa, cron de fechamento e um painel de moderação. A compra do passe só desbloqueia itens visuais; nunca concede saldo real ou vantagem na rodada.

**Critérios de aceite:** pontos não duplicam em reconexão; temporada fecha sem apagar histórico; jogadores podem participar gratuitamente; recompensas são entregues uma única vez; nenhum prêmio em dinheiro.

**Métricas:** retenção D1/D7/D30, partidas por usuário, conclusão de missões, aquisição e uso de itens do passe, incidência de fraude.

### 6. Patrocínios e mesas temáticas (P4)

**Proposta:** marcas patrocinarem espaços de divulgação e experiências gratuitas dentro do jogo, sem alterar resultados.

**Formatos:** logo discreta em lobby, mesa cosmética temática patrocinada, tela de agradecimento após partida e evento comunitário gratuito com patrocínio identificado. Evitar peças de patrocinadores que promovam apostas, álcool, produtos com restrição etária ou material incompatível com o público.

**Modelo comercial:** montar mídia-kit com audiência real (usuários ativos, sessões e impressões), público e regiões apenas de forma agregada, formatos, período da campanha, limites de frequência e um relatório de entrega. Preço e contrato negociados individualmente; não prometer alcance sem dados.

**Implementação:** painel para subir e agendar criativos aprovados, data de início/fim, campos de identificação **Publicidade/Patrocinado**, controle de cliques, links seguros, revisão editorial e exclusão de anúncios em áreas sensíveis. Criativos de terceiros nunca ganham acesso à câmera, microfone ou dados pessoais dos jogadores.

**Critérios de aceite:** publicidade claramente marcada; término automático da campanha; link externo seguro; nenhuma marca interfere na jogabilidade; relatórios agregados e auditáveis.

**Métricas:** impressões verificadas, taxa de visualização/clique, cumprimento de entrega, renovações e custo de operação por campanha.

### 7. Apoie o Sugya — contribuições voluntárias (P1)

**Proposta:** permitir que pessoas apoiem o desenvolvimento de forma voluntária, sem transformar a contribuição em entrada para partidas.

**UX:** botão **Apoiar o criador**, separado de **Depositar** e da carteira fictícia; explicação do objetivo da contribuição; sugestões de R$ 5, R$ 10 e R$ 20, com valor livre apenas se o provedor permitir; confirmação e comprovante. Se houver agradecimento visual ou selo, deixar claro que não gera vantagem no jogo.

**Implementação:** provedor habilitado para contribuições/doações conforme seu contrato e legislação aplicável; página de suporte ao projeto; notificações e recibos; painel de reconciliação e contato para problemas/estornos. Nunca enviar senha, chave secreta ou credenciais de pagamentos aos navegadores. A chave Pix de contribuição, se usada, precisa aparecer expressamente como **apoio voluntário**, não como recarga de fichas.

**Critérios de aceite:** usuário joga sem contribuir; recibo correto; contribuição não aumenta saldo fictício, não libera prêmios e não altera o ranking; separação contábil e informativa do financiamento do projeto.

**Métricas:** apoiadores únicos, contribuição média, taxa de clique para apoio, custos do provedor e percentual de estornos.

### Arquitetura comercial transversal (pré-requisitos)

1. **Identidade e itens:** compras digitais vinculadas a contas com login; visitantes continuam jogando gratuitamente. Nome de usuário ou IP nunca é prova suficiente de propriedade de uma compra.
2. **Bancos e estados:** manter saldos fictícios e suas movimentações em tabelas separadas de pedidos, pagamentos e direitos de acesso. Não reutilizar `test_balance_cents` para receita, créditos pagos ou valores sacáveis.
3. **Checkout de terceiros:** usar provedor que aceite por escrito o conteúdo e a finalidade específica da transação; conferir aprovação de políticas antes de comercializar. Nunca guardar dados brutos de cartão ou aceitar Pix diretamente para apostas.
4. **Webhooks confiáveis:** assinaturas verificadas, idempotência, controle de estado de pedido, reprocessamento seguro e reconciliação independente. Não liberar item por retorno do cliente ou tela "pagamento concluído".
5. **Segurança:** TLS, sessões protegidas, mitigação de bots, proteção de CSRF e abuso, auditoria de estornos, acesso administrativo por identidade robusta e backups/restauração testados.
6. **LGPD e público:** política de privacidade clara, retenção mínima, consentimentos e regras aplicáveis a crianças e adolescentes; câmera e microfone opcionais sem coleta para marketing. Revisar requisitos de idade, publicidade e pagamentos com profissionais responsáveis.
7. **Disponibilidade:** o banco PostgreSQL gratuito mencionado neste projeto expira em **17/12/2026**; antes de vender algo, migrar para banco durável com backups, monitoramento, plano de falhas e retenção de direitos adquiridos.
8. **Suporte e confiança:** termos de compra, entregas digitais, contestação, política de reembolso aplicável, comunicação de indisponibilidade e contato de suporte.
9. **Conformidade:** avaliação jurídica e tributária do projeto e das regras de provedores/plataformas; **nenhuma aposta, premiação, depósito ou saque real** é autorizada por este documento.

### Fases de execução e responsáveis

| Fase | Período indicativo após aprovação da fase anterior | Entregáveis | Gate para avançar |
| --- | --- | --- | --- |
| **F0 — Estabilidade e segurança** | Semanas 1–2 | Testes com 50 jogadores, correção de falhas de salas/voz/câmera, retenção do PostgreSQL, métricas agregadas, política e suporte | Partidas completas em dispositivos reais; backups e continuidade definidos |
| **F1 — Economia cosmética sem cobrança** | Semanas 3–4 | Tela Loja, 8–12 itens de teste, catálogo, prévia, equipar, inventário e emotes básicos; tudo gratuito no ambiente de teste | Sem efeitos sobre regras, com testes de reconexão e inventário |
| **F2 — Apoio e compra avulsa** | Semanas 5–6 | Escolha de provedor compatível, avaliação jurídica/contábil, recibos, webhook idempotente, catálogo comercial inicial e apoio voluntário | Testes sandbox concluídos; aprovação documental; suporte/reembolso |
| **F3 — VIP** | Semanas 7–8 | Benefícios entregues e medidos, assinatura mensal, cancelamento e gestão de licenças | Retenção inicial demonstrada e faturamento recorrente validado |
| **F4 — Publicidade e temporada** | Semanas 9–12 | Teste de anúncios em lobby/pós-partida, rankings confiáveis, temporada piloto gratuita e passe cosmético | Aprovação da rede de anúncios, métricas e ausência de perda de retenção |
| **F5 — Patrocínios** | Quando houver audiência comprovável | Mídia-kit, tabela de inventário de espaços, contratos e relatório de campanha | Dados verificados e conteúdo patrocinado aprovado |

**Papéis mínimos:** Sugya (priorização, identidade do jogo e aprovação de campanhas); desenvolvimento (frontend, backend, testes e infraestrutura); design (itens e experiência); jurídico/contabilidade (enquadramento e termos); suporte/moderação (atendimento e segurança). Uma pessoa pode acumular papéis, mas as revisões obrigatórias não devem ser ignoradas.

### Backlog técnico inicial — ordem recomendada

- [ ] Congelar e testar as regras de blefe, +2/+4, revanche e salas; manter jogos reais desativados.
- [ ] Corrigir confiabilidade das salas e da comunicação entre quatro dispositivos.
- [ ] Migrar PostgreSQL gratuito antes de 17/12/2026; habilitar backup e restauração verificável.
- [ ] Definir termos, privacidade, regras de compras digitais e fluxo de atendimento.
- [ ] Projetar catálogo, inventário cosmético e ações **Equipar / Desequipar / Pré-visualizar**.
- [ ] Produzir pelo menos 8 itens cosméticos com opções gratuitas.
- [ ] Implantar emotes básicos e controle de spam; garantir opção de reduzir movimento.
- [ ] Criar painel de preços e pedidos de forma segura, em ambiente de teste.
- [ ] Selecionar provedor de pagamento **apenas para produtos/apoio permitidos** e formalizar sua aprovação.
- [ ] Implementar webhooks, idempotência, recibos, reembolsos e reconciliação sem tocar na carteira de teste.
- [ ] Lançar pequeno piloto de compras cosméticas, após validação legal e operacional.
- [ ] Avaliar VIP com benefícios disponíveis e cancelamento acessível.
- [ ] Medir retenção antes de integrar anúncios e passe de temporada.
- [ ] Criar mídia-kit e patrocínios somente com números de audiência verificáveis.

### Indicadores de desempenho (sem prometer receita)

| Indicador | Definição | Motivo |
| --- | --- | --- |
| **D1/D7/D30** | Jogadores que retornam 1/7/30 dias após o primeiro acesso | Medir retenção antes de cobrar |
| **Ativação** | Novos jogadores que terminam um treino ou partida humana | Encontrar falhas na entrada no jogo |
| **Partidas concluídas** | Concluídas ÷ iniciadas, separando treino e multiplayer | Qualidade do produto |
| **Conversão da loja** | Compradores ÷ visitantes elegíveis à compra | Validar itens sem pressão de compra |
| **ARPPU** | Receita líquida / usuários pagantes no período | Ticket real de quem comprou |
| **ARPU** | Receita líquida / usuários ativos no período | Sustentabilidade do modelo |
| **Churn VIP** | Assinaturas canceladas ou expiradas ÷ base inicial | Valor percebido e retenção |
| **Receita líquida** | Receita efetivamente recebida, descontados custos de provedor, reembolsos, tributos e demais deduções aplicáveis | Evitar confundir vendas brutas com lucro |
| **Satisfação/privacidade** | Reclamações, estornos e incidentes por grupo de usuários | Preservar confiança e segurança |

**Critério de decisão:** não ativar uma nova cobrança apenas porque a interface está pronta. Cada fase precisa de testes automatizados, validação com pessoas reais, transparência comercial, revisão de risco e evidência de que a monetização não reduziu a experiência gratuita.

### O que não fazer

- Não vender créditos da carteira fictícia como se fossem dinheiro resgatável.
- Não oferecer depósitos ou prêmios em dinheiro com base no modelo atual de partidas.
- Não vender cartas mais fortes, maior chance de comprar certas cartas ou vantagens na disputa.
- Não obrigar jogadores a assistir anúncios para continuar a partida.
- Não expor áudio, vídeo, identidade ou dados de pagamento para anunciantes e patrocinadores.
- Não associar permissões administrativas ao apelido `Sugya` sem comprovação de identidade e controle de acesso apropriado.

### Resultado esperado deste planejamento

O Blefe Color continua sendo **um jogo gratuito de cartas e blefes**, com duas frentes de crescimento: **mais partidas concluídas e jogadores recorrentes**, e **receita opcional por estética, conveniência e apoio ao criador**. O primeiro lançamento comercial recomendado é **Loja cosmética + emotes + Apoiar o Sugya**; VIP, anúncios, temporadas e patrocínios vêm depois, conforme maturidade e aprovação das dependências.
