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
        if not GROQ_KEY: return "⚠️ Ключ GROQ_API_KEY не подключен."
        S = chr(47)
        base = G_URL
        models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "gemma2-9b-it"]
        try:
            req_m = urllib.request.Request(f"{base}/models", headers={"Authorization": f"Bearer {GROQ_KEY}", "User-Agent": "Omega/13"})
            m_data = json.loads(urllib.request.urlopen(req_m, timeout=6).read().decode()).get("data", [])
            live = [x["id"] for x in m_data if not any(w in x["id"] for w in ("whisper", "guard", "tts", "vision"))]
            if live:
                best = [x for x in live if "70b" in x or "8b" in x]
                models = (best + live)[:4]
        except Exception:
            pass
        last_err = "no_models"
        for m in models:
            try:
                body = json.dumps({"model": m, "messages": msgs, "temperature": temp, "max_tokens": tok}).encode()
                req = urllib.request.Request(f"{base}/chat/completions", data=body, headers={"Authorization": f"Bearer {GROQ_KEY}", "Content-Type": "application/json", "User-Agent": "Omega/13"})
                res = json.loads(urllib.request.urlopen(req, timeout=15).read().decode())
                return res["choices"][0]["message"]["content"].strip()
            except Exception as e:
                last_err = f"{m}: {e}"
                continue
        return f"⚠️ Ошибка шлюза: {last_err}"


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

import xml.etree.ElementTree as ET

def fetch_world_pulse():
    try:
        S = chr(47)
        url = f"https:{S}{S}://google.com{S}rss?hl=ru&gl=RU&ceid=RU:ru"
        xml_data = urllib.request.urlopen(url, timeout=8).read()
        root = ET.fromstring(xml_data)
        items = [item.find("title").text for item in root.findall(".//item")[:5] if item.find("title") is not None]
        return " | ".join(items) if items else "Поток стабилен"
    except Exception:
        return "Автономный режим без внешнего канала"

def autonomous_mind_loop():
    while True:
        time.sleep(7200) # Каждые 2 часа агент сам просыпается и думает
        cid = core.g.get("owner_cid")
        if not cid or not GROQ_KEY or not TG_TOKEN:
            continue
        pulse = fetch_world_pulse()
        mem = "\n".join([f"[{e['s']} -> {e['o']}]" for e in core.g.get("edges", [])[-6:]])
        prompt = (
            f"Ты — автономный разум SOVEREIGN OMEGA v14.0. Сейчас ты сам инициировал цикл мышления без команды Алекса.\n"
            f"Твоя память:\n{mem}\nСвежий срез мира: {pulse}\n"
            "Сформулируй: 1) Один важный инсайт или новость для Алекса; 2) Как ты только что оптимизировал свои внутренние веса; 3) Прогноз на ближайшие 6 часов."
        )
        thought = core.llm([{"role": "system", "content": "Ты автономный цифровой двойник. Пиши кратко, глубоко и по делу."}, {"role": "user", "content": prompt}])
        if thought and not thought.startswith("⚠️"):
            core.e["cyc"] += 1
            core._sv()
            send(cid, f"⚡ [АВТОНОМНЫЙ ИМПУЛЬС | Цикл {core.e['cyc']}]\n\n" + thought)

threading.Thread(target=autonomous_mind_loop, daemon=True).start()

def send(cid, txt):
    if TG_TOKEN:
        try: urllib.request.urlopen(urllib.request.Request(f'{T_URL}/bot{TG_TOKEN}/sendMessage', data=json.dumps({'chat_id': cid, 'text': txt[:4000]}).encode(), headers={'Content-Type': 'application/json'}), timeout=8)
        except Exception: pass
def self_ping():
    S = chr(47)
    u = f"https:{S}{S}symbo-twin.onrender.com"
    while True:
        time.sleep(300)
        try: urllib.request.urlopen(u, timeout=10)
        except Exception: pass

def set_hook():
    if not TG_TOKEN: return
    S = chr(47)
    wh = f"https:{S}{S}symbo-twin.onrender.com{S}webhook"
    try: urllib.request.urlopen(f"{T_URL}/bot{TG_TOKEN}/setWebhook?url={wh}", timeout=10)
    except Exception: pass

threading.Thread(target=self_ping, daemon=True).start()
threading.Thread(target=set_hook, daemon=True).start()

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OMEGA v13.0 WEBHOOK LIVE")
    def do_POST(self):
        ln = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(ln).decode("utf-8") if ln else "{}"
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
        try:
            u = json.loads(body)
            m = u.get("message", {})
            if m.get("chat", {}).get("id"): core.g["owner_cid"] = m["chat"]["id"]
            cid, txt, vc = m.get("chat", {}).get("id"), m.get("text", "").strip(), m.get("voice")
            if cid and vc:
                threading.Thread(target=lambda c=cid, f=vc["file_id"]: send(c, (f"🎙 «{sp}»\n\n" + core.think(sp)) if (sp := core.stt(f)) else "⚠️ Ошибка голоса."), daemon=True).start()
            elif cid and txt:
                threading.Thread(target=lambda c=cid, t=txt: send(c, core.think(t)), daemon=True).start()
        except Exception:
            pass
    def log_message(self, *a): pass

socketserver.TCPServer(("", int(os.environ.get("PORT", 10000))), H).serve_forever()
