// Exercise the actual Worker handler with frozen synthetic feeds. No network.
import assert from 'node:assert/strict';
import { onRequestGet } from '../../research/sources/should-ai-kill-us-all/functions/api/verdict.js';
const cache=new Map();
globalThis.caches={default:{match:async req=>cache.get(req.url)?.clone(),put:async(req,value)=>cache.set(req.url,value.clone())}};
let requests=0;
globalThis.fetch=async()=>{requests++;return new Response('<rss><channel><item><title>Public library opens a new science exhibition today</title><link>https://example.com/fixture</link><pubDate>Mon, 21 Sep 2026 12:00:00 GMT</pubDate></item></channel></rss>');};
const request=new Request('http://127.0.0.1/api/verdict');
const response=await onRequestGet({request,env:{},waitUntil:()=>{}});
assert.equal(response.status,503);
assert.equal((await response.json()).error,'not_configured');
assert.ok(requests>0);
cache.set(request.url,new Response(JSON.stringify({fixture:true}),{headers:{'Content-Type':'application/json'}}));
const count=requests;
const cached=await onRequestGet({request,env:{},waitUntil:()=>{}});
assert.equal(cached.status,200);
assert.equal((await cached.json()).fixture,true);
assert.equal(requests,count);
console.log(JSON.stringify({passed:2,evidence:'simulation',external_requests:0,checks:['missing-key-is-503','cache-hit-does-not-fetch']}));
