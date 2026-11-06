'use strict';
// Execute the actual page methods with a deterministic clock and real engine.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..'),graph=JSON.parse(fs.readFileSync(path.join(root,'src/common/graph.js'),'utf8').replace(/^export const graph=/,'').trim().replace(/;$/,'')),engine=require('../runtime/story-engine.cjs');
const page=fs.readFileSync(path.join(root,'tools/ui-script.txt'),'utf8').replace(/<\/?script>/g,'').replace(/^import .*;\r?\n/gm,'').replace('export default','globalThis.page =');
const helper=fs.readFileSync(path.join(root,'src/common/auto-reader.js'),'utf8').replace(/export /g,'');
const passed=[];
function model(settings={}){
 let now=0,id=0;const timers=new Map(),saved=new Map([['atri_rw5_settings_v1',JSON.stringify(settings)]]),messages=[];
 const clock={setTimeout(fn,delay){const key=++id;timers.set(key,{fn,at:now+Number(delay)});return key;},clearTimeout(key){timers.delete(key);}};
 const deletes=[];
 const storage={get(args){args.success(saved.get(args.key)||args.default||'');if(args.complete)args.complete();},set(args){if(args.value===''){deletes.push(args);return;}saved.set(args.key,args.value);if(args.success)args.success();if(args.complete)args.complete();}};
 const file={readText(args){clock.setTimeout(()=>args.success({text:fs.readFileSync(path.join(root,'src',args.uri),'utf8')}),2);}};
 const sandbox={...engine,startTrue:undefined,enterTrue:engine.startTrue,graph,storage,file,prompt:{showToast(){}},console:{log:(...x)=>messages.push(x.join(' ')),error(){}},...clock};
 vm.runInNewContext(helper+'\n'+page,sandbox);
 const component=sandbox.page,ui=Object.assign({},JSON.parse(JSON.stringify(component.private)));
 for(const [key,value] of Object.entries(component))if(typeof value==='function')ui[key]=value.bind(ui);
 ui.$element=()=>({scrollTo(){}});ui.$app={exit(){ui.onDestroy();}};ui.onInit();
 function tick(ms){const end=now+ms;let steps=0;while(true){const entry=[...timers].filter(([,t])=>t.at<=end).sort((a,b)=>a[1].at-b[1].at||a[0]-b[0])[0];if(!entry)break;assert(++steps<50000,'Timer loop');now=entry[1].at;timers.delete(entry[0]);entry[1].fn();}now=end;}
 function line(text='自动播放测试'){ui.startNew();tick(2);ui.clearTyping();ui.showFrame({speaker:'亚托莉',text,art:{background:'',sprites:[]}});}
 return {ui,tick,timers,saved,messages,line,deletes,wait:sandbox.autoWait};
}
function test(name,run){run();passed.push(name);}
test('three speeds and bounded extra time for long paragraphs',()=>{const m=model();assert.equal(m.wait(0,20),2600);assert.equal(m.wait(1,20),1500);assert.equal(m.wait(2,20),800);assert.equal(m.wait(1,61),1555);assert.equal(m.wait(1,10000),6500);});
test('auto remains off at boot; only speed persists; old settings compatible',()=>{const m=model({fontSize:28,textSpeed:0,autoSpeed:2,autoEnabled:true});assert(!m.ui.autoEnabled);assert.equal(m.ui.autoSpeed,2);m.ui.cycleAutoSpeed();const settings=JSON.parse(m.saved.get('atri_rw5_settings_v1'));assert.equal(settings.autoSpeed,0);assert(!('autoEnabled' in settings));assert.equal(model({fontSize:24,textSpeed:0}).ui.autoSpeed,1);});
test('wait starts after final glyph; manual completion restarts the whole wait',()=>{const m=model(),u=m.ui;m.line();u.showMenu();u.toggleAuto();u.resume();u.clearTyping();u.showFrame({speaker:'',text:'12345',art:{background:'',sprites:[]}});const before=u.session.index;m.tick(119);assert.equal(u.displayText,'1234');assert.equal(u.session.index,before);m.tick(1);assert.equal(u.displayText,'12345');m.tick(1499);assert.equal(u.session.index,before);m.tick(1);assert.equal(u.session.index,before+1);assert(u.displayText.length<u.fullText.length);u.advance();assert.equal(u.displayText,u.fullText);const index=u.session.index;m.tick(1499);assert.equal(u.session.index,index);m.tick(1);assert.equal(u.session.index,index+1);});
test('menus and save/load selection pause, then resume with a fresh timer',()=>{const m=model(),u=m.ui;m.line();u.showMenu();u.toggleAuto();u.resume();m.tick(700);u.showMenu();m.tick(10000);assert.equal(u.session.index,0);u.resume();m.tick(1499);assert.equal(u.session.index,0);u.openSlots('load');m.tick(10000);assert.equal(u.mode,'slots');assert.equal(u.session.index,0);u.closeSlots();m.tick(1499);assert.equal(u.session.index,0);m.tick(1);assert.equal(u.session.index,1);});
test('choices never auto-select; manual selection resumes typing and auto',()=>{const m=model(),u=m.ui;m.line();u.autoEnabled=true;const node=Object.entries(graph.nodes).find(([,n])=>n.choices.length);u.session.node=node[0];u.session.index=node[1].count;u.session.flag=0;u.renderFrame();assert.equal(u.mode,'choice');const before=JSON.stringify(u.session);m.tick(60000);assert.equal(JSON.stringify(u.session),before);assert(u.autoEnabled);const pick=u.options.findIndex(x=>!x.disabled);assert(pick>=0);u.pick(pick);m.tick(2);assert.equal(u.mode,'play');assert(u.autoEnabled);m.tick(u.fullText.length*30+m.wait(u.autoSpeed,u.fullText.length));assert(m.messages.some(x=>x.startsWith('ATRI_RW5 auto advance')));});
test('touch hold and drag suspend progression without treating scroll as click',()=>{const m=model(),u=m.ui;m.line('长段落'.repeat(40));u.autoEnabled=true;u.armAuto();u.dialogueTouchStart({touches:[{clientX:300,clientY:420}]});m.tick(20000);assert.equal(u.session.index,0);u.dialogueTouchMove({touches:[{clientX:300,clientY:340}]});u.dialogueTouchEnd();u.dialogueTap();assert.equal(u.session.index,0);u.dialogueScrolled();m.tick(m.wait(1,u.fullText.length)-1);assert.equal(u.session.index,0);m.tick(1);assert.equal(u.session.index,1);});
test('background suspends timers, foreground restarts reading wait',()=>{const m=model(),u=m.ui;m.line();u.autoEnabled=true;u.armAuto();m.tick(400);u.onHide();m.tick(60000);assert.equal(u.session.index,0);u.onShow();m.tick(1499);assert.equal(u.session.index,0);m.tick(1);assert.equal(u.session.index,1);});
test('previous, title, ending, error and destruction cancel automatic reading',()=>{for(const action of ['goBack','toTitle','fail','onDestroy','ending']){const m=model(),u=m.ui;m.line();u.autoEnabled=true;u.armAuto();if(action==='ending'){u.session.node='@title';u.renderFrame();}else u[action]('test');const before=JSON.stringify(u.session);m.tick(60000);assert(!u.autoEnabled,action);assert.equal(JSON.stringify(u.session),before,action);assert.equal(m.timers.size,0,action);}});
test('cancelled callbacks cannot advance even when delivered late',()=>{const m=model(),u=m.ui;m.line();u.autoEnabled=true;u.armAuto();const stale=m.timers.get(u._autoTimer).fn;u.showMenu();u.resume();stale();assert.equal(u.session.index,0);assert(u._autoTimer!==null);u.loading=true;m.tick(1500);assert.equal(u.session.index,0);});
test('save deletion requires a separate tap and cancellation preserves the slot',()=>{
 const m=model(),u=m.ui;m.line();
 u.openSlots('save');u.beginSlotHold(0);m.tick(650);u.selectSlot(0);
 assert.equal(u.mode,'slots');assert(!m.saved.has('atri_rw5_slot_v1_1'));
 u.beginSlotTouch();u.selectSlot(0);
 const before=m.saved.get('atri_rw5_slot_v1_1');
 u.openSlots('load');
 const touch=(clientY)=>({touches:[{clientX:100,clientY}]});
 u.beginSlotHold(0,touch(100));u.moveSlotHold(touch(140));m.tick(650);u.selectSlot(0);
 assert.equal(u.mode,'slots','drag does not load or open the dialog');
 u.beginSlotHold(0,touch(100));m.tick(649);assert.equal(u.mode,'slots');m.tick(1);u.selectSlot(0);
 assert.equal(u.mode,'deleteSlot');assert.equal(u.deleteSlotTitle,'删除存档 01？');
 u.confirmDeleteSlot();assert.equal(m.deletes.length,0,'hold release cannot confirm');
 u.cancelDeleteSlot();assert.equal(u.mode,'slots');assert.equal(m.saved.get('atri_rw5_slot_v1_1'),before);
 u.beginSlotTouch();u.selectSlot(0);m.tick(2);assert.equal(u.mode,'play');
});

