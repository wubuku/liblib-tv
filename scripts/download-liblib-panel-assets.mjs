import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const auditPath = path.join(root, "docs/research/liblib-live-2026-08-25/panel-audit.json");
const outputDir = path.join(root, "public/images/liblib-panels");

const audit = JSON.parse(await readFile(auditPath, "utf8"));

const toolbox = audit.toolbox.images.map((asset, index) => ({
  group: "toolbox",
  title: asset.alt,
  url: asset.src,
  file: `toolbox-${String(index + 1).padStart(2, "0")}.webp`,
}));

const character = audit.character.images.map((asset, index) => ({
  group: index < 4 ? "character-detail" : "character-thumb",
  title: asset.alt,
  url: asset.src,
  file: index < 4
    ? `character-detail-${index + 1}.webp`
    : `character-thumb-${String(index - 3).padStart(2, "0")}.webp`,
}));

const history = audit.history.images
  .filter((asset) => !asset.src.includes("watermark.png"))
  .map((asset, index) => ({
    group: "history",
    title: `历史图片 ${index + 1}`,
    url: asset.src,
    file: `history-${String(index + 1).padStart(2, "0")}.webp`,
  }));

const assets = [...toolbox, ...character, ...history];

await mkdir(outputDir, { recursive: true });

async function download(asset) {
  const response = await fetch(asset.url);
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}: ${asset.url}`);
  }
  const bytes = Buffer.from(await response.arrayBuffer());
  await writeFile(path.join(outputDir, asset.file), bytes);
  return { ...asset, bytes: bytes.length, contentType: response.headers.get("content-type") };
}

const downloaded = [];
for (let index = 0; index < assets.length; index += 4) {
  downloaded.push(...await Promise.all(assets.slice(index, index + 4).map(download)));
}

await writeFile(
  path.join(outputDir, "manifest.json"),
  `${JSON.stringify({ generatedFrom: path.relative(root, auditPath), assets: downloaded }, null, 2)}\n`,
);

console.log(`Downloaded ${downloaded.length} LibTV panel assets to ${path.relative(root, outputDir)}`);
