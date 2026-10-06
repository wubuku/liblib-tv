import { launch, open, closePromos } from './lib.mjs';
import { resolve } from 'node:path';
const B='https://www.liblib.tv/canvas?spaceId=10354929&projectId=34226ef170f248248c74f85290228f6b';
const { browser, page } = await launch();
const T=(l,v)=>console.log(l, JSON.stringify(v));
const E=(n)=>resolve('tools','.evidence',n);
async function 稳(){let p=-1;for(let i=0;i<14;i++){const n=await page.locator('.react-flow__node').count();
  if(n===p) return n; p=n; await page.waitForTimeout(900);} return p;}

const 底栏 = () => {
  const R=(e)=>{const r=e.getBoundingClientRect();
    return [Math.round(r.x),Math.round(r.y),Math.round(r.width),Math.round(r.height)];};
  const 条=[...document.querySelectorAll('div')].filter(e=>{const r=e.getBoundingClientRect();
    return r.y>745 && r.y<775 && r.width>100 && r.height>=30 && r.height<=60;})
    .sort((a,b)=>b.getBoundingClientRect().width-a.getBoundingClientRect().width);
  const 行=条[0];
  const 列=(行?[...行.querySelectorAll('button,[role="button"]')]:[])
    .map(b=>{const r=b.getBoundingClientRect();
      const h=document.elementFromPoint(Math.round(r.x+r.width/2),Math.round(r.y+r.height/2));
      const 看得见=!!(r.width>0&&r.height>0&&+getComputedStyle(b).opacity>0.05
        &&getComputedStyle(b).visibility!=='hidden');
      return {文字:(b.innerText||'').trim().replace(/\s+/g,' ').slice(0,8),
        aria:b.getAttribute('aria-label'), 框:R(b), 看得见,
        落点:(()=>{if(!h) return null;
          let p=h, 名=(h.innerText||'').trim().split('\n')[0].slice(0,8);
          for(let k=0;k<6&&p;k++){ if(p.classList?.contains('assetboard-panel')){名='【故事板列】';break;}
            p=p.parentElement;}
          return 名;})()};});
  return {条框:行?R(行):null, 按钮:列};
};

try {
  await open(page,B); await closePromos(page); await 稳();

  // 工作流态底栏
  const 工=await page.evaluate(底栏);
  T('【工作流态·左下底栏】', JSON.stringify(工,null,1).slice(0,2000));
  await page.screenshot({path:E('gl5-a-工作流态-底栏.png'), clip:{x:0,y:745,width:900,height:62}});
  await page.screenshot({path:E('gl5-c-工作流态-顶栏右.png'), clip:{x:900,y:0,width:540,height:50}});

  await page.locator('button[aria-label="故事板"]').click(); await page.waitForTimeout(3200);
  await page.keyboard.press('Escape'); await page.waitForTimeout(1500);

  const 故=await page.evaluate(底栏);
  T('【故事板态·左下底栏】', JSON.stringify(故,null,1).slice(0,2000));
  await page.screenshot({path:E('gl5-b-故事板态-底栏.png'), clip:{x:0,y:745,width:900,height:62}});
  await page.screenshot({path:E('gl5-d-故事板态-顶栏右.png'), clip:{x:900,y:0,width:540,height:50}});
  await page.screenshot({path:E('gl5-e-故事板态-全屏.png')});
} finally { await browser.close(); }
