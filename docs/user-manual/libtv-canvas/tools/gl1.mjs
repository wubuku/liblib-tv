import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

// 故事板态下的「可写性」读数
const 读 = (标) => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  // 添加节点面板：列出面板里所有可选类型
  const 面板=[...document.querySelectorAll('div')].filter(e=>{
    const s=getComputedStyle(e), r=e.getBoundingClientRect(), t=(e.innerText||'');
    return r.width>=180&&r.width<=560&&r.height>=200&&r.height<=760
      &&(s.position==='fixed'||s.position==='absolute')&&+s.opacity>0.5
      &&/添加节点/.test(t)&&/视频/.test(t);})
    .sort((a,b)=>b.getBoundingClientRect().width-a.getBoundingClientRect().width)[0];
  const 抽屉=document.querySelector('.copilotKitChat');
  const 资产=document.querySelector('.mantine-Drawer-content,[class*="drawer" i]');
  return {标, 节点数:document.querySelectorAll('.react-flow__node').length,
    添加节点面板:面板?{框:R(面板), 项:(面板.innerText||'').trim().split('\n').filter(s=>s.trim()).slice(0,14)}:null,
    底栏加号:(()=>{const b=[...document.querySelectorAll('button')]
      .find(x=>(x.innerText||'').trim()==='添加节点'||x.getAttribute('aria-label')==='添加节点');
      return b?{框:R(b), 文字:(b.innerText||'').trim()}:null;})(),
    TV抽屉框:抽屉?R(抽屉):'无',
    任意抽屉:[...document.querySelectorAll('.mantine-Drawer-inner,.mantine-Drawer-content')]
      .map(e=>({cls:(e.className||'').toString().slice(0,40), 框:R(e),
        op:getComputedStyle(e).opacity, 文字:(e.innerText||'').trim().slice(0,40)})),
    资产抽屉:资产?{框:R(资产)}:null,
    尾文:document.body.innerText.replace(/\n{2,}/g,'\n').slice(-260)};
};

try {
  await open(page,B); await closePromos(page); await 稳();
  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  T('【A 故事板态基准】', await page.evaluate(读,'A'));
  await page.screenshot({path:E('gl1-a-基准.png')});

  // ① 双击画布空白（故事板右侧无遮的区域：顶部工具带 y≈95）
  await page.mouse.dblclick(760, 95); await page.waitForTimeout(1800);
  T('【B 双击画布空白】', await page.evaluate(读,'B'));
  await page.screenshot({path:E('gl1-b-双击空白.png')});

  // ② 底栏「添加节点」
  const 加=page.locator('button').filter({hasText:'添加节点'}).first();
  T('底栏「添加节点」可见:', await 加.isVisible().catch(()=>false));
  await 加.click({timeout:4000}).catch(e=>T('  点失败', e.message.slice(0,60)));
  await page.waitForTimeout(1600);
  T('【C 点底栏添加节点】', await page.evaluate(读,'C'));
  await page.screenshot({path:E('gl1-c-点底栏加号.png')});
  await page.keyboard.press('Escape'); await page.waitForTimeout(1400);
  T('【D Esc 之后】', await page.evaluate(读,'D'));

  // ③ TV Director 抽屉还能不能开
  const tv=page.locator('button').filter({hasText:'TV Director'}).first();
  await tv.click({timeout:4000}).catch(e=>T('  点 TV 失败', e.message.slice(0,60)));
  await page.waitForTimeout(1800);
  T('【E 点 TV Director】', await page.evaluate(读,'E'));
  await page.screenshot({path:E('gl1-d-点TVDirector.png')});
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);
  T('【F Esc 关抽屉】', await page.evaluate(读,'F'));
} finally { await browser.close(); }
