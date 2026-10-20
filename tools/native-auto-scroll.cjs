const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const root=path.resolve(__dirname,'..'),version=JSON.parse(fs.readFileSync(path.join(root,'src/manifest.json'),'utf8')).versionName,out=path.join(root,'native-test-results/v'+version.replace(/\./g,'')),base='http://127.0.0.1:43131',log=path.resolve(root,'../atri-environment/emulator.log');
const sleep=ms=>new Promise(r=>setTimeout(r,ms)),logs=()=>fs.readFileSync(log,'utf8');
async function request(url){const r=await fetch(base+url);assert(r.ok,await r.clone().text());return r;}
async function wait(re,at){for(let i=0;i<200;i++){if(re.test(logs().slice(at)))return;await sleep(100);}throw Error('Timeout '+re);}
async function click(x,y,re){const at=logs().length;await request('/click?x='+x+'&y='+y);await sleep(250);if(re)await wait(re,at);}
(async()=>{
 const sha=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'dist/com.codex.atri.rw5.debug.'+version+'.rpk'))).digest('hex');assert(JSON.parse(fs.readFileSync(path.join(root,'reports/installed-script-check.json'),'utf8')).packageSha256===sha);
 const begin=logs().length;
 await click(216,323,/ATRI_RW5 frame b999:\*start 0/);await click(216,477,/ATRI_RW5 menu/);await click(216,182,/ATRI_RW5 frame b101:\*start 0/);
 for(let i=1;i<=28;i++)await click(370,477,new RegExp('ATRI_RW5 frame b101:\\*start '+i+'(?:\\s|$)'));
 await click(216,477,/ATRI_RW5 menu/);await click(216,228,/ATRI_RW5 auto enabled true/);await click(216,412);
 const at=logs().length;await request('/drag?x0=300&y0=440&x1=300&y1=350');await sleep(500);
 assert(!/ATRI_RW5 (?:frame|auto advance)/.test(logs().slice(at)),'Dragging advanced automatically');
 fs.writeFileSync(path.join(out,'auto-scrolled-dialogue.png'),Buffer.from(await(await request('/screen')).arrayBuffer()));
 await wait(/ATRI_RW5 auto advance b101:\*start 28/,at);await wait(/ATRI_RW5 frame b101:\*start 29/,at);
 await click(216,477,/ATRI_RW5 menu/);await click(216,228,/ATRI_RW5 auto enabled false/);await click(216,458,/ATRI_RW5 title ready/);
 assert(!/ATRI_RW5 error|ATRI_RW5 image failed|ASSERTION FAILED|PANIC!!!/.test(logs().slice(begin)));
 const report={passed:true,packageSha256:sha,realUIClicks:true,sceneInjection:false,dragDoesNotAdvance:true,automaticReadingResumesAfterActualScroll:true,physicalDeviceTested:false};
 fs.writeFileSync(path.join(out,'auto-scroll-report.json'),JSON.stringify(report,null,2));console.log('NATIVE_AUTO_SCROLL_PASS',JSON.stringify(report));
})().catch(e=>{console.error(e);process.exitCode=1;});
