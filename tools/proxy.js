// 本地微型代理：给所有转发到 OpenCode Go 网关的请求自动补上 x-opencode-session 头
// 用法: node ~/proxy.js   （监听 127.0.0.1:8787）
const http = require('http');
const https = require('https');
const fs = require('fs');

const TARGET = 'opencode.ai';
const PORT = 8787;
const LOG = process.env.HOME + '/proxy.log';
const log = (m) => fs.appendFileSync(LOG, new Date().toISOString() + ' ' + m + '\n');

const server = http.createServer((req, res) => {
  // 无 key 的请求 = Claude Code 的连通性探测（如 HEAD /api/hello）→ 本地直接应答，不转发
  // （网关对该路径回 404，会让 Claude Code 误判为连不上）
  if (!req.headers['x-api-key'] && !req.headers.authorization) {
    log(`probe answered locally: ${req.method} ${req.url}`);
    res.writeHead(401, { 'content-type': 'application/json' });
    res.end('{"type":"error","error":{"type":"authentication_error","message":"missing api key"}}');
    return;
  }
  // Claude Code 用 AUTH_TOKEN 时发送 Authorization: Bearer <key>；网关 Anthropic 端点(/v1/messages)只认 x-api-key，翻译一下
  // 网关 OpenAI 端点(/v1/chat/completions)要标准 Bearer，保持原样
  if (req.url.includes('/v1/messages') && !req.headers['x-api-key'] && req.headers.authorization && req.headers.authorization.startsWith('Bearer ')) {
    req.headers['x-api-key'] = req.headers.authorization.slice(7);
    delete req.headers.authorization;
  }
  log(`${req.method} ${req.url} key=${req.headers['x-api-key'] ? 'yes' : 'no'} session=${req.headers['x-opencode-session'] || 'none'}`);
  const opts = {
    hostname: TARGET,
    port: 443,
    path: '/zen/go' + req.url,
    method: req.method,
    headers: { ...req.headers, 'x-opencode-session': 'claude-wsl', host: TARGET },
  };
  const preq = https.request(opts, (pres) => {
    res.writeHead(pres.statusCode, pres.headers);
    pres.pipe(res);
  });
  preq.on('error', (e) => { log('UPSTREAM ERROR: ' + e.message); res.writeHead(502); res.end(); });
  req.pipe(preq);
});

server.listen(PORT, '127.0.0.1', () => log('proxy listening on ' + PORT));
