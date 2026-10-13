// Exercise actual page initialization/progress handling with fresh and old data.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert/strict');
const root=path.resolve(__dirname,'..'),graph=JSON.parse(fs.readFileSync(path.join(root,'converted/graph.json'),'utf8')),engine=require('../runtime/story-engine.cjs');
function page(progress){
 const code=fs.readFileSync(path.join(root,'tools/ui-script.txt'),'utf8').replace(/<\/?script>/g,'').replace(/^import .*;\r?\n/gm,'').replace('export default','module.exports=');
 const context={module:{exports:{}},file:{},prompt:{showToast(){}},storage:{get(o){o.success(o.key.endsWith('progress_v1')?JSON.stringify(progress):'');},set(o){o.success();}},graph,...engine,enterTrue:engine.startTrue,console:{log(){},error(){}},setTimeout,clearTimeout};vm.runInNewContext(code,context);const page=context.module.exports;Object.assign(page,page.private);page.onInit();return page;
}
assert.equal(page({}).trueUnlocked,false);
assert.equal(page({b501:true}).trueUnlocked,false);
assert.equal(page({b601:true}).trueUnlocked,false);
const complete=page({b501:true,b601:true});assert.equal(complete.trueUnlocked,true);
const fresh=page({});fresh.mode='play';fresh.session.progress={b501:true,b601:true};fresh.syncProgress();assert.equal(fresh.trueUnlocked,true);fresh.toTitle();assert.equal(fresh.mode,'title');
const template=fs.readFileSync(path.join(root,'tools/ui-template.txt'),'utf8');assert(template.includes('if="{{trueUnlocked}}"'));assert(template.indexOf('onclick="startTrue"')<template.indexOf('onclick="startNew"'));
assert(!template.includes('openRoutes')&&!template.includes("mode === 'chapters'"));
let exited=false;complete.$app={exit(){exited=true;}};complete.exitApplication();assert(exited);
const report={passed:true,freshTitleHidesTrueEnd:true,originalGoodAndBadUnlockPreserved:true,completedMainProgressShowsTrueEndOnReturn:true,oldProgressLoads:true};fs.writeFileSync(path.join(root,'reports/title-ui-check.json'),JSON.stringify(report,null,2));console.log('TITLE_UI_PASS',report);
