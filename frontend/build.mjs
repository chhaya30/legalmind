import { build } from 'esbuild'
import { mkdir, rm, readFile, writeFile } from 'node:fs/promises'
import { dirname, resolve } from 'node:path'

const root = process.cwd()
const dist = resolve(root, 'dist')
await rm(dist, { recursive: true, force: true })
await mkdir(resolve(dist, 'assets'), { recursive: true })

await build({
  entryPoints: [resolve(root, 'src/main.jsx')],
  bundle: true,
  minify: true,
  sourcemap: false,
  target: ['es2020'],
  platform: 'browser',
  format: 'esm',
  jsx: 'automatic',
  define: {
    'import.meta.env.VITE_API_URL': JSON.stringify(process.env.VITE_API_URL || 'http://127.0.0.1:8001/api/v1'),
  },
  outfile: resolve(dist, 'assets/app.js'),
  logLevel: 'info',
  legalComments: 'none',
})

const cssPath = resolve(dist, 'assets/app.css')
let html = await readFile(resolve(root, 'index.html'), 'utf8')
html = html
  .replace(/<script[^>]+src="\/src\/main\.jsx"[^>]*><\/script>/, '<script type="module" src="/assets/app.js"></script>')
  .replace('</head>', '<link rel="stylesheet" href="/assets/app.css"></head>')
await writeFile(resolve(dist, 'index.html'), html)
console.log(`Production bundle created: ${dist}`)
console.log(`CSS emitted: ${cssPath}`)