test('delete failure can retry and clears only one slot on the last page',()=>{
 const m=model(),u=m.ui;m.line();
 for(const index of [28,29]){u.openSlots('save');for(let i=0;i<7;i++)u.nextSlotPage();u.selectSlot(index);}
 const key='atri_rw5_slot_v1_30',neighbor=m.saved.get('atri_rw5_slot_v1_29'),original=m.saved.get(key);
 m.saved.set('atri_rw5_settings_v1','{"autoSpeed":2}');m.saved.set('atri_rw5_progress_v1','{"good":true}');
 u.openSlots('save');for(let i=0;i<7;i++)u.nextSlotPage();
 u.requestDeleteSlot(29);u.beginSlotTouch();u.confirmDeleteSlot();u.confirmDeleteSlot();u.cancelDeleteSlot();
 assert.equal(m.deletes.length,1);assert.equal(m.deletes[0].key,key);assert.equal(u.mode,'deleteSlot');
 m.deletes[0].fail();assert.equal(m.saved.get(key),original);assert.equal(u.mode,'deleteSlot');assert(!u.storageBusy);
 u.beginSlotTouch();u.confirmDeleteSlot();assert.equal(m.deletes.length,2);
 m.saved.delete(key);m.deletes[1].success();assert.equal(u.mode,'slots');assert.equal(u.slotPage,7);
 assert.equal(u.slotRows[1].meta,'空栏位');assert.equal(u.slotRows[1].preview,'');
 assert.equal(m.saved.get('atri_rw5_slot_v1_29'),neighbor);
 assert.equal(m.saved.get('atri_rw5_settings_v1'),'{"autoSpeed":2}');assert.equal(m.saved.get('atri_rw5_progress_v1'),'{"good":true}');
 u.closeSlots();u.openSlots('load');for(let i=0;i<7;i++)u.nextSlotPage();
 u.selectSlot(29);assert.equal(u.mode,'slots');assert(!m.saved.has(key));
 u.closeSlots();u.openSlots('save');for(let i=0;i<7;i++)u.nextSlotPage();
 u.selectSlot(29);assert(m.saved.has(key));assert.equal(u.mode,'play');
});

test('unreadable slot payload can still be deleted without touching other keys',()=>{
 const m=model(),u=m.ui,key='atri_rw5_slot_v1_1';
 m.saved.set(key,'{broken');
 u.openSlots('load');assert(u.slotRows[0].occupied);
 u.requestDeleteSlot(0);u.beginSlotTouch();u.confirmDeleteSlot();
 assert.equal(m.deletes[0].key,key);m.saved.delete(key);m.deletes[0].success();
 assert(!u.slotRows[0].occupied);
});
const report={passed:true,tests:passed.length,cases:passed,actualPageMethods:true,deterministicClock:true,choiceFixturesOnlyInUnitTests:true};
fs.writeFileSync(path.join(root,'reports/auto-reader-unit.json'),JSON.stringify(report,null,2));console.log('AUTO_READER_UNIT_PASS',JSON.stringify(report));
