// Executa cases.jsonl contra a implementação JavaScript. Uso: node run_js.js <dir_js_pkg> <saida.json>
const fs = require('fs');
const hub = require(require('path').resolve(process.argv[2]) + '/index.js');
const out = [];
for (const line of fs.readFileSync('cases.jsonl', 'utf8').split('\n')) {
  if (!line.trim()) continue;
  const c = JSON.parse(line);
  let args;
  try { args = JSON.parse(c.args_text); } catch (e) { out.push({ id: c.id, outcome: 'parse_error', detail: e.name }); continue; }
  try {
    const v = hub[c.tool][c.fn](...args);
    JSON.stringify(v);
    out.push({ id: c.id, outcome: 'ok', value: v === undefined ? null : v });
  } catch (e) {
    if (e && e.name === 'ToolError') out.push({ id: c.id, outcome: 'error', code: e.code });
    else out.push({ id: c.id, outcome: 'crash', detail: String(e && e.name) + ': ' + String(e && e.message).slice(0, 120) });
  }
}
fs.writeFileSync(process.argv[3], JSON.stringify(out));
console.log('javascript:', out.length, 'casos;', out.filter(r => r.outcome === 'crash').length, 'crashes (exceção não-ToolError)');
