import os
import re
import json
import asyncio
import requests
import emoji
from dotenv import load_dotenv
from telethon import TelegramClient, functions
from telethon.sessions import StringSession

load_dotenv()

API_ID = os.getenv("API_ID", "28196030")
API_HASH = os.getenv("API_HASH", "db0ec388f4ff19cbb5ce0ce06e117566")
BOT_TOKEN = os.getenv("BOT_TOKEN", "7652023850:AAFg09BA7-Detoauqk3GOR2_w2_hMWkvVc0")
TELEGRAPH_TOKEN = os.getenv("TELEGRAPH_TOKEN", "f7bf78e9c636967eac2f4830d461351dafaccec9594b053a54d1d6504eb3")
SESSION_STRING = os.getenv("SESSION_STRING")

if API_ID:
    API_ID = int(API_ID)

GROUP_ID = -1004388024164
BOT_TARGET = "Quinellaadm_bot"
CACHE_FILE = "animes_cache.json"
PATH_PAGINA = "Yggdrasil-Animes-VIP-09-15"

def contem_emoji(texto):
    return bool(re.search(r'[\U00010000-\U0010ffff]|:\w+:', emoji.demojize(texto)))

def salvar_cache(lista_animes):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(lista_animes, f, ensure_ascii=False, indent=2)

async def main():
    if not API_ID or not API_HASH:
        print("❌ Credenciais API_ID / API_HASH não encontradas!")
        return

    print("🔄 Conectando à Telegram API via Telethon...")
    
    if SESSION_STRING:
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    else:
        client = TelegramClient('sessao_userbot', API_ID, API_HASH)

    await client.start()

    print(f"📌 Lendo tópicos do grupo {GROUP_ID}...")
    animes_encontrados = []

    try:
        chat_entity = await client.get_entity(GROUP_ID)
        
        # Chama a função nativa do Telethon para obter tópicos do fórum
        resultado = await client(functions.channels.GetForumTopicsRequest(
            channel=chat_entity,
            offset_date=0,
            offset_id=0,
            offset_topic=0,
            limit=100,
            q=''
        ))

        for topic in resultado.topics:
            nome_topico = getattr(topic, 'title', '').strip()
            if not nome_topico:
                continue
            
            if contem_emoji(nome_topico):
                print(f"Ignorado (Emoji): {nome_topico}")
                continue
            
            slug = re.sub(r'[^a-zA-Z0-9_]', '_', nome_topico.lower())
            link_bot = f"https://t.me/{BOT_TARGET}?start={slug}"
            animes_encontrados.append({"nome": nome_topico, "link": link_bot})

    except Exception as e:
        print(f"❌ Erro ao ler tópicos via API: {e}")
        await client.disconnect()
        return

    await client.disconnect()

    total_animes = len(animes_encontrados)
    print(f"✅ Sucesso! Total de animes/tópicos encontrados: {total_animes}")

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
        nodes.append({"tag": "p", "children": ["Nenhum anime encontrado nos tópicos no momento."]})

    print(f"📝 Atualizando a página {PATH_PAGINA} no Telegraph...")
    
    url_telegraph = "https://api.telegra.ph/editPage"
    payload = {
        "access_token": TELEGRAPH_TOKEN,
        "path": PATH_PAGINA,
        "title": "Yggdrasil Animes VIP",
        "author_name": "Yggdrasil VIP",
        "content": str(nodes).replace("'", '"'),
        "return_content": True
    }
    
    resp = requests.post(url_telegraph, data=payload).json()
    if resp.get("ok"):
        print("\n" + "="*50)
        print(f"🎉 CATÁLOGO ATUALIZADO COM SUCESSO!")
        print(f"👉 Link oficial: {resp['result']['url']}")
        print("="*50 + "\n")
        salvar_cache(animes_encontrados)
    else:
        print(f"❌ Erro ao atualizar Telegraph: {resp}")

if __name__ == "__main__":
    asyncio.run(main())
