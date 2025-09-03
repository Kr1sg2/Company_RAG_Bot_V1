export function hasTTS(){return typeof window!=='undefined'&&'speechSynthesis'in window;}
export function speak(text:string){ if(!hasTTS())return; try{ window.speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance(text); u.rate=1;u.pitch=1;u.volume=1; window.speechSynthesis.speak(u);}catch{} }
export function stopSpeak(){try{window.speechSynthesis.cancel();}catch{}}

export type STTHandle={start:()=>void;stop:()=>void;supported:boolean;};
export function createSTT(onResult:(finalText:string)=>void):STTHandle{
  const SR:any=(window as any).SpeechRecognition||(window as any).webkitSpeechRecognition;
  if(!SR) return {start() {}, stop() {}, supported:false};
  const rec=new SR(); rec.lang='en-US'; rec.continuous=false; rec.interimResults=true;
  let final=''; rec.onresult=(e:any)=>{ for(let i=e.resultIndex;i<e.results.length;++i){ const t=e.results[i][0].transcript; if(e.results[i].isFinal) final+=t; } if(final) onResult(final); };
  return { start:()=>rec.start(), stop:()=>rec.stop(), supported:true };
}