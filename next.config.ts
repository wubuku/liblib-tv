import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: "standalone",
  // ★★ Batch 827：Next 16 的 dev 资源（`/_next/webpack-hmr`）默认**只认 localhost**，
  //   用 `http://127.0.0.1:4317` 访问时会被判成跨源并**拒绝**：
  //   「Blocked cross-origin request to Next.js dev resource /_next/webpack-hmr from "127.0.0.1"」
  //   ⟹ ★★ **整页不 hydration**（DOM 上没有 `__react*` props，点击全部无效），
  //   而页面看起来是正常的 ⟹ ★★ 探针会把「静态 SSR HTML」当成「活体读数」。
  //   ⟹ 这里把两个 origin 都放行 ⟹ 两种写法都能测到真交互。
  //   ★ 生产构建不受影响（`allowedDevOrigins` 只作用于 dev server）。
  allowedDevOrigins: ["127.0.0.1", "localhost"],
};

export default nextConfig;
