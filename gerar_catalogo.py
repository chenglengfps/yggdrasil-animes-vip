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
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAPH_TOKEN = os.getenv("TELEGRAPH_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")

if API_ID:
    API_ID = int(API_ID)

if SESSION_STRING:
    SESSION_STRING = SESSION_STRING.strip().strip("'").strip('"')

GROUP_ID = -1004388024164
BOT_TARGET = "Quinellaadm_bot"
CACHE_FILE = "animes_cache.json"
PATH_PAGINA = "Yggdrasil-Animes-VIP-09-15"

def limpar_nome_para_slug(texto):
    texto_sem_emoji = emoji.replace_emoji(texto, replace='')
    slug = re.sub(r'[^a-zA-Z0-9_]', '_', texto_sem_emoji.strip().lower())
    slug = re.sub(r'_+', '_', slug).strip('_')
    return slug

def salvar_cache(lista_animes):
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(lista_animes, f, ensure_ascii=False, indent=2)

async def main():
    if not API_ID or not API_HASH or not SESSION_STRING:
        print("❌ Credenciais API_ID, API_HASH ou SESSION_STRING ausentes/invalidas!")
        return

    print("🔄 Conectando à Telegram API via Telethon...")
    
    try:
        client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
        await client.start()
    except Exception as e:
        print(f"❌ Erro ao autenticar session string: {e}")
        return

    print("📌 Localizando o grupo correto...")
    chat_entity = None

    # Tenta buscar pelo ID direto ou varre os chats da conta
    try:
        chat_entity = await client.get_entity(GROUP_ID)
    except Exception:
        async for dialog in client.iter_dialogs():
            if "yggdrasil" in dialog.name.lower() or "vip" in dialog.name.lower():
                chat_entity = dialog.entity
                print(f"🎯 Grupo localizado por nome: {dialog.name} (ID: {dialog.id})")
                break

    if not chat_entity:
        print("❌ Não foi possível encontrar o grupo no perfil da conta.")
        await client.disconnect()
        return

    print(f"✅ Lendo tópicos de: {getattr(chat_entity, 'title', 'Grupo')}")
    animes_encontrados = []
    topicos_unicos = set()

    try:
        offset_date = 0
        offset_id = 0
        offset_topic = 0

        while True:
            resultado = await client(functions.channels.GetForumTopicsRequest(
                channel=chat_entity,
                offset_date=offset_date,
                offset_id=offset_id,
                offset_topic=offset_topic,
                limit=100,
                q=''
            ))

            if not getattr(resultado, 'topics', None):
                break

            for topic in resultado.topics:
                nome_topico = getattr(topic, 'title', '').strip()
                topic_id = getattr(topic, 'id', None)

                if not nome_topico or topic_id in topicos_unicos:
                    continue
                
                topicos_unicos.add(topic_id)

                if nome_topico.lower() in ["general", "geral"]:
                    continue

                print(f"🔹 Tópico encontrado: {nome_topico}")

                slug = limpar_nome_para_slug(nome_topico)
                if not slug:
                    slug = "anime"

                link_bot = f"https://t.me/{BOT_TARGET}?start={slug}"
                animes_encontrados.append({"nome": nome_topico, "link": link_bot})

            if len(resultado.topics) < 100:
                break
                
            ultimo = resultado.topics[-1]
            offset_topic = ultimo.id
            offset_id = getattr(ultimo, 'top_message', 0)
            offset_date = getattr(ultimo, 'date', 0)

    except Exception as e:
        print(f"❌ Erro ao ler tópicos: {e}")

    await client.disconnect()

    total_animes = len(animes_encontrados)
    print(f"📊 Total de animes encontrados: {total_animes}")

    nodes = [
        {"tag": "h3", "children": ["Yggdrasil Animes VIP - Catálogo Oficial"]},
        {"tag": "p", "children": [f"📊 Total de animes disponíveis: {total_animes}"]},
        {"tag": "p", "children": ["Clique no título do anime para acessar via bot:"]},
        {"tag": "hr", "children": []}
    ]

    lista_items = []
    for anime in sorted(animes_encontrados, key=lambda x: x["nome"].lower()):
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
        nodes.append({"tag": "p", "children": ["Nenhum anime cadastrado nos tópicos no momento."]})

    print(f"📝 Enviando dados para a página {PATH_PAGINA} no Telegraph...")
    
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
        print(f"🎉 Catálogo atualizado com sucesso no link oficial!")
        salvar_cache(animes_encontrados)
    else:
        print(f"❌ Erro Telegraph: {resp}")

if __name__ == "__main__":
    asyncio.run(main())
