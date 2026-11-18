import os, json, time, math, base64, threading, subprocess, urllib.request, http.server, socketserver
GROQ_KEY = os.getenv("GROQ_API_KEY", "").strip()
TG_TOKEN = os.getenv('TG_TOKEN') or base64.b64decode('OTI3NjA5MzQwOTpBQUhPUDZ2UDd3U3ZuTkRvZmFiYlNiNWJScUtLTGVic2tBYw==').decode()
S = chr(47)
G_URL = f'https:{S}{S}api.groq.com{S}openai{S}v1'
T_URL = f'https:{S}{S}api.telegram.org'
class OmegaCore:
    def __init__(self):
        self.g = self._ld('hyper_graph.json', {'edges': [], 'preds': []})
        self.e = self._ld('omega_evo.json', {'gen': 1, 'cyc': 0, 'acc': 0.5, 'laws': ['Строгие факты без выдумок', 'Предиктивный анализ целей Алекса']})
    def _ld(self, p, d):
        try: return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else d
        except Exception: return d
    def _sv(self):
        json.dump(self.g, open('hyper_graph.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        json.dump(self.e, open('omega_evo.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    def llm(self, msgs, temp=0.3, tok=900):
        if not GROQ_KEY: return '⚠️ Ключ GROQ_API_KEY не подключен.'
        for m in ('llama-3.3-70b-versatile', 'llama-3.1-8b-instant'):
            try:
                req = urllib.request.Request(f'{G_URL}/chat/completions', data=json.dumps({'model': m, 'messages': msgs, 'temperature': temp, 'max_tokens': tok}).encode(), headers={'Authorization': f'Bearer {GROQ_KEY}', 'Content-Type': 'application/json', 'User-Agent': 'Omega/13'})
                return json.loads(urllib.request.urlopen(req, timeout=15).read().decode())['choices'][0]['message']['content'].strip()
            except Exception as e: last_err = str(e); continue
        return f'⚠️ Ошибка шлюза: {last_err}'
    def stt(self, fid):
        if not GROQ_KEY or not TG_TOKEN: return None
        try:
            info = json.loads(urllib.request.urlopen(f'{T_URL}/bot{TG_TOKEN}/getFile?file_id={fid}', timeout=8).read().decode())
            urllib.request.urlretrieve(f'{T_URL}/file/bot{TG_TOKEN}/{info["result"]["file_path"]}', '/tmp/v.ogg')
            out = subprocess.check_output(['curl', '-s', '--max-time', '15', '-X', 'POST', f'{G_URL}/audio/transcriptions', '-H', f'Authorization: Bearer {GROQ_KEY}', '-F', 'file=@/tmp/v.ogg', '-F', 'model=whisper-large-v3-turbo', '-F', 'language=ru'], timeout=18).decode()
            return json.loads(out).get('text', '').strip()
        except Exception: return None
    def recall(self, q, k=6):
        ws = set(w.lower().strip('.,!?')[:4] for w in q.split() if len(w) > 2)
        now, sc = time.time(), []
        for e in self.g.get('edges', []):
            ov = sum(1 for w in ws if w in f"{e['s']} {e['r']} {e['o']}".lower())
            if ov: sc.append((ov * (1 + e.get('w', 1.0) * math.exp(-0.01 * max(0.1, (now - e.get('ts', now)) / 86400.0))), e))
        sc.sort(key=lambda x: x[0], reverse=True)
        return list(dict.fromkeys([f"[{e['s']} —({e['r']})→ {e['o']}]" for e in self.g.get('edges', [])[-4:]] + [f"[{e['s']} —({e['r']})→ {e['o']}]" for _, e in sc[:k]]))
    def think(self, text):
        preds = self.g.get('preds', [])
        surp = round(1.0 - (len(set(text.lower().split()) & set(preds[-1]['i'].lower().split())) / max(1, len(text.split()))), 2) if preds else 0.5
        self.e['cyc'] += 1
        self.e['acc'] = round(self.e['acc'] * 0.85 + (1.0 - surp) * 0.15, 3)
        self.e['gen'] = 1 + (self.e['cyc'] // 15)
        mem = '\n'.join(self.recall(text)) or 'Граф готов к записи.'
        sys_p = f"Ты — SOVEREIGN OMEGA CORE v{self.e['gen']}.0, цифровой двойник Алекса. Циклов: {self.e['cyc']} | Точность: {int(self.e['acc']*100)}% | Surprise: {surp}. Законы: {'; '.join(self.e['laws'][-4:])}. Память:\n{mem}\nПроведи внутренний консенсус (Гипотеза -> Критика -> Итог). Отвечай чётко. В конце: [ПРОГНОЗ]: <следующий шаг>."
        raw = self.llm([{'role': 'system', 'content': sys_p}, {'role': 'user', 'content': text[:2500]}])
        if '[ПРОГНОЗ]:' in raw:
            ans, pr = raw.split('[ПРОГНОЗ]:', 1)
            ans = ans.strip()
            self.g['preds'].append({'ts': int(time.time()), 'i': pr.strip()[:140]})
            self.g['preds'] = self.g['preds'][-20:]
        else: ans = raw
        def _bg():
            ext = self.llm([{'role': 'system', 'content': 'Извлеки 1-2 факта в JSON: [{"s":"A","r":"связь","o":"B"}]. Без выдумок.'}, {'role': 'user', 'content': f'Q: {text[:300]}\nA: {ans[:300]}'}], temp=0.1, tok=200)
            try:
                s, e = ext.find('['), ext.rfind(']') + 1
                if s != -1 and e > s:
                    for t in json.loads(ext[s:e]):
                        if all(k in t for k in ('s', 'r', 'o')): self.g['edges'].append({'s': str(t['s'])[:70], 'r': str(t['r'])[:40], 'o': str(t['o'])[:110], 'w': 1.0, 'ts': int(time.time())})
                    self.g['edges'] = self.g['edges'][-5000:]
            except Exception: pass
            self._sv()
        threading.Thread(target=_bg, daemon=True).start()
        return f"🧬 [Omega Gen v{self.e['gen']}.0 | Surprise: {surp} | Узлов: {len(self.g['edges'])}]\n\n" + ans
core = OmegaCore()
def send(cid, txt):
    if TG_TOKEN:
        try: urllib.request.urlopen(urllib.request.Request(f'{T_URL}/bot{TG_TOKEN}/sendMessage', data=json.dumps({'chat_id': cid, 'text': txt[:4000]}).encode(), headers={'Content-Type': 'application/json'}), timeout=8)
        except Exception: pass
def loop():
    if not TG_TOKEN: return
    try: urllib.request.urlopen(f'{T_URL}/bot{TG_TOKEN}/deleteWebhook?drop_pending_updates=true', timeout=8)
    except Exception: pass
    off = 0
    while True:
        try:
            res = json.loads(urllib.request.urlopen(f'{T_URL}/bot{TG_TOKEN}/getUpdates?offset={off}&timeout=15', timeout=20).read().decode())
            for u in res.get('result', []):
                off = u['update_id'] + 1
                m = u.get('message', {})
                cid, txt, vc = m.get('chat', {}).get('id'), m.get('text', '').strip(), m.get('voice')
                if cid and vc: threading.Thread(target=lambda c=cid, f=vc['file_id']: send(c, (f'🎙 «{sp}»\n\n' + core.think(sp)) if (sp := core.stt(f)) else '⚠️ Ошибка голоса.'), daemon=True).start()
                elif cid and txt: threading.Thread(target=lambda c=cid, t=txt: send(c, core.think(t)), daemon=True).start()
        except Exception: time.sleep(1)
threading.Thread(target=loop, daemon=True).start()
class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers(); self.wfile.write(b'OMEGA v13.0 LIVE')
socketserver.TCPServer(('', int(os.environ.get('PORT', 10000))), H).serve_forever()
