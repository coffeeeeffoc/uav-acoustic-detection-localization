import React from "react";
import {Composition, Series, registerRoot} from "remotion";
import {Scene} from "./scenes";
import {chapters, stops} from "./story";

// Each stop has the same entrance as the live presentation and a reading hold.
const framesPerStop=90;
function Walkthrough() {
  return <Series>{stops.map(({page,step,label})=>
    <Series.Sequence key={page+"-"+step} name={chapters[page].nav+" · "+label} durationInFrames={framesPerStop}>
      <Scene page={page} step={step}/>
    </Series.Sequence>)}</Series>;
}
function Root() {
  return <Composition id="AcousticsTalk" component={Walkthrough} width={1280} height={720}
    fps={30} durationInFrames={stops.length*framesPerStop}/>;
}
registerRoot(Root);
