'use strict';
/* Instalação PWA e primeiros passos — sem interferir com o WebSocket do jogo. */
(()=>{
  const $=id=>document.getElementById(id);
  const standalone=()=>window.matchMedia('(display-mode: standalone)').matches||navigator.standalone===true;
  const isApple=/iPad|iPhone|iPod/.test(navigator.userAgent)||
    (navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
  let deferredPrompt=null;
  const installBtn=$('installApp');
  const installModal=$('installModal');
  const tutorial=$('welcomeGuide');
  function hide(el){if(el)el.hidden=true}
  function show(el){if(el)el.hidden=false}
  function renderInstallHelp(){
    const text=$('installText');
    if(isApple){
      text.textContent='No Safari, toque em Compartilhar (quadrado com seta), escolha Adicionar à Tela de Início e confirme. O jogo aparecerá como aplicativo.';
    }else{
      text.textContent='No Chrome ou Edge, use o menu ⋮ e escolha Instalar aplicativo ou Adicionar à tela inicial. Se o navegador permitir, este botão também inicia a instalação.';
    }
    show(installModal);
  }
  window.addEventListener('beforeinstallprompt',event=>{
    event.preventDefault();
    deferredPrompt=event;
    if(!standalone())show(installBtn);
  });
  window.addEventListener('appinstalled',()=>{
    deferredPrompt=null;
    hide(installBtn);hide(installModal);
  });
  installBtn?.addEventListener('click',async()=>{
    if(standalone())return;
    if(!deferredPrompt){renderInstallHelp();return}
    const prompt=deferredPrompt;deferredPrompt=null;
    try{await prompt.prompt();await prompt.userChoice}
    catch(e){renderInstallHelp()}
  });
  $('closeInstall')?.addEventListener('click',()=>hide(installModal));
  if(standalone())hide(installBtn);

  const seenKey='blefe_color_welcome_guide_v1';
  const invite=new URLSearchParams(location.search).get('sala');
  function dismissWelcome(){
    hide(tutorial);
    try{localStorage.setItem(seenKey,'1')}catch(e){}
  }
  $('welcomeClose')?.addEventListener('click',dismissWelcome);
  $('welcomeTraining')?.addEventListener('click',()=>{
    dismissWelcome();
    $('trainingStake').value='0';
    $('training')?.scrollIntoView({behavior:'smooth',block:'center'});
    $('training')?.focus();
  });
  $('welcomePublic')?.addEventListener('click',()=>{
    dismissWelcome();
    $('publicBrowse')?.click();
  });
  $('showGuideFromLobby')?.addEventListener('click',()=>show(tutorial));
  if(!invite){
    let seen=false;
    try{seen=localStorage.getItem(seenKey)==='1'}catch(e){}
    if(!seen){
      const tryWelcome=()=>{
        if(document.body.dataset.authenticated==='true'&&$('lobby')&&!$('lobby').hidden)
          show(tutorial);
      };
      setTimeout(tryWelcome,550);
      document.addEventListener('blefe:authenticated',tryWelcome,{once:true});
    }
  }
  if('serviceWorker' in navigator&&location.protocol==='https:'){
    window.addEventListener('load',()=>{
      navigator.serviceWorker.register('/sw.js',{scope:'/'}).catch(error=>
        console.warn('Instalação offline indisponível:',error));
    });
  }
})();
