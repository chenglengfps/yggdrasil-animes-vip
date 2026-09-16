import os
import re
import json
import asyncio
import requests
import emoji
from dotenv import load_dotenv
from telethon import TelegramClient, functions
from telethon.tl.types import MessageActionTopicCreate
from telethon.sessions import StringSession

load_dotenv()

API_ID = os.getenv("API_ID", "28196030")
API_HASH = os.getenv("API_HASH", "db0ec388f4ff19cbb5ce0ce06e117566")
TELEGRAPH_TOKEN = os.getenv("TELEGRAPH_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")

if API_ID:
    API_ID = int(API_ID)

if SESSION_STRING:
    SESSION_STRING = SESSION_STRING.strip().strip("'").strip('"')

TARGET_GROUP_ID = -1004388024164
BOT_TARGET = "Quinellaadm_bot"
CACHE_FILE = "animes_cache.json"
PATH_PAGINA = "Yggdrasil-Animes-VIP-09-15"

def limpar_nome_para_slug(texto):
    texto_sem_emoji = emoji.replace_emoji(texto, replace='')
    slug = re.sub(r'[^a-zA-Z0-9_]', '_', texto_sem_emoji.strip().lower())
    slug = re.sub(r'_+', '_', slug).strip('_')
    return slug

def obter_token_telegraph():
    if TELEGRAPH_TOKEN and len(TELEGRAPH_TOKEN) > 10:
        return TELEGRAPH_TOKEN
    resp = requests.get("https://api.telegra.ph/createAccount", params={
        "short_name": "Yggdrasil",
        "author_name": "Yggdrasil VIP"
    }).json()
    if resp.get("ok"):
        return resp["result"]["access_token"]
    return TELEGRAPH_TOKEN

async def main():
    if not API_ID or not API_HASH or not SESSION_STRING:
        print("❌ Credenciais ausentes/inválidas!")
        return

    print("🔄 Conectando à Telegram API via Telethon...")
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()

    print(f"📌 Acessando grupo: {TARGET_GROUP_ID}...")
    try:
        chat_entity = await client.get_entity(TARGET_GROUP_ID)
    except Exception:
        chat_entity = None
        async for dialog in client.iter_dialogs():
            if dialog.id == TARGET_GROUP_ID:
                chat_entity = dialog.entity
                break

    if not chat_entity:
        print("❌ Grupo não localizado.")
        await client.disconnect()
        return

    print(f"🎯 Grupo carregado: {getattr(chat_entity, 'title', 'Fórum')}")
    
    dict_animes = {}

    # Método 1: GetForumTopicsRequest
    try:
        resultado = await client(functions.channels.GetForumTopicsRequest(
            channel=chat_entity,
            offset_date=0,
            offset_id=0,
            offset_topic=0,
            limit=100,
            q=''
        ))
        if getattr(resultado, 'topics', None):
            for topic in resultado.topics:
                nome = getattr(topic, 'title', '').strip()
                if nome and nome.lower() not in ["general", "geral"]:
                    dict_animes[nome] = True
    except Exception as e:
        print(f"⚠️ Erro M1: {e}")

    # Método 2 (Varredura de Ações de Criação de Tópicos nas Mensagens)
    print("🔄 Varrendo mensagens para capturar nomes dos tópicos criados...")
    try:
        async for msg in client.iter_messages(chat_entity, limit=1000):
            if isinstance(getattr(msg, 'action', None), MessageActionTopicCreate):
                nome_topico = msg.action.title.strip()
                if nome_topico and nome_topico.lower() not in ["general", "geral"]:
                    dict_animes[nome_topico] = True
            elif getattr(msg, 'reply_to', None):
                reply_info = msg.reply_to
                if getattr(reply_info, 'forum_topic', False):
                    # Captura mensagens que pertencem a tópicos
                    pass
    except Exception as e:
        print(f"⚠️ Erro M2: {e}")

    await client.disconnect()

    animes_encontrados = []
    for nome_topico in dict_animes.keys():
        slug = limpar_nome_para_slug(nome_topico) or "anime"
        link_bot = f"https://t.me/{BOT_TARGET}?start={slug}"
        animes_encontrados.append({"nome": nome_topico, "link": link_bot})

    total_animes = len(animes_encontrados)
    print(f"📊 Total de animes/tópicos encontrados: {total_animes}")

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

    token_ativo = obter_token_telegraph()
    print(f"📝 Atualizando catálogo no Telegraph...")
    
    url_telegraph = "https://api.telegra.ph/editPage"
    payload = {
        "access_token": token_ativo,
        "path": PATH_PAGINA,
        "title": "Yggdrasil Animes VIP",
        "author_name": "Yggdrasil VIP",
        "content": str(nodes).replace("'", '"'),
        "return_content": True
    }
    
    resp = requests.post(url_telegraph, data=payload).json()
    if resp.get("ok"):
        print(f"🎉 CATÁLOGO ATUALIZADO COM SUCESSO! Link: {resp['result']['url']}")
    else:
        url_create = "https://api.telegra.ph/createPage"
        payload["title"] = "Yggdrasil Animes VIP"
        resp_create = requests.post(url_create, data=payload).json()
        if resp_create.get("ok"):
            print(f"🎉 CATÁLOGO PUBLICADO COM SUCESSO! Link: {resp_create['result']['url']}")

if __name__ == "__main__":
    asyncio.run(main())
