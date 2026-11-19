import { build } from "esbuild";
import { paperTitle } from "./story.js";
import { writeFile } from "node:fs/promises";
import assert from "node:assert/strict";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const bundle = await build({
  absWorkingDir: here,
  entryPoints: ["app.jsx"],
  bundle: true,
  minify: true,
  write: false,
  outdir: "build",
  loader: { ".jpg": "dataurl" },
  define: { "process.env.NODE_ENV": '"production"' },
  legalComments: "inline",
  target: "es2020",
});
const js = bundle.outputFiles.find((f) => f.path.endsWith(".js")).text;
const css = bundle.outputFiles.find((f) => f.path.endsWith(".css")).text;
assert.equal(
  bundle.outputFiles.length,
  2,
  "离线版必须只生成可内嵌的 JS 和 CSS",
);
assert.equal(js.split("data:image/jpeg;base64,").length - 1, 2, "封面和双声源示意图必须内嵌");
const html =
  `<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${paperTitle}</title><style>` +
  css +
  '</style><body><div id="root"></div><script>' +
  js.replace(/<\/script/gi, "<\\/script") +
  "</script></body></html>";
await writeFile(path.resolve(here, "../03 交互动画版.html"), html);
console.log("已生成可离线打开的 03 交互动画版.html");
