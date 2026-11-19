import React, {useEffect, useLayoutEffect, useRef, useState} from "react";
import {createRoot} from "react-dom/client";
import {Player} from "@remotion/player";
import {Scene} from "./scenes";
import {chapters, motionFrames, stops} from "./story";

const prompts = [
  "开场先介绍论文题目和作者。点击画面进入研究背景，借双声源图向听众提问。",
  "先请听众指一指无人机、风机与阵列，再问：两个方向都有峰时，我们应该报告哪一个？风机只是讲解示意。",
  "可举一个反例：方向估计很准，但没有报警。请听众判断这个窗是否算联合成功。",
  "先让听众押一个候选。重排时请他们盯住 B，看它如何从第二行移动到第一行。24 个频带覆盖 300–7500 Hz。",
  "每个窗长 200 ms，同段录音中的窗彼此相关。200 米是采集位置，无法据此推出最大探测距离。",
  "逐项比较同一行的两条线。最后请听众指认哪一行改善最大，注意 95 分位描述的是误差分布尾部。",
  "提醒听众三次点击中分母始终是 600。54 是联合成功数的净增量，色块按类别排列，不对应逐窗配对轨迹。",
  "先让听众猜一猜，若再换一个排序器，理论上还有多少个失败窗能在这四个候选中选对？答案是 2 个。",
  "带回开场的问题。然后区分两类错误：候选里有目标，排序可能纠正；候选都超差，排序无法补回。",
  "从当前研究的边界谈到环境适应性、动态声源测向和实时处理。最后留一点时间，让听众思考哪些条件最影响声音测向的可靠性。",
  "放映停在本页。",
];

function useMedia(query) {
  const [matches,setMatches]=useState(()=>matchMedia(query).matches);
  useEffect(()=>{
    const media=matchMedia(query);
    const change=()=>setMatches(media.matches);
    media.addEventListener("change",change);
    return ()=>media.removeEventListener("change",change);
  },[query]);
  return matches;
}

