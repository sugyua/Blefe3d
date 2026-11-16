# Roadmap oficial — Blefe Color
**Próximas 20 atualizações planejadas: v0.10 → v0.29**

> **Status:** planejamento, não funcionalidades já concluídas.  
> **Base atual:** v0.9 (protótipo web para iPhone, Android e computador).  
> **Foco:** partidas estáveis entre pessoas reais, treino contra bots separado, blefes com cartas de ação ocultas, voz/câmera opcionais e carteira **exclusivamente fictícia**.  
> **Ordem:** proposta por dependências, não por datas prometidas. A sequência pode mudar após testes com usuários.

## Regras de produto que não podem regredir

- Máximo de **quatro jogadores por mesa**; três adversários e o próprio jogador aparecem nos quatro quadros de vídeo/avatares.
- **Bots apenas no treinamento.** Salas públicas e privadas para jogar com outras pessoas devem conter exclusivamente humanos. Não habilitar bots em qualquer futura sala com dinheiro real.
- Um novo jogador recebe **R$ 50,00 de teste uma única vez**, após criação segura da conta; valores de teste não têm valor monetário, não podem ser sacados, convertidos ou misturados com outra carteira.
- **Dinheiro real, depósitos e saques permanecem desativados.** Uma implementação futura exigiria avaliação jurídica e regulatória, verificação de identidade, controles antifraude, proteção de menores e políticas das plataformas; **não integra este cronograma como funcionalidade a ativar**.
- Abandonar um **treino contra bots** encerra a sala imediatamente e **não reembolsa** a entrada fictícia já descontada; treino gratuito não gera perda. Documentar o comportamento de desconexão e tornar o saldo persistente.
- Nas partidas entre pessoas, a sala deve continuar aplicando política de abandono/reconexão própria, distinta do treinamento; jamais transferir saldo sem operação registrada no servidor.
- As cartas de ação são declaradas **viradas para baixo**; o próximo jogador pode aceitar ou duvidar. Nas pilhas de +2/+4, a soma é visível; a identidade real da última carta só é revelada ao duvidar.
- É necessário **possuir uma carta +2 ou +4 para empilhar**, embora seja permitido blefar sobre **qual das duas** foi jogada. Ao duvidar errado, compra-se a pilha + 1; ao descobrir o blefe, o autor da última carta compra 2 e a pilha é cancelada.
- Falar e manter a câmera ligada simultaneamente deve funcionar para todos; quadros dos participantes ficam com anel verde enquanto seu áudio é detectado localmente.
- Salas públicas exibem anfitrião, ocupação, valor de entrada fictício e opção de participar; salas privadas são acessíveis por código/convite, não listadas publicamente.
- Qualquer doação por Pix é voluntária, **não compra créditos**, e a futura promessa de acesso sem anúncios após doação **acima de R$ 5,00** exige pagamento verificado e direito persistente na conta. O jogo atualmente não usa anúncios.

## Visão geral

| Versão | Tema principal | Prioridade | Marco |
|---|---|---|---|
| **0.10** | Base de testes e correções críticas | P0 | Confiabilidade |
| **0.11** | Contas, identidade e segurança de sessões | P0 | Confiabilidade |
| **0.12** | Saldo fictício persistente e transações atômicas | P0 | Confiabilidade |
| **0.13** | Desconexão, abandono e reconexão | P0 | Confiabilidade |
| **0.14** | Auditoria das regras de cartas e pilhas | P0 | Confiabilidade |
| **0.15** | Resultado, prêmio fictício e revanche | P0 | Confiabilidade |
| **0.16** | Lobby e salas públicas aprimorados | P1 | Multiplayer |
| **0.17** | Salas privadas, convites e prontidão | P1 | Multiplayer |
| **0.18** | Voz simultânea estável e anel de fala | P0 | Multiplayer |
| **0.19** | Câmeras simultâneas no Safari/Android | P0 | Multiplayer |
| **0.20** | Conectividade WebRTC e TURN | P0 | Multiplayer |
| **0.21** | Interface mobile e acessibilidade | P1 | Experiência |
| **0.22** | Animações e efeitos de blefe | P1 | Experiência |
| **0.23** | Treinamento e bots mais inteligentes | P1 | Experiência |
| **0.24** | Moderação e proteção de privacidade | P0 | Experiência |
| **0.25** | Painel interno e telemetria confiável | P1 | Operação |
| **0.26** | Testes de estresse por etapas | P0 | Operação |
| **0.27** | Escalabilidade e recuperação após reinícios | P1 | Operação |
| **0.28** | Doações e remoção verificada de anúncios | P2 | Operação |
| **0.29** | Beta público com métricas e checklist de lançamento | P1 | Operação |

**Legenda:** P0 = bloqueia teste público confiável; P1 = experiência essencial; P2 = pode ser adiada.

