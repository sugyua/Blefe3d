# Beta orgânico — meta de 50 jogadores de teste

**Status:** planejamento, ainda sem campanha iniciada ou usuários recrutados.  
**Orçamento de mídia paga:** R$ 0.  
**Escopo:** apenas partidas com dinheiro **fictício**; voz e câmera opcionais.

## Dependências antes de divulgar amplamente
- [ ] Corrigir os bugs bloqueantes do login, das salas e dos convites via WhatsApp.
- [ ] Persistir o saldo fictício e impedir bônus duplicados após reinícios/novos dispositivos.
- [ ] Garantir que saldo real, saques e apostas reais continuem desativados.
- [ ] Validar a moderação, privacidade e autorização de uso de câmera/microfone.
- [ ] Testar PWA com iPhone e Android reais.
- [ ] Validar quatro câmeras e microfones simultâneos em Wi-Fi e 4G.
- [ ] Medir capacidade do Render em ambiente de teste antes de convidar muitos jogadores.

## Recrutamento em cinco ondas
| Onda | Novos convidados | Foco |
|---|---:|---|
| 1 | 5 | Criar sala, entrar, sair e testar tutorial |
| 2 | 10 | Testar câmera, voz, Wi-Fi e dados móveis |
| 3 | 10 | Salas públicas e convites WhatsApp |
| 4 | 15 | Partidas completas, blefe, +2/+4 e revanche |
| 5 | 10 | Retenção de jogadores e instalação PWA |
| **Total** | **50** | |

Não convidar as próximas ondas se houver perda de saldo fictício, travamento da sala ou indisponibilidade frequente.

## Tarefas simples para um novo testador
1. Abrir https://blefe3d-teste.onrender.com/ e verificar a primeira tela.
2. Jogar uma partida gratuita de treino e testar a saída (a entrada, se paga em saldo fictício, não é reembolsável).
3. Procurar uma sala pública ou criar uma sala privada.
4. Compartilhar um convite via WhatsApp e verificar código e entrada.
5. Ligar câmera e microfone voluntariamente, se desejar; experimentar sem eles também.
6. Jogar uma carta oculta; aceitar ou duvidar; empilhar +2 ou +4.
7. Encerrar partida, ver a janela de vitória e negociar revanche.
8. Adicionar o jogo à tela inicial, se o aparelho permitir.

## Métricas a verificar
- **Acesso:** cliques no link e novas sessões (idealmente por analytics respeitoso e agregado).
- **Ativação:** proporção de convidados que entrou numa sala ou concluiu treino.
- **Qualidade:** porcentagem de partidas concluídas, duração, erros e desconexões.
- **Conectividade:** chamadas WebRTC bem-sucedidas com múltiplas redes.
- **Retenção:** jogadores que retornam no segundo dia e após sete dias.
- **Performance:** p50/p95 de latência, CPU e memória durante cargas de 4, 8, 16 e 32 conexões.

Não publicar números sem medição. O painel atual usa métricas em memória e reinicia junto do servidor; não serve como histórico definitivo.

## Coleta de feedback
Perguntas essenciais: (1) Entrou na sala sem ajuda? (2) Teve travamento? Qual aparelho e navegador? (3) Entendeu o blefe oculto e a compra acumulada? (4) Jogaria novamente? (5) Qual seria a melhoria prioritária?

Pedir capturas apenas se o jogador quiser e evitar coletar imagens de câmera ou informações de pagamento.

## Rotina de revisão
Analisar feedback depois de cada onda; registrar bugs com passos de reprodução e gravidade; corrigir antes da próxima onda. Manter uma página de mudanças por versão e sempre avisar quando um teste novo for liberado.