function Talk() {
  const [index,setIndex]=useState(0), [replay,setReplay]=useState(0);
  const [review,setReview]=useState(false), [panel,setPanel]=useState(null);
  const [full,setFull]=useState(false), [message,setMessage]=useState("");
  const canvas=useRef(null), dialog=useRef(null), shell=useRef(null);
  const player=useRef(null);
  const portrait=useMedia("(orientation: portrait) and (max-width: 1000px)");
  const reduce=useMedia("(prefers-reduced-motion: reduce)");
  const {page,step,label}=stops[index], chapter=chapters[page];
  const last=index===stops.length-1;
  function move(delta) {
    if ((delta<0 && index===0) || (delta>0 && last)) return;
    setReview(delta<0);
    setIndex(i=>Math.max(0,Math.min(stops.length-1,i+delta)));
    canvas.current?.focus({preventScroll:true});
  }
  function jump(target) {
    setReview(false);
    setIndex(target);
    setReplay(n=>n+1);
    if (dialog.current?.open) dialog.current.close();
    canvas.current?.focus({preventScroll:true});
  }
  function openPanel(name) {
    setPanel(name);
    if (!dialog.current.open) dialog.current.showModal();
  }
  async function fullscreen() {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await shell.current.requestFullscreen();
      setMessage("");
    } catch {setMessage("浏览器未进入全屏，可使用浏览器的全屏命令。");}
    canvas.current?.focus({preventScroll:true});
  }
  useEffect(()=>{
    const sync=()=>setFull(Boolean(document.fullscreenElement));
    document.addEventListener("fullscreenchange",sync);
    return ()=>document.removeEventListener("fullscreenchange",sync);
  },[]);
  useEffect(()=>{
    function onKey(e) {
      if(e.altKey||e.ctrlKey||e.metaKey||e.isComposing) return;
      const k=e.key.toLowerCase();
      if(dialog.current.open) {
        if((k==="m" && panel==="menu") || (k==="n" && panel==="notes")) dialog.current.close();
        return;
      }
      if(e.target.closest?.("button:not(.canvas-action)") && (k===" "||k==="enter")) return;
      const actions={
        " ":()=>move(1), enter:()=>move(1), arrowright:()=>move(1), pagedown:()=>move(1),
        arrowleft:()=>move(-1), pageup:()=>move(-1), backspace:()=>move(-1),
        home:()=>jump(0),end:()=>jump(stops.length-1),r:()=>jump(index),
        m:()=>openPanel("menu"),n:()=>openPanel("notes"),f:fullscreen,
      };
      if(actions[k]) {e.preventDefault(); if(!e.repeat) actions[k]();}
    }
    window.addEventListener("keydown",onKey);
    return ()=>window.removeEventListener("keydown",onKey);
  });
  const still=reduce||review;
  useLayoutEffect(()=>{
    const view=player.current;
    if (!view) return;
    view.pause();
    view.seekTo(still?motionFrames-1:0);
    if (!still) view.play();
  },[index,replay,still]);
  return <main className={`talk ${portrait?"narrow":""}`} ref={shell}>
    <div className="stage">
      <Player ref={player} component={Scene} inputProps={{page,step,portrait,settled:still}}
        compositionWidth={portrait?720:1280} compositionHeight={portrait?1140:720}
        durationInFrames={motionFrames} fps={30}
        numberOfSharedAudioTags={0} initiallyMuted controls={false} clickToPlay={false}
        spaceKeyToPlayOrPause={false} doubleClickToFullscreen={false} moveToBeginningWhenEnded={false}
        style={{width:"100%",height:"100%"}}/>
      <button ref={canvas} className="canvas-action" aria-label={last?"演讲已结束":"点击画布继续讲解"} aria-disabled={last} onClick={()=>move(1)}/>
    </div>
    <nav className="tools" aria-label="放映工具">
      <div className="status" aria-live="polite"><b>{chapter.nav}</b> <span>{step+1} / {chapter.steps.length}</span>
        <i aria-hidden="true">{chapter.steps.map((_,i)=><s key={i} className={i<=step?"on":""}/>)}</i></div>
      <span className="hint">{message || (last?"放映结束":step===chapter.steps.length-1
        ? `${page===0?"":"再"}${portrait?"轻触":"单击"}进入「${chapters[page+1].nav}」` : (portrait?"轻触画面继续":"单击画面或按空格继续"))}</span>
      <div className="tool-buttons">
        <button onClick={()=>move(-1)} disabled={index===0} title="回退一步（←）">回退</button>
        <button onClick={()=>openPanel("menu")} title="章节目录（M）">目录</button>
        <button onClick={()=>openPanel("notes")} title="讲解提示（N）">提示</button>
        {document.fullscreenEnabled && <button onClick={fullscreen} title="投影全屏（F）">{full?"退出全屏":"全屏"}</button>}
      </div>
    </nav>
    <dialog ref={dialog} aria-labelledby="dialog-title" onClose={()=>{
      // A queued close can arrive after another panel has already opened.
      if (dialog.current?.open) return;
      setPanel(null);
      canvas.current?.focus({preventScroll:true});
    }}>
      <header><h2 id="dialog-title">{panel==="menu"?"章节目录":"讲解提示"}</h2>
        <button onClick={()=>dialog.current.close()}>关闭</button></header>
      {panel==="menu" ? <div className="directory">{chapters.map((c,i)=><button key={c.nav} aria-current={page===i?"step":undefined}
        onClick={()=>jump(stops.findIndex(s=>s.page===i))}><small>{String(i+1).padStart(2,"0")}</small>{c.nav}</button>)}</div>
        : panel==="notes" ? <section className="notes"><b>{chapter.nav} · {label}</b><p>{prompts[page]}</p>
          <button className="replay" onClick={()=>jump(index)}>重播本步</button>
          <small>空格继续　← 回退　R 重播　M 目录　N 提示　F 全屏　Home / End 首尾</small></section>:null}
    </dialog>
  </main>;
}
createRoot(document.getElementById("root")).render(<Talk/>);
