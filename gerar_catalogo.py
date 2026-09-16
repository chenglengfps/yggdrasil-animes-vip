import os
import re
import json
import asyncio
import requests
import emoji
from dotenv import load_dotenv
from hydrogram import Client

load_dotenv()

API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
TELEGRAPH_TOKEN = os.getenv("TELEGRAPH_TOKEN")
SESSION_STRING = os.getenv("SESSION_STRING")

if API_ID:
    API_ID = int(API_ID)

if SESSION_STRING:
    SESSION_STRING = SESSION_STRING.strip().strip("'").strip('"').replace("\n", "").replace("\r", "")

TARGET_GROUP_ID = -1004388024164
BOT_TARGET = "Quinellaadm_bot"
# Path fixo do catálogo no Telegraph
PATH_PAGINA = "Lista-de-animes-09-16-4"

def limpar_nome_para_slug(texto):
    texto_sem_emoji = emoji.replace_emoji(texto, replace='')
    slug = re.sub(r'[^a-zA-Z0-9_]', '_', texto_sem_emoji.strip().lower())
    slug = re.sub(r'_+', '_', slug).strip('_')
    return slug

async def main():
    if not API_ID or not API_HASH or not SESSION_STRING:
        print("❌ Credenciais API_ID, API_HASH ou SESSION_STRING ausentes!")
        return

    print("🔄 Conectando à Telegram API via Hydrogram...")
    try:
        app = Client(
            "yggdrasil_userbot",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=SESSION_STRING,
            in_memory=True
        )
    except Exception as err:
        print(f"❌ Erro na criação do cliente Hydrogram: {err}")
        return

    animes_encontrados = []
    topicos_unicos = set()

    try:
        async with app:
            print(f"📌 Buscando tópicos do grupo: {TARGET_GROUP_ID}...")
            async for topic in app.get_forum_topics(TARGET_GROUP_ID):
                nome_topico = getattr(topic, 'title', '').strip()
                topic_id = getattr(topic, 'id', None)

                if not nome_topico or topic_id in topicos_unicos:
                    continue

                topicos_unicos.add(topic_id)

                if nome_topico.lower() in ["general", "geral"]:
                    continue

                print(f"🔹 Tópico encontrado: {nome_topico}")

                slug = limpar_nome_para_slug(nome_topico) or "anime"
                link_bot = f"https://t.me/{BOT_TARGET}?start={slug}"
                animes_encontrados.append({"nome": nome_topico, "link": link_bot})

    except Exception as e:
        print(f"❌ Erro de execução no Hydrogram: {e}")

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

    print(f"📝 Atualizando página fixa no Telegraph ({PATH_PAGINA})...")
    url_telegraph = "https://api.telegra.ph/editPage"
    payload = {
        "access_token": TELEGRAPH_TOKEN,
        "path": PATH_PAGINA,
        "title": "Lista de animes",
        "author_name": "Yggdrasil VIP",
        "content": str(nodes).replace("'", '"'),
        "return_content": True
    }
    
    resp = requests.post(url_telegraph, data=payload).json()
    
    # Se por algum motivo o path não for encontrado, faz o fallback seguro para criação
    if not resp.get("ok") and resp.get("error") in ["PAGE_ACCESS_DENIED", "PATH_INVALID"]:
        print("⚠️ Erro ao editar path padrão. Tentando recriar página...")
        url_create = "https://api.telegra.ph/createPage"
        payload_create = {
            "access_token": TELEGRAPH_TOKEN,
            "title": "Lista de animes",
            "author_name": "Yggdrasil VIP",
            "content": str(nodes).replace("'", '"'),
            "return_content": True
        }
        resp = requests.post(url_create, data=payload_create).json()

    if resp.get("ok"):
        print(f"🎉 CATÁLOGO ATUALIZADO COM SUCESSO! Link: {resp['result']['url']}")
    else:
        print(f"⚠️ Erro no Telegraph: {resp}")

if __name__ == "__main__":
    asyncio.run(main())
