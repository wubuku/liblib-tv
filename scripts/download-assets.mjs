import https from "https";
import http from "http";
import fs from "fs";
import path from "path";

const ASSETS = [
  {
    url: "https://liblibai-online.liblib.cloud/web/avatar/avatar5.png?x-oss-process=image/resize,w_100,m_lfit/",
    dest: "public/images/avatar.png",
  },
  {
    url: "https://libtv-res.liblib.art/watermark.png",
    dest: "public/images/watermark.png",
  },
  {
    url: "https://libtv-res.liblib.art/upload-images/5cdcf405ca3e42299d1234607e630fce/ee677b5998d05633d14b0aafe879148d2683be66.png?x-oss-process=image/resize,w_1600,m_lfit/format,webp/ignore-error,1",
    dest: "public/images/scene-coffee-1.png",
  },
  {
    url: "https://libtv-res.liblib.art/sd-gen-save-img/genius_playground/image/5cdcf405ca3e42299d1234607e630fce/765910904_90405148df0648e0943f8abb5bd95808.png?x-oss-process=image/resize,w_1600,m_lfit/format,webp/ignore-error,1",
    dest: "public/images/scene-coffee-2.png",
  },
  {
    url: "https://libtv-res.liblib.art/upload-images/5cdcf405ca3e42299d1234607e630fce/148d3bd30096c0d041ccb2f950c7ba151c9bd215.png?x-oss-process=image/resize,w_1600,m_lfit/format,webp/ignore-error,1",
    dest: "public/images/scene-coffee-3.png",
  },
  {
    url: "https://libtv-res.liblib.art/sd-gen-save-img/genius_playground/image/5cdcf405ca3e42299d1234607e630fce/765930586_ab1d46e5d96742c8b55d055fb1fe5a41.png?x-oss-process=image/resize,w_800,m_lfit/format,webp/ignore-error,1",
    dest: "public/images/storyboard-2.png",
  },
];

function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const dir = path.dirname(dest);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    const client = url.startsWith("https") ? https : http;

    const makeRequest = (reqUrl) => {
      client
        .get(reqUrl, (res) => {
          if (res.statusCode >= 300 && res.statusCode < 400 && res.headers.location) {
            makeRequest(res.headers.location);
            return;
          }
          if (res.statusCode !== 200) {
            reject(new Error(`HTTP ${res.statusCode} for ${url}`));
            return;
          }
          const stream = fs.createWriteStream(dest);
          res.pipe(stream);
          stream.on("finish", () => {
            stream.close();
            resolve();
          });
        })
        .on("error", reject);
    };

    makeRequest(url);
  });
}

async function main() {
  console.log("Downloading assets...");
  for (const asset of ASSETS) {
    try {
      await downloadFile(asset.url, asset.dest);
      const stats = fs.statSync(asset.dest);
      console.log(`✓ ${asset.dest} (${(stats.size / 1024).toFixed(1)}KB)`);
    } catch (err) {
      console.error(`✗ ${asset.dest}: ${err.message}`);
    }
  }
  console.log("Done!");
}

main();