---

## Fase 1 — Confiabilidade e regras (0.10–0.15)

### v0.10 — Testes automatizados e correções críticas · P0
**Entregas:** consolidar testes de regras do servidor, smoke tests de criação/entrada/saída de salas e teste do JavaScript no navegador; validar execução do CI no GitHub Actions; revisar estados inconsistentes ao fechar abas.

**Critérios de aceite:**
- Os testes de abandono do treino, bots proibidos em salas humanas, desafios, pilhas, carteira fictícia e início de partida são executados automaticamente em cada alteração.
- Uma falha nos testes bloqueia a publicação; não há erros de JavaScript na criação de uma sala e em uma partida de ponta a ponta.
- Existe uma lista de regressão manual no Safari iOS e no Chrome Android.

### v0.11 — Contas e sessões seguras · P0
**Entregas:** identificação estável de jogadores, login/recuperação de conta (sem exigir exposição pública de dados pessoais), tokens de sessão revogáveis, proteção contra impersonação e limites de requisições; rotacionar o segredo do painel administrativo e manter todos os segredos no Render.

**Critérios de aceite:**
- Entrar por outro aparelho não cria saldo de boas-vindas extra para a mesma conta.
- Tokens inválidos não permitem assumir uma conta ou consultar o painel.
- Dados de câmera e voz não são gravados por padrão.

### v0.12 — Carteira fictícia persistente · P0
**Entregas:** banco de dados para saldo/teste, histórico e bônus inicial; registro atômico e idempotente de entrada e prêmio; reconciliar saldo após reinício; exibir separadamente a carteira real **indisponível**.

**Critérios de aceite:**
- Bônus de **R$ 50,00 fictícios** é concedido uma única vez por conta.
- Débito e prêmio são lançados exatamente uma vez, inclusive com clique duplo, reconexão ou reinício.
- Saldo de teste não migra para dinheiro real; é impossível sacar ou depositar no protótipo.
- Desistência de treino com entrada paga preserva o débito após reiniciar o servidor.

### v0.13 — Abandono e reconexão · P0
**Entregas:** política distinta para treino e multiplayer humano: treino fecha na saída/desconexão; sala humana oferece prazo de reconexão e estado de desconectado, com transição definida caso alguém não volte.

**Critérios de aceite:**
- O treino encerra e não reembolsa uma entrada já debitada, seja ao clicar em sair, fechar a aba ou perder a conexão WebSocket.
- Na sala humana, reconectar não distribui novas cartas nem cobra novamente a entrada.
- Abandonos em salas humanas não deixam turno travado nem saldo fictício sem destino definido.

### v0.14 — Regras do baralho e pilhas +2/+4 · P0
**Entregas:** bateria de casos-limite para cores, curinga, bloqueio, reverso, +2, +4, ações ocultas, blefes e pilhas; registrar explicações claras do que acontece ao duvidar da última carta de uma pilha.

**Critérios de aceite:**
- As regras de cada jogada são validadas pelo servidor, não apenas pelos botões da interface.
- Não é possível empilhar uma carta comum fingindo ser +2/+4; é possível declarar +2 com +4, e vice-versa, e ser desafiado.
- Dúvida errada aplica pilha acumulada + 1; dúvida correta cancela a pilha e aplica 2 cartas ao último blefador.
- Testes cobrem mão vazia, fim de baralho, carta final de ação e sequência de cartas ocultas.

### v0.15 — Fim de partida, resultado e revanche · P0
**Entregas:** consolidar vitória, janela de resultado, animações de celebração, contagem das cartas restantes, pote fictício, reentrada e votação unânime de novas entradas entre participantes humanos.

**Critérios de aceite:**
- O vencedor e os movimentos de saldo fictício são os mesmos em todos os aparelhos.
- O anfitrião propõe valor; a próxima rodada só começa após aceitação de todos os participantes que vão jogar.
- Jogadores podem recusar, voltar ao menu ou ficar assistindo; espectadores não têm cartas nem influenciam turnos.

## Fase 2 — Multiplayer e comunicação (0.16–0.20)

### v0.16 — Busca de salas públicas · P1
**Entregas:** atualização automática da lista, filtros por vagas e entrada fictícia, diferenciação entre sala esperando e em andamento, indicação de anfitrião conectado e remoção de salas expiradas.

**Critérios de aceite:**
- Nenhuma sala privada aparece na listagem.
- Dois jogadores tentando a última vaga não conseguem ultrapassar quatro por sala.
- O valor é mostrado antes do aceite e validado novamente pelo servidor ao entrar.

### v0.17 — Salas privadas, convite e prontidão · P1
**Entregas:** convite pelo WhatsApp/compartilhamento do sistema, código em texto copiável, link direto que abre prévia da sala, confirmação de entrada fictícia, botão **Estou pronto** e controle de início pelo anfitrião.

