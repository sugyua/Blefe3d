# Blefe Color

Jogo online de cartas e blefes para até quatro participantes, com salas públicas e privadas, convites por WhatsApp, treinamento contra bots e câmera/microfone opcionais.

🎮 **Jogar grátis:** https://blefe3d-teste.onrender.com/

> **Atenção:** projeto em testes, com possíveis falhas. Entradas e prêmios exibidos no jogo são exclusivamente **saldos fictícios**; não existem depósitos, saques ou apostas com dinheiro real. A carteira ainda precisa de persistência antes de um beta público amplo.

## Instalar no celular (PWA)
- **iPhone:** abrir no Safari, tocar em **Compartilhar → Adicionar à Tela de Início**.
- **Android:** abrir no Chrome e escolher **Instalar aplicativo** ou **Adicionar à tela inicial**.
- O modo PWA fornece ícone e experiência sem barras de navegador; **partidas ainda exigem internet**.
- A instalação é gratuita; não está na App Store nem na Google Play.

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

O servidor usa **aiohttp** e WebSocket. Atualmente armazena várias informações em memória; reiniciar a instância pode zerar sessões e saldos. Antes de qualquer operação com dinheiro real, o projeto exigiria revisão legal e arquitetura adequada.

## Planejamento e divulgação
- [Roadmap das próximas 20 atualizações (0.10–0.29)](ROADMAP.md)
- [Página e descrição para itch.io](marketing/ITCH_IO.md)
- [Três roteiros de vídeos e textos para redes sociais](marketing/VIDEOS_E_POSTS.md)
- [Plano de beta orgânico com 50 jogadores](marketing/BETA_50.md)
- [Página de apresentação HTML5 para itch.io](marketing/itch_launcher/index.html)

**Os materiais de divulgação estão preparados, mas não foram publicados automaticamente em contas externas.**

## Contas de jogador (versão em preparação)

A nova interface inclui uma barra superior com o saldo de **teste** e botões de **Entrar / Criar conta / Sair**. A autenticação usa usuário e senha, sessão em cookie protegido e PostgreSQL; as senhas não são armazenadas em texto puro.

**Antes de liberar esta alteração**, é necessário conectar o banco gratuito do Render por meio da variável secreta `DATABASE_URL`. Veja o [guia de contas e configuração](docs/CONTAS.md). O banco gratuito atual expira em **17/12/2026**, e é preciso planejar a migração antes dessa data. Os saldos são fictícios, sem depósito ou saque.
