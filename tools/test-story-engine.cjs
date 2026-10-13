'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),g=JSON.parse(fs.readFileSync(path.join(root,'converted/graph.json'),'utf8')),e=require('../runtime/story-engine.cjs');
function run(useSkip,choices){
  const state=e.create(g),seen=[],files=new Map();let frame=e.locate(g,state),count=0,pick=0;
  while(frame.type!=='end'){
    assert(++count<15000,'Infinite story');
    if(frame.type==='text'){
      if(!files.has(frame.file)){const original=path.join(root,'converted/story',frame.file),source=path.join(root,'src/common/story',frame.file.replace(/\.json$/,'.txt'));files.set(frame.file,JSON.parse(fs.readFileSync(fs.existsSync(original)?original:source,'utf8')));}
      assert(files.get(frame.file)[frame.index]);
      frame=useSkip?e.skipChapter(g,state):e.advance(g,state);
    }else{
      seen.push(frame.items.filter(x=>!x.disabled).map(x=>x.text));
      const requested=choices[pick++];const selected=frame.items.findIndex(x=>!x.disabled&&x.text===requested);assert(selected>=0,JSON.stringify({requested,items:frame.items}));
      const before=JSON.stringify(e.checkpoint(state));assert.equal(e.skipChapter(g,state).type,'choice');assert.equal(JSON.stringify(e.checkpoint(state)),before);
      const disabled=frame.items.findIndex(x=>x.disabled);if(disabled>=0){e.choose(g,state,disabled);assert.equal(JSON.stringify(e.checkpoint(state)),before);}
      frame=e.choose(g,state,selected);
    }
  }
  return {flag:state.flag,progress:state.progress,seen,iterations:count};
}
const cases=[['亚托莉先放在我这','吻她','捡起鞋子'],['亚托莉先放在我这','吻她','放着不管'],['把亚托莉交出去','吻她','放着不管'],['亚托莉先放在我这','静静地看她','放着不管'],['把亚托莉交出去','静静地看她','放着不管']];
const report=[];
for(const choices of cases){const normal=run(false,choices),skip=run(true,choices);assert.deepEqual(skip.progress,normal.progress);assert.deepEqual(skip.seen,normal.seen);assert.equal(skip.flag,normal.flag);report.push({choices,normalSteps:normal.iterations,skipSteps:skip.iterations});}
const state=e.create(g);e.advance(g,state);const saved=e.checkpoint(state);assert.deepEqual(e.checkpoint(e.restore(g,saved)),saved);e.previous(g,state);assert.equal(state.index,0);
assert(!e.startTrue(g,state));state.progress.b501=true;assert(!e.startTrue(g,state));state.progress.b601=true;assert(e.startTrue(g,state));assert.equal(e.locate(g,state).chapter,'b701');
fs.writeFileSync(path.join(root,'reports/runtime-check.json'),JSON.stringify({passed:true,cases:report,note:'Pure JavaScript engine, not device performance or UI validation.'},null,2));
console.log('PASS: sequential/skip parity for all 5 routes, disabled choices, save roundtrip, previous, true-ending unlock.');
