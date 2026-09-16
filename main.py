import os
import re
import json
import requests
import emoji
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAPH_TOKEN = os.getenv("TELEGRAPH_TOKEN")
GROUP_ID = "-1004388024164"
BOT_TARGET = "Quinellaadm_bot"
CACHE_FILE = "animes_cache.json"

def contem_emoji(texto):
    return bool(re.search(r'[𐀀-􏿿]|:\w+:', emoji.demojize(texto)))

def carregar_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def salvar_cache(lista_animes):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(lista_animes, f, ensure_ascii=False, indent=2)

def atualizar_catalogo():
    bot = Bot(token=BOT_TOKEN)
    
    url_topics = f"https://api.telegram.org/bot{BOT_TOKEN}/getForumTopics"
    params = {"chat_id": GROUP_ID}
    res = requests.get(url_topics, params=params).json()

    animes_encontrados = []

    if res.get("ok") and "topics" in res.get("result", {}):
        topics = res["result"]["topics"]
        for topic in topics:
            nome_topico = topic.get("name", "").strip()
            
            # Pula tópicos que possuem emojis (bate-papo/avisos)
            if contem_emoji(nome_topico):
                print(f"Ignorado (Contém Emoji): {nome_topico}")
                continue
            
            slug = re.sub(r'[^a-zA-Z0-9_]', '_', nome_topico.lower())
            link_bot = f"https://t.me/{BOT_TARGET}?start={slug}"
            
            animes_encontrados.append({"nome": nome_topico, "link": link_bot})

    cache_anterior = carregar_cache()
    nomes_anteriores = [a["nome"] for a in cache_anterior]
    novos_titulos = [a["nome"] for a in animes_encontrados if a["nome"] not in nomes_anteriores]

    total_animes = len(animes_encontrados)

    nodes = [
        {"tag": "h3", "children": ["Yggdrasil Animes VIP - Catálogo Oficial"]},
        {"tag": "p", "children": [f"📊 Total de animes disponíveis: {total_animes}"]},
        {"tag": "p", "children": ["Clique no título do anime para acessar via bot:"]},
        {"tag": "hr", "children": []}
    ]

    lista_items = []
    for anime in sorted(animes_encontrados, key=lambda x: x["nome"]):
        lista_items.append({
            "tag": "li",
            "children": [
                {
                    "tag": "a",
                    "attrs": {"href": anime["link"]},
                    "children": [anime["nome"]]
                }
            ]
        })

    if lista_items:
        nodes.append({"tag": "ul", "children": lista_items})
    else:
        nodes.append({"tag": "p", "children": ["Nenhum anime cadastrado no momento."]})

    url_telegraph = "https://api.telegra.ph/createPage"
    payload = {
        "access_token": TELEGRAPH_TOKEN,
        "title": "Yggdrasil Animes VIP",
        "author_name": "Yggdrasil VIP",
        "content": str(nodes).replace("'", '"'),
        "return_content": True
    }
    
    resp = requests.post(url_telegraph, data=payload).json()
    if resp.get("ok"):
        catalogo_url = resp['result']['url']
        print(f"✅ Catálogo atualizado com sucesso! Link: {catalogo_url}")
        
        # Avisa no grupo sobre os títulos novos informando o nome do anime
        if novos_titulos:
            for novo in novos_titulos:
                msg_notificacao = f"📣 *Novo anime adicionado ao catálogo:* {novo}"
                url_send = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                payload_msg = {
                    "chat_id": GROUP_ID,
                    "text": msg_notificacao,
                    "parse_mode": "Markdown"
                }
                requests.post(url_send, data=payload_msg)
        
        salvar_cache(animes_encontrados)
    else:
        print(f"❌ Erro ao atualizar Telegraph: {resp}")

if __name__ == "__main__":
    atualizar_catalogo()
