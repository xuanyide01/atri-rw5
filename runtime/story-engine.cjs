'use strict';
// Pure bounded state machine. The UI loads only the chunk returned by locate().
function matches(test,flag){return !test||(test[0]==='=='?flag===test[1]:flag!==test[1]);}
function clone(v){return JSON.parse(JSON.stringify(v));}
function create(graph,progress){return {format:1,node:graph.initial,index:0,flag:0,progress:clone(progress||{}),history:[]};}
function checkpoint(state){const {history,...saved}=state;return clone(saved);}
function restore(graph,saved){
  if(!saved||saved.format!==1||!graph.nodes[saved.node]||!Number.isInteger(saved.index)||saved.index<0||saved.index>graph.nodes[saved.node].count||!Number.isInteger(saved.flag))throw Error('Invalid ATRI save');
  return {...clone(saved),progress:clone(saved.progress||{}),history:[]};
}
function remember(state){state.history.push(checkpoint(state));if(state.history.length>24)state.history.shift();}
function locate(graph,state){
  for(let steps=0;steps<100;steps++){
    if(state.node==='@title')return {type:'end'};
    const node=graph.nodes[state.node];if(!node)throw Error('Unknown story node '+state.node);
    if(state.index<node.count){
      let offset=state.index;
      for(const chunk of node.chunks){if(offset<chunk.count)return {type:'text',file:chunk.file,index:offset,chapter:node.chapter,title:node.title};offset-=chunk.count;}
      throw Error('Broken chunk index');
    }
    for(const id of node.complete)state.progress[id]=true;
    if(node.allClear)state.progress.allClear=true;
    if(node.choices.length)return {type:'choice',items:node.choices.filter(x=>matches(x.when,state.flag))};
    const next=node.next.find(x=>matches(x.when,state.flag));if(!next)throw Error('Unexpected story end');
    state.node=next.to;state.index=0;
  }
  throw Error('Story transition limit exceeded');
}
function advance(graph,state){const current=locate(graph,state);if(current.type!=='text')return current;remember(state);state.index++;return locate(graph,state);}
function choose(graph,state,index){
  const current=locate(graph,state);if(current.type!=='choice')throw Error('No active choice');
  const option=current.items[index];if(!option||option.disabled||!option.to)return current;
  remember(state);if(option.effect)state.flag=option.effect[0]==='set'?option.effect[1]:state.flag+option.effect[1];
  state.node=option.to;state.index=0;return locate(graph,state);
}
function skipChapter(graph,state){
  const initial=locate(graph,state);if(initial.type!=='text')return initial;
  remember(state);const chapter=initial.chapter;
  // Jump over text counts, not text records. Every branch and completion remains active.
  for(let steps=0;steps<100;steps++){
    state.index=graph.nodes[state.node].count;
    const next=locate(graph,state);
    if(next.type!=='text'||next.chapter!==chapter)return next;
  }
  throw Error('Chapter skip transition limit exceeded');
}
function previous(graph,state){if(!state.history.length)return locate(graph,state);const history=state.history;const saved=history.pop();Object.assign(state,saved,{history});return locate(graph,state);}
function trueAvailable(graph,state){return graph.trueRequires.every(id=>!!state.progress[id]);}
function startTrue(graph,state){if(!trueAvailable(graph,state))return false;remember(state);state.node=graph.trueEnding;state.index=0;state.flag=0;return true;}
module.exports={create,checkpoint,restore,locate,advance,choose,skipChapter,previous,trueAvailable,startTrue};
