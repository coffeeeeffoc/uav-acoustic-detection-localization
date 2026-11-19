import React from "react";
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from "remotion";
import cover from "./cover.jpg";
import twoSources from "./two-sources.jpg";
import {chapters} from "./story";
import "./talk.css";

const blue = "#185cc4", ink = "#123452", sky = "#88a8c5", pale = "#d8e4ef";
const clamp = n => Math.max(0, Math.min(1, n));

function Sources({step, p, recap = false}) {
  const fan = !recap && step === 1;
  const routes = [[132, 111, "B  无人机"], [466, 245, "A  风机"]];
  return <figure className="sources">
    <img src={twoSources} alt="无人机在左上方，风机在右侧，声音传向下方的麦克风阵列。"/>
    <svg viewBox="0 0 600 400" aria-hidden="true">
      {routes.map(([x,y,label], i) => {
        const active = recap ? i === 0 : (step === 0 || i === 1);
        const color = i ? ink : blue;
        const endX = 245, endY = 298;
        return <g key={label} opacity={active ? 1 : 0.45}>
          <line x1={x} y1={y} x2={endX} y2={endY} stroke={color} strokeWidth={active ? 4 : 2} strokeDasharray="8 7"/>
          {active && [0,.18,.36].map(delay => {
            const t = clamp((p - delay) / .64);
            return <circle key={delay} cx={x+(endX-x)*t} cy={y+(endY-y)*t} r={8+3*t} fill={color} opacity={.9*Math.sin(Math.PI*t)}/>;
          })}
          <rect x={x-67} y={y-18} rx="5" width="134" height="37" fill={(fan && i === 1) || (recap && !i) ? color : "white"} stroke={color} strokeWidth="2"/>
          <text x={x} y={y+8} textAnchor="middle" fontSize="23" fontWeight="700" fill={(fan && i === 1) || (recap && !i) ? "white" : color}>{label}</text>
        </g>;
      })}
      <text x="250" y="385" textAnchor="middle" fill={ink} fontSize="22">麦克风阵列</text>
    </svg>
  </figure>;
}

function Decisions({step,p}) {
  return <div className="decision-list">
    <div><small>检测</small><strong>最高评分 &gt; 当地背景阈值</strong></div>
    {step > 0 && <><b className="join" style={{opacity:p}}>＋</b>
      <div style={{opacity:p,translate:`0 ${(1-p)*25}px`}}><small>测向</small><strong>方向偏差 ≤ 10°</strong></div>
      <div className="result-line" style={{scale:`${p} 1`}}>联合成功</div></>}
  </div>;
}

const rankNames = ["A　风机", "B　无人机", "C　候选", "D　候选"];
function Ranking({step,p}) {
  return <svg className="chart" viewBox="0 0 650 365" role="img" aria-label="四个候选保持身份，根据峰高或频带评分重新排序">
    <text x="2" y="27" className="chart-title">{step===2?"按频带评分重排":"按空间峰高排列"}</text>
    <text x="626" y="27" textAnchor="end" className="axis-label">{step ? "24 频带特征（示意）" : "候选方向（示意）"}</text>
    {rankNames.map((name,i) => <text key={name} x="5" y={92+i*70} className="rank-num">{String(i+1).padStart(2,"0")}</text>)}
    {rankNames.map((name,i) => {
      const target = [1,0,2,3][i];
      const pos = i + (target-i)*(step===2?p:0);
      const slide = step===2 && i<2 ? (i===0?1:-1)*18*Math.sin(Math.PI*p) : 0;
      const color = i===1?blue:ink;
      return <g key={name} data-rank={name[0]} transform={`translate(${slide},${pos*70})`}>
        <rect x="57" y="53" width="565" height="57" rx="6" fill={i===1?"#e3eeff":"#eff4f8"} stroke={i===1?blue:pale} strokeWidth={i===1?2:1}/>
        <text x="78" y="90" fontSize="26" fontWeight="700" fill={color}>{name}</text>
        {step===0 ? <rect x="303" y="76" rx="3" width={[284,243,164,102][i]*p} height="11" fill={i===1?blue:sky}/> :
          <g><line x1="302" x2="597" y1="82" y2="82" stroke={sky}/>{Array.from({length:24},(_,j)=>{
            const v = 6+14*Math.abs(Math.sin((j+2)*(i+.78)));
            const up = Math.cos(j*.65+i)>.1;
            const h = v*(step===1?clamp(p*1.4-j/60):1);
            return <rect key={j} x={303+j*12} y={up?82-h:82} width="8" height={h} fill={color}/>;
          })}</g>}
      </g>;
    })}
    <text x="58" y="353" className="axis-label">{["条长表示示意峰高","每个方向各有一组有符号的频带特征","相同的候选集合，第一名从 A 变为 B"][step]}</text>
  </svg>;
}

