// Real clicks in the official Vela emulator, with no artificial scene injection.
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),version=JSON.parse(fs.readFileSync(path.join(root,'src/manifest.json'),'utf8')).versionName,out=path.join(root,'native-test-results/v'+version.replace(/\./g,'')),base='http://127.0.0.1:43131';
const log=path.resolve(root,'../atri-environment/emulator.log');
const sleep=ms=>new Promise(r=>setTimeout(r,ms)),logs=()=>fs.readFileSync(log,'utf8');
const literal=text=>String(text).replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const request=async endpoint=>{const r=await fetch(base+endpoint);assert.ok(r.ok,await r.clone().text());return r;};
async function wait(at,pattern){for(let i=0;i<120;i++){const s=logs().slice(at);if(pattern.test(s))return s;await sleep(200);}throw Error('Timeout '+pattern);}
async function click(x,y){await request('/click?x='+x+'&y='+y);await sleep(650);}
async function expected(x,y,re){const at=logs().length;await click(x,y);return wait(at,re);}
async function shot(name){await sleep(700);fs.writeFileSync(path.join(out,name+'.png'),Buffer.from(await(await request('/screen')).arrayBuffer()));}
async function ready(){const at=Math.max(0,logs().lastIndexOf('NuttShell (NSH)'));await wait(at,/ATRI_RW5 title ready/);await wait(at,/Page show page_info:name:pages\/index/);await sleep(1800);}
async function menu(){await expected(216,477,/ATRI_RW5 menu/);await sleep(250);}
async function title(){await menu();await sleep(1100);await expected(216,443,/ATRI_RW5 title ready/);}
async function skip(){await menu();const at=logs().length,start=Date.now();await click(216,211);const text=await wait(at,/ATRI_RW5 (?:frame|choice|ending)/);return {text,ms:Date.now()-start};}
async function slot(index,re){for(let n=0;n<Math.floor(index/4);n++)await click(360,477);return expected(216,123+(index%4)*92,re);}
async function confirmY(){
  // The preview changes the dialog's height. Read actual button bounds instead
  // of reusing a coordinate that can land on Cancel for shorter previews.
  const {createRequire}=require('module');let toolkit=process.env.WATCH_COMPAT_TOOLKIT||path.join(root,'tools/compat-toolkit/node_modules/aiot-toolkit');if(!fs.existsSync(path.join(toolkit,'package.json')))toolkit=path.resolve(root,'../legacy-toolkit/node_modules/aiot-toolkit');
  const sharp=createRequire(path.join(toolkit,'package.json'))('sharp'),raw=Buffer.from(await(await request('/screen')).arrayBuffer());
  const {data,info}=await sharp(raw).ensureAlpha().raw().toBuffer({resolveWithObject:true});let start=-1,ranges=[];
  for(let y=65;y<490;y++){const at=(y*info.width+60)*info.channels,match=Math.abs(data[at]-223)<10&&Math.abs(data[at+1]-237)<10&&Math.abs(data[at+2]-246)<10;if(match&&start<0)start=y;if(!match&&start>=0){if(y-start>25)ranges.push([start,y]);start=-1;}}
  assert.equal(ranges.length,2,'Expected exactly two overwrite-dialog buttons');return Math.round((ranges[0][0]+ranges[0][1])/2);
}
async function save(index){await menu();await expected(216,95,/ATRI_RW5 slots ready save/);let result=await slot(index,new RegExp('ATRI_RW5 (?:slot saved|overwrite) '+(index+1)+'(?:\\s|$)'));if(result.includes('ATRI_RW5 overwrite'))result=await expected(216,await confirmY(),new RegExp('ATRI_RW5 slot saved '+(index+1)+' '));await sleep(400);return result.match(new RegExp('ATRI_RW5 slot saved '+(index+1)+' (\\S+) (\\d+)')).slice(1);}
async function prepare(){
  await ready();await shot('title');await expected(216,323,/ATRI_RW5 frame b999:\*start 0/);
  await expected(180,395,/ATRI_RW5 frame b999:\*start 1/);await shot('tap-advance');
  const positions=[];
  for(let i=0;i<30;i++){await expected(370,477,/ATRI_RW5 frame/);positions.push(await save(i));if(i%5===4)console.log('SAVED',i+1);}
  assert.equal(new Set(positions.map(x=>x.join(':'))).size,30);
  fs.writeFileSync(path.join(out,'save-preparation.json'),JSON.stringify({positions},null,2));await sleep(1600);await title();console.log('PREPARE_PASS');
}
async function verify(){
  const installed=JSON.parse(fs.readFileSync(path.join(root,'reports/installed-script-check.json'),'utf8'));assert(installed.installedScriptMatchesPackage);assert.equal(installed.packageSha256,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'dist/com.codex.atri.rw5.debug.'+version+'.rpk'))).digest('hex'));
  await ready();const begin=logs().length;const status=await(await request('/status')).json();
  for(const [k,v] of Object.entries({'hw.lcd.width':'432','hw.lcd.height':'514','hw.ramSize':'128'}))assert.equal(status.hardware[k],v);
  if(!process.argv.includes('--routes')){
  const saved=JSON.parse(fs.readFileSync(path.join(out,'save-preparation.json'),'utf8'));
  await expected(216,369,/ATRI_RW5 slots ready load/);
  for(let i=29;i>=0;i--){if(i!==29){await menu();await expected(216,153,/ATRI_RW5 slots ready load/);}await slot(i,new RegExp('ATRI_RW5 slot loaded '+(i+1)+' '+literal(saved.positions[i].join(' '))+'(?:\\s|$)'));if(i%5===0)console.log('COLD_LOADED',30-i);}
  await title();
  await click(216,415);await sleep(650);await shot('cg-list');await expected(100,160,/ATRI_RW5 cg 0 0/);await expected(216,200,/ATRI_RW5 cg 0 1/);await shot('cg-variant');await click(216,487);await expected(216,477,/ATRI_RW5 title ready/);
  fs.writeFileSync(path.join(out,'cold-ui-check.json'),JSON.stringify({passed:true,coldBoot30Slots:true,packageSha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'dist/com.codex.atri.rw5.debug.'+version+'.rpk'))).digest('hex')},null,2));
  }else{const completed=JSON.parse(fs.readFileSync(path.join(out,'cold-ui-check.json'),'utf8'));assert(completed.passed&&completed.coldBoot30Slots);assert.equal(completed.packageSha256,crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'dist/com.codex.atri.rw5.debug.'+version+'.rpk'))).digest('hex'));}
  const routeChoices=[[1,1,0],[1,1,1],[0,1,1],[1,0,1],[0,0,1]],routeResults=[],latencies=[];
  for(let route=0;route<routeChoices.length;route++){
    await expected(216,323,/ATRI_RW5 frame b999:\*start 0/);let selected=0,ended=false;
    for(let i=0;i<50;i++){
      const next=await skip();latencies.push(next.ms);
      if(next.text.includes('ATRI_RW5 choice')){
        const match=next.text.match(/ATRI_RW5 choice (\S+) (\d+)/);assert(match);
        if(route===0){await shot('choice-'+selected);const unchanged=await skip();assert.match(unchanged.text,/ATRI_RW5 choice/);}
        await expected(216,83+routeChoices[route][selected]*74,/ATRI_RW5 frame/);selected++;
      }else if(next.text.includes('ATRI_RW5 ending')){
        const end=next.text.match(/ATRI_RW5 ending (\d+) (\{[^\r\n]*\})/);assert(end);const progress=JSON.parse(end[2]);
        if(route===0){assert(progress.b501);assert.equal(Number(end[1]),11);}else{assert(progress.b601);assert.notEqual(Number(end[1]),11);}
        routeResults.push({route,choices:selected,flag:Number(end[1])});await shot('ending-'+route);await expected(216,382,/ATRI_RW5 title ready/);ended=true;break;
      }
      if(route===0&&i===1)await shot('portrait');
    }
    assert(ended&&selected===3,'Route did not end');console.log('NATIVE_ROUTE_PASS',route);
  }
  await shot('true-unlocked');await expected(216,277,/ATRI_RW5 frame b701:\*start 0/);const trueEnd=await skip();assert.match(trueEnd.text,/ATRI_RW5 ending/);assert.match(trueEnd.text,/"allClear":true/);await shot('true-ending');await expected(216,382,/ATRI_RW5 title ready/);
  assert(!/ATRI_RW5 error|ATRI_RW5 image failed|ASSERTION FAILED|PANIC!!!/.test(logs().slice(begin)));
  const file=path.join(root,'dist/com.codex.atri.rw5.debug.'+version+'.rpk');
  const report={result:'passed',runtime:'official vela-watch-5.0 emulator; not physical REDMI Watch 5 firmware',screen:[432,514],emulatorRAMMB:128,packageBytes:fs.statSync(file).size,packageSha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),physicalDeviceTested:false,coldBoot30Slots:true,routes:routeResults,trueEndingReached:true,skipLatencyMs:{maximum:Math.max(...latencies),median:latencies.sort((a,b)=>a-b)[Math.floor(latencies.length/2)]},checks:['tap dialogue advances','30 distinct save slots restored after cold boot','CG variants cycle','5 reachable normal-play choice paths and true ending','skip stops at choices','no runtime or image failures during checks']};
  const extraPath=path.join(out,'extra-report.json');if(fs.existsSync(extraPath)){const extra=JSON.parse(fs.readFileSync(extraPath,'utf8'));if(extra.passed&&extra.packageSha256===report.packageSha256){Object.assign(report,extra,{result:'passed'});report.checks.push('dialogue scroll shows previously clipped content','large font rendering','portrait head/torso with lower edge aligned');}}
  fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log('NATIVE_PASS',JSON.stringify(report));
}
(process.argv.includes('--prepare')?prepare():verify()).catch(e=>{console.error(e);process.exitCode=1;});
