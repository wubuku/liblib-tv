import { launch, closePromos, ORIGIN } from './lib.mjs';
const SPACE = '10354929';
const CANVAS_URL = `${ORIGIN}/canvas?spaceId=${SPACE}&projectId=34226ef170f248248c74f85290228f6b`;
const 浏览器 = await launch();
const page = 浏览器.page;
try {
  await page.goto(CANVAS_URL, { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(9000);
  await closePromos(page);
  await page.keyboard.press('Meta+0');
  await page.waitForTimeout(3000);
  const s = await page.evaluate(() => [...document.querySelectorAll('.react-flow__node')].map((n) => {
    const m = /translate\((-?[\d.]+)px,\s*(-?[\d.]+)px\)/.exec(n.style.transform || '');
    return [n.getAttribute('data-id'), m ? [Number(m[1]), Number(m[2])] : null];
  }));
  const 基线 = {
    'a-GgqvrVz0pw': [719.388, 1509.13], 'a-THmbuJXQj4': [-1356, 600],
    'b-mfkcQNULC3': [636, 300], 'i-9nlG6HdjK2': [-1764, 900],
    'i-sODTbgLUm1': [-168, 900], 'n-56F19pXVB4': [-1225.03, 370.975],
    't-2AK3Ukyxj3': [-1476, 1524], 't-UtVx3lZmrV': [600, 900],
    'v-eMpqKtiLlx': [-1787, 900], 'v-oZNpH99MtM': [132, 300], 'v-v2hlWY4Br3': [-696, 300],
  };
  let 坏 = 0;
  for (const [id, xy] of s) {
    const b = 基线[id];
    if (!b) { console.log('  未知节点', id, xy); 坏++; continue; }
    const d = Math.hypot(xy[0] - b[0], xy[1] - b[1]);
    if (d > 0.5) { console.log(`  ⚠️ 偏离 ${id}: 现 ${JSON.stringify(xy)} 基线 ${JSON.stringify(b)} 差 ${d.toFixed(2)}`); 坏++; }
    else console.log(`  ✅ ${id} ${JSON.stringify(xy)}`);
  }
  console.log('偏离节点数 =', 坏);
} catch (e) { console.log('ERR', e.message); } finally { await 浏览器.browser.close(); }