function Groups({step,p}) {
  return <div className="groups">{[100,150,200].slice(0,step+1).map((dist,i)=>
    <div key={dist} className={i?"held":"dev"} style={{opacity:i===step?.2+.8*p:1,translate:`${i===step?(1-p)*55:0}px 0`}}>
      <em>P{i+1}</em><strong>{dist}<small> m</small></strong>
      <span>{i?"保留评价":"方法开发"}<small>{i?"300 无人机窗 · 100 背景窗":"学习频带权重"}</small></span>
    </div>)}</div>;
}

const metrics = [
  ["均值",14.78,6.97],["中位数",3.49,3.47],["95 分位",96.87,54.16],
];
function Metrics({step,p}) {
  return <svg className="chart" viewBox="0 0 650 370" role="img" aria-label="SRP-PHAT 与 DCCR 角偏差，所有指标使用相同横轴">
    <Legend x={4} y={21} color={sky} label="SRP-PHAT"/><Legend x={194} y={21} color={blue} label="DCCR"/>
    {[0,25,50,75,100].map(v=><g key={v}><line x1={109+v*5.14} x2={109+v*5.14} y1="51" y2="320" stroke={pale}/><text x={109+v*5.14} y="350" textAnchor="middle" className="axis-label">{v}°</text></g>)}
    {metrics.slice(0,step+1).map(([name,a,b],i)=><g key={name}>
      <text x="4" y={81+i*92} className="row-title">{name}</text>
      {[a,b].map((v,j)=>{
        const length = v*5.14*(i===step?p:1);
        const y=55+i*92+j*32;
        const inside=length>433;
        return <g key={j}><rect data-bar={name+j} x="109" y={y} width={length} height="25" rx="3" fill={j?blue:sky}/>
          <text x={109+length+(inside?-9:8)} y={y+21} textAnchor={inside?"end":"start"} fontSize="22" fontWeight="700" fill={inside?ink:(j?blue:ink)}>{v.toFixed(2)}°</text></g>;
      })}
    </g>)}
  </svg>;
}
function Legend({x,y,color,label}) {
  return <g transform={`translate(${x},${y})`}><rect y="-15" width="16" height="16" rx="2" fill={color}/><text x="24" fontSize="22" fill={ink}>{label}</text></g>;
}

function Gate({step,p}) {
  const good = [0,459,513][step];
  const alarm = 514;
  return <svg className="chart" viewBox="0 0 650 372" role="img" aria-label="600 个无人机窗，按类别排列。514 个报警窗与 86 个漏检窗。">
    <text x="0" y="24" className="chart-title">{["600 个无人机窗","PHAT 峰高选向","DCCR 频带选向"][step]}</text>
    <text x="640" y="24" textAnchor="end" className="axis-label">{step?"固定 514 个报警 · 按类别排列":"每格 1 窗 · 按类别排列"}</text>
    {Array.from({length:600},(_,i)=>{
      const category = i>=alarm ? "miss" : i<good ? "success" : step ? "error" : "alarm";
      const col = i%40;
      const uniqueError = step===2 && category==="error";
      const highlighted = step ? category==="success" : category==="alarm";
      const sweep = highlighted ? clamp(1-Math.abs(col-(-5+49*p))/5) : 0;
      return <rect key={i} data-gate={category} x={col*16.15} y={48+Math.floor(i/40)*16.15}
        width="12.7" height="12.7" rx="2" fill={category==="success"?blue:category==="miss"?pale:ink}
        stroke={uniqueError?"#c75306":"#73d9ff"} strokeWidth={uniqueError?3.5:3.5*sweep}/>;
    })}
    {step ? <><Legend x={0} y={330} color={blue} label={`联合成功 ${good}`}/><Legend x={229} y={330} color={ink} label={`报警且超差 ${514-good}`}/></> :
      <Legend x={0} y={330} color={ink} label={`报警 ${alarm}`}/>}
    <Legend x={478} y={330} color={pale} label="漏检 86"/>
    {step===2 && <text x="0" y="363" className="axis-label">橙框标出唯一已报警但方向偏差超过 10° 的窗。</text>}
  </svg>;
}

