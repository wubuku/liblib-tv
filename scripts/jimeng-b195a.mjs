// 批次 195 a 轮：普查画布上「带媒体的视频节点」，并读三档状态的元素差分
//
// 假设：手册 media-playback.md 的三档表（未选中 / 已选中未播 / 正在播）
//   仍然成立，且「已选中未播」那档只有 5 个按钮（无 mute/fullscreen）。
// 本轮只读，不点播放，不新建/删除任何节点。
import fs from 'node:fs';
import { openCanvas, readers, settle, setZoom, endState } from './jimeng-b135-lib.mjs';

const { b, p } = await openCanvas();
const R = readers(p);
const 基线 = { ids: await R.ids(), testids: await R.testids() };
await settle(p, R);

const 普查 = await p.evaluate(() => {
  const 账 = (el) => {
    const t = (el.innerText || '') + ' || ' + (el.getAttribute('aria-label') || '');
    const m = /(\d+ resources?:|No resources:)[^|]*/.exec(t);
    return m ? m[0].trim() : null;
  };
  return Array.from(document.querySelectorAll('.react-flow__node')).map((n) => {
    const id = n.getAttribute('data-id');
    const r = n.getBoundingClientRect();
    const testids = Array.from(new Set(Array.from(n.querySelectorAll('[data-testid]')).map((e) => e.getAttribute('data-testid'))));
    const 按钮 = Array.from(n.querySelectorAll('button')).map((b2) => b2.getAttribute('aria-label') || b2.innerText.trim()).filter(Boolean);
    return {
      id,
      aria: n.getAttribute('aria-label'),
      账: 账(n),
      屏上: [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)],
      在视口内: r.right > 0 && r.x < innerWidth && r.bottom > 0 && r.y < innerHeight,
      有video: n.querySelectorAll('video').length,
      有img: n.querySelectorAll('img').length,
      按钮,
      关键testid: testids.filter((t) => /video|audio|player|duration|preview|passive/.test(t)),
    };
  });
});

const 带媒体 = 普查.filter((x) => /视频|video/i.test(x.aria || '') || /视频/.test((x.按钮 || []).join(' ')));
const 有资源 = 普查.filter((x) => x.账 && /1 ready/.test(x.账) && x.账.startsWith('1 resource'));
const 音频 = 普查.filter((x) => /音频|audio/i.test(x.aria || ''));

const out = {
  轮次: 'b195a',
  说明: '只读普查；未点播放、未新建/删除任何节点',
  节点总数: 普查.length,
  视频节点: 带媒体.map((x) => ({ id: x.id, aria: x.aria, 账: x.账, 屏上: x.屏上, 在视口内: x.在视口内, 有video: x.有video, 有img: x.有img, 按钮: x.按钮, 关键testid: x.关键testid })),
  有资源的节点: 有资源.map((x) => ({ id: x.id, aria: x.aria, 账: x.账, 在视口内: x.在视口内, 按钮: x.按钮 })),
  音频节点: 音频.map((x) => ({ id: x.id, aria: x.aria, 账: x.账, 在视口内: x.在视口内, 有video: x.有video, 按钮: x.按钮 })),
};
fs.writeFileSync('/tmp/b195a.json', JSON.stringify(out, null, 1));
console.log(JSON.stringify(out, null, 1).slice(0, 4000));
console.log('--- 收尾 ---');
console.log(JSON.stringify(await endState(p, R, 基线), null, 1));
await b.close();
