// 倒出**每一个** <pattern> 元素与背景 svg 的逐字外链，解开
// 「patternTransform 这次是 null / 上次有值」之谜。
import { launch, closePromos, ORIGIN } from './lib.mjs';
import { writeFileSync } from 'node:fs';
import { 核对坐标 } from './canvas-baseline.mjs';

const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const HERE = new URL('.', import.meta.url).pathname;
const 落盘 = (o) => writeFileSync(HERE + 'dbg-fb2.json', JSON.stringify(o, null, 2));
const R = { 步骤: [] };
const 记 = (s) => { R.步骤.push(s); 落盘(R); console.log('· ' + s); };

const 浏览器 = await launch();
const page = 浏览器.page;
try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  记('开局坐标偏差：' + JSON.stringify(await 核对坐标(page)));

  const d = await page.evaluate(() => {
    const v = document.querySelector('.react-flow__viewport');
    const vm = getComputedStyle(v).transform;
    const pats = [...document.querySelectorAll('pattern')].map((p) => {
      const o = {};
      for (const a of p.attributes) o[a.name] = a.value;
      return { 属性: o, 外链: p.outerHTML.slice(0, 260), 父: p.parentElement ? p.parentElement.tagName + '.' + (p.parentElement.getAttribute('class') || '') : null };
    });
    const bgs = [...document.querySelectorAll('.react-flow__background')].map((b) => b.outerHTML.slice(0, 1200));
    const 背景类 = [...document.querySelectorAll('svg')].filter((s) => /background/.test(s.getAttribute('class') || '')).map((s) => s.getAttribute('class'));
    return { viewport: vm, pattern个数: pats.length, pats, 背景数: bgs.length, bgs, 背景类 };
  });
  记('viewport transform = ' + d.viewport);
  记('pattern 元素个数 = ' + d.pattern个数 + '｜.react-flow__background 个数 = ' + d.背景数);
  记('背景 svg class = ' + JSON.stringify(d.背景类));
  for (let i = 0; i < d.pats.length; i++) {
    const p = d.pats[i];
    记(`--- pattern[${i}] 父=${p.父}`);
    记('    属性=' + JSON.stringify(p.属性));
    记('    外链=' + p.外链);
  }
  for (let i = 0; i < d.bgs.length; i++) 记(`--- background[${i}] = ` + d.bgs[i]);
  R.读数 = d;
} catch (e) {
  R.错误 = String(e && e.stack || e);
  记('❌ ' + R.错误.split('\n')[0]);
} finally {
  记('收尾核对：' + JSON.stringify(await 核对坐标(page)));
  await 浏览器.browser.close();
  落盘(R);
}