function Errors({step,p}) {
  if(step===2) return <div className="record-errors"><span>按录音重新统计这 36 个窗</span>
    <strong>33 <small>/ 36</small></strong><div className="record-track"><i style={{width:`${100*33/36*p}%`}}/></div>
    <div className="record-labels"><b>P3 第 2 段　33 个</b><span>其余录音　3 个</span></div></div>;
  return <svg className="chart" viewBox="0 0 650 365" role="img" aria-label={step?"34 个窗缺少合格候选，2 个有合格候选却选错":"36 个偏差超过 10 度的窗"}>
    <text x="2" y="28" className="chart-title">{step?"按候选覆盖情况分组":"36 个超差窗"}</text>
    {Array.from({length:36},(_,i)=>{
      const x=24+(i%9)*53,y=77+Math.floor(i/9)*53;
      const toX=i<34?24+(i%9)*51:555;
      const toY=i<34?77+Math.floor(i/9)*52:108+(i-34)*56;
      const split=step?p:0;
      return <rect key={i} data-window={i} x={x+(toX-x)*split} y={y+(toY-y)*split} width="37" height="37" rx="5" fill={step && i<34 ? blue : ink} opacity={step?1:clamp(p*1.65-i/55)}/>;
    })}
    {step>0 && <g opacity={p}><line x1="505" x2="505" y1="66" y2="283" stroke={pale} strokeWidth="2"/>
      <text x="25" y="324" className="row-title">34 个 · 四峰均超差</text><text x="575" y="324" textAnchor="middle" className="row-title">2 个 · 选错</text></g>}
  </svg>;
}

const questions = [["不同机型与声环境","环境适应性"],["由静止到运动","动态声源测向"],["估计精度与响应速度","实时处理"]];
function Outlook({step,p}) {
  return <div className="outlook">{questions.slice(0,step+1).map(([a,b],i)=><div key={a} style={{opacity:i===step?.2+.8*p:1,translate:`${i===step?38*(1-p):0}px 0`}}>
    <b>{a}</b><span>→</span><strong>{b}</strong></div>)}</div>;
}

export function Scene({page=0,step=0,portrait=false,settled=false}) {
  const frame = useCurrentFrame();
  const p = settled?1:interpolate(frame,[0,45],[0,1],{extrapolateRight:"clamp",extrapolateLeft:"clamp",easing:Easing.inOut(Easing.quad)});
  const chapter=chapters[page], [,heading,detail]=chapter.steps[step];
  const {kind}=chapter;
  if(kind==="cover"){
    return <AbsoluteFill className={`scene title-slide ${portrait?"portrait":""}`} data-page={page} data-step={step}>
      <figure className="title-visual"><img src={cover} alt="飞行中的民用无人机"/><figcaption>概念配图</figcaption></figure>
      <div className="title-copy">
        <p className="affiliation">{chapter.source}</p>
        <h1>{chapter.title.replace("的无人机","的\n无人机")}</h1>
        <p className="authors">{detail}</p>
      </div>
    </AbsoluteFill>;
  }
  if(kind==="thanks"){
    return <AbsoluteFill className={`scene thanks ${portrait?"portrait":""}`} data-page={page} data-step={step}>
      <h1>{chapter.title}</h1>
    </AbsoluteFill>;
  }
  const graphics={sources:Sources,decisions:Decisions,ranking:Ranking,groups:Groups,metrics:Metrics,gate:Gate,errors:Errors,summary:Sources,outlook:Outlook};
  const Graphic=graphics[kind];
  return <AbsoluteFill className={`scene ${portrait?"portrait":""}`} data-page={page} data-step={step}>
    <div className="mast"><b>{chapter.section}</b><span>无人机声学探测与测向</span></div>
    <h1>{chapter.title}</h1>
    {(kind==="metrics" || kind==="gate") && <div className="reference-note"><b>角偏差参考</b>采集示意图中的静态标称方向，未同步跟踪无人机。</div>}
      <div className="body-grid">
        <div className="visual">
          {kind==="summary" && step===1 ? <div className="summary-chart">
            <span>方向偏差超过 10° 的窗数</span>
            <div><b>91</b><i>→</i><strong>36<span className="number-underline" style={{scale:`${p} 1`}}/></strong></div>
            <small>SRP-PHAT 峰高选向　／　DCCR 频带选向</small>
          </div>:<Graphic step={step} p={p} recap={kind==="summary"}/>}
        </div>
        <div className="reading" style={{opacity:.55+.45*p,translate:`0 ${(1-p)*10}px`}}>
          <div className="cue"><i/>{chapter.steps[step][0]}</div>
          <h2>{heading}</h2><p>{detail}</p>
        </div>
      </div>
    <footer className="source"><span>{chapter.source}</span><b>{String(page+1).padStart(2,"0")} / {chapters.length}</b></footer>
  </AbsoluteFill>;
}
