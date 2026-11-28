const d = require(process.argv[2] + '/index.js').durationTimer;
for (const n of [2000, 4000, 8000, 16000, 32000]) {
  const s = '1'.repeat(n) + 'x'; const t = Date.now(); let r;
  try { d.parseDuration(s); r = 'ok'; } catch (e) { r = e.code || e.name; }
  console.log(`javascript parseDuration('1'*${n}+'x') ${((Date.now() - t) / 1000).toFixed(3)}s -> ${r}`);
}