**Critérios de aceite:**
- Convite contém código, link, nome do anfitrião e valor **em saldo de teste**.
- Convite funciona abrindo pelo Safari e por navegadores integrados ao WhatsApp.
- A partida não começa com jogadores não prontos; bots nunca entram em salas humanas.

### v0.18 — Voz simultânea e indicador de quem fala · P0
**Entregas:** revisar WebRTC para quatro microfones simultâneos, volume individual, botão de mudo, medição de voz local sem transmissão de níveis, anéis verdes e limpeza de recursos de áudio.

**Critérios de aceite:**
- Quatro participantes podem falar ao mesmo tempo e ouvir uns aos outros.
- Um anel verde aparece em cada câmera/avatar cuja voz está ativa, inclusive no quadro do próprio jogador.
- Modo silencioso não mantém anel ativo e não interfere no microfone dos demais.
- A câmera não é reiniciada quando uma carta é jogada.

### v0.19 — Quatro câmeras estáveis no iPhone · P0
**Entregas:** testar Safari/iOS e Android com quatro vídeos simultâneos, restabelecer tracks após bloqueio de tela/troca de aplicativo, controlar bitrate e resolução, evitar recriação desnecessária do elemento de vídeo.

**Critérios de aceite:**
- Quatro câmeras podem ficar ligadas simultaneamente, inclusive a prévia espelhada do próprio jogador.
- Teste real prolongado não provoca travamento progressivo conhecido; quando o sistema interromper a câmera, existe caminho claro de recuperação.
- Desligar câmera substitui por avatar sem interromper voz.

### v0.20 — Redes diferentes e servidor TURN · P0
**Entregas:** configurar STUN/TURN, credenciais temporárias, diagnóstico de ICE e fallback de conectividade; documentar limites e custo de uma arquitetura peer-to-peer de quatro participantes.

**Critérios de aceite:**
- Pessoas conectadas por Wi-Fi doméstico, 4G/5G e redes com NAT restritivo conseguem estabelecer voz e vídeo nos cenários de teste definidos.
- TURN tem autenticação e não se torna relay público.
- Os indicadores de conexão não expõem IPs ou informações privadas aos outros jogadores.

## Fase 3 — Experiência e segurança da comunidade (0.21–0.24)

### v0.21 — Layout mobile e acessibilidade · P1
**Entregas:** ajuste para telas menores, áreas seguras do iPhone, visualização ampliada de cartas, botões sem toques acidentais, realce de turno, contraste e rótulos em português.

**Critérios de aceite:**
- Quatro quadros de participantes, mesa e mão ficam visíveis em telefones populares.
- Jogador identifica com clareza quem está na vez, cartas próprias, pilha de compras e quantidade de cartas dos adversários.
- A interface funciona com tamanho de fonte ampliado e preferência de animação reduzida.

### v0.22 — Animações e efeitos visuais · P1
**Entregas:** cartas voando até a mesa, pilhas visuais, virar da carta oculta, revelação de blefe com **ACERTOU/ERROU**, contagem da penalidade, destaque do vencedor e otimização gráfica.

**Critérios de aceite:**
- Todas as animações refletem um resultado já validado pelo servidor e não revelam cartas escondidas prematuramente.
- Sem bloqueios de interação, travamentos ou vazamento de animações após sair da partida.
- Dispositivos modestos podem reduzir ou desativar efeitos.

### v0.23 — Bots e tutorial de treinamento · P1
**Entregas:** tutorial guiado, níveis de dificuldade dos bots, explicação visual da compra acumulada e estratégias de blefe simples; indicação explícita de partida simulada contra bots.

**Critérios de aceite:**
- Um jogador novo consegue completar tutorial e um treino gratuito sem ajuda externa.
- Bots aceitam, desafiam e empilham +2/+4 sem infringir regras.
- Os bots ficam restritos a treinamento; encerrar treino com entrada fictícia não gera reembolso.

### v0.24 — Segurança, moderação e privacidade · P0
**Entregas:** bloquear/mutar participante, denunciar abuso, nomes permitidos, controle de convites e rate limits; consentimento de câmera/microfone e documentação de retenção de dados.

**Critérios de aceite:**
- Cada pessoa consegue silenciar outra sem impedir o áudio dos demais.
- Contas/sessões abusivas podem ser restringidas administrativamente.
- Nenhuma transmissão é gravada sem consentimento específico; permissões são opcionais e revogáveis.

## Fase 4 — Operação, escala e beta (0.25–0.29)

### v0.25 — Painel interno e observabilidade · P1
**Entregas:** painel com autenticação robusta, estados de salas, ocupação, líder provisório por menos cartas, pote e entrada fictícios, conexões, erros e latência; histórico persistente e gráficos; segregação entre métricas públicas e privadas.

**Critérios de aceite:**
- Apenas administrador autenticado vê detalhes das salas; chaves não ficam no GitHub ou no navegador do jogador.
- Painel indica claramente que o líder provisório não é o vencedor definitivo.
- Existe histórico de erros e de pico além da duração de um processo no Render.

### v0.26 — Estresse controlado e capacidade máxima medida · P0
**Entregas:** executar uma campanha progressiva de carga autorizada em ambiente separado: conexões WebSocket, criação e jogadas, turnos/latência, abandono e reconexão, uso de CPU/RAM; depois uma campanha menor com câmeras/voz reais ou simuladores especializados.

**Critérios de aceite:**
- Publicar tabela com concorrência sustentada, p50/p95 de latência, taxa de erro, CPU/RAM e método de teste.
- Definir limite operacional seguro **medido**, e não inferido do plano do Render.
- Rodadas de carga não derrubam o servidor onde amigos estão jogando; testes param automaticamente ao ultrapassar critérios de segurança.

### v0.27 — Preparação para escala horizontal · P1
**Entregas:** remover dependências de salas e carteiras mantidas apenas na memória; persistir estado das partidas, coordenar sessões/WebSockets e eventos entre instâncias; recuperação após deploy; revisar arquitetura de voz/vídeo (mesh versus SFU).

**Critérios de aceite:**
- Reiniciar uma instância não zera carteira, histórico e identidade do jogador.
- Mensagens da mesma sala permanecem consistentes ao usar mais de uma instância.
- Comportamento de reconexão, sala encerrada e atualização de pote não duplica transações.

### v0.28 — Apoio ao projeto e benefício sem anúncios · P2
**Entregas:** página de apoio voluntário, chave Pix oficial somente após configuração autorizada, confirmação verificável de doação, associação da doação à conta e concessão permanente de experiência sem anúncios após valor **acima de R$ 5,00**, quando/onde houver anúncios.

**Critérios de aceite:**
- Doar não acrescenta saldo à carteira de teste ou real e não altera as chances no jogo.
- Benefício só é ativado após confirmação de pagamento; nenhuma doação é marcada como paga por clique em botão.
- Conta mantém o benefício após logout, reinstalação ou troca de aparelho.
- Se não houver serviço de pagamento confiável ou enquadramento jurídico aplicável, manter recurso desabilitado.

### v0.29 — Beta público e ciclo de melhoria · P1
**Entregas:** beta com usuários convidados, instrumento de feedback, estatísticas básicas de partidas e desconexões, telemetria com privacidade, relatórios de bugs e prioridades da versão 1.0.

**Critérios de aceite:**
- Checklist de lançamento passa em iPhone, Android e desktop.
- Existe relatório real de estabilidade, taxa de partidas concluídas, conexões de voz/vídeo e problemas conhecidos.
- O produto comunica claramente **somente partidas de teste**; modos com dinheiro real continuam indisponíveis até eventual análise legal e autorização específica.

---

## Critérios globais para marcar uma versão como concluída

1. Código revisado e registrado em commit específico no GitHub.
2. Testes automatizados relevantes executados e resultado documentado (não presumir sucesso).
3. Smoke test em Android e/ou iPhone para mudanças de interface e mídia.
4. Atualização de textos, regra de jogo e tutorial quando o comportamento mudar.
5. Deploy no Render confirmado como **live**, com rollback possível; uma versão no repositório **não** significa que está publicada.
6. Saldo fictício, bots, privacidade e distinção entre treinamento/salas humanas não podem regredir.
7. A versão só ganha a marca **Concluída** após os critérios de aceite daquela versão serem efetivamente verificados.

## Como acompanhar

- [ ] **v0.10** — Testes e correções
- [ ] **v0.11** — Contas e sessões
- [ ] **v0.12** — Carteira persistente
- [ ] **v0.13** — Abandono e reconexão
- [ ] **v0.14** — Regras e pilhas
- [ ] **v0.15** — Vitória e revanche
- [ ] **v0.16** — Busca pública
- [ ] **v0.17** — Convites e prontidão
- [ ] **v0.18** — Voz e anel verde
- [ ] **v0.19** — Câmeras
- [ ] **v0.20** — TURN
- [ ] **v0.21** — Interface mobile
- [ ] **v0.22** — Animações
- [ ] **v0.23** — Bots e tutorial
- [ ] **v0.24** — Moderação
- [ ] **v0.25** — Observabilidade
- [ ] **v0.26** — Teste de capacidade
- [ ] **v0.27** — Escala e persistência
- [ ] **v0.28** — Doação verificada e sem anúncios
- [ ] **v0.29** — Beta público

**Observação:** itens já presentes de maneira parcial na v0.9 serão **estabilizados e validados** nas versões respectivas; a presença de um protótipo não significa que todos os critérios estão atendidos.
