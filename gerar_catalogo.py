import os
import re
import json
import asyncio
import requests
import emoji
from dotenv import load_dotenv
from hydrogram import Client
from hydrogram.raw import functions

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
    maior_topic_id = -1

    IGNORAR_TOPICOS = [
        "general", "geral", "bate-papo", "sugestões", "sugestoes", 
        "bate papo", "chat", "regras", "avisos"
    ]

    try:
        async with app:
            print(f"📌 Buscando TODOS os tópicos via paginação MTProto raw...")
            peer = await app.resolve_peer(TARGET_GROUP_ID)
            
            offset_date = 0
            offset_id = 0
            offset_topic_id = 0
            
            while True:
                # Chamada de baixo nível da API Telegram com offset correto
                res = await app.invoke(
                    functions.channels.GetForumTopics(
                        channel=peer,
                        offset_date=offset_date,
                        offset_id=offset_id,
                        offset_topic_id=offset_topic_id,
                        limit=100
                    )
                )

                if not res.topics:
                    break

                for topic in res.topics:
                    topic_id = getattr(topic, 'id', None)
                    nome_topico = getattr(topic, 'title', '').strip()

                    if not nome_topico or topic_id in topicos_unicos:
                        continue

                    topicos_unicos.add(topic_id)

                    nome_limpo = emoji.replace_emoji(nome_topico, replace='').strip().lower()
                    if any(termo in nome_limpo for termo in IGNORAR_TOPICOS):
                        print(f"🚫 Ignorando tópico de bate-papo: {nome_topico}")
                        continue

                    if topic_id and topic_id > maior_topic_id:
                        maior_topic_id = topic_id

                    slug = limpar_nome_para_slug(nome_topico) or "anime"
                    link_bot = f"https://t.me/{BOT_TARGET}?start={slug}"

                    animes_encontrados.append({
                        "id": topic_id,
                        "nome": nome_topico,
                        "link": link_bot
                    })

                # Prepara o offset para buscar a próxima página de tópicos
                last_topic = res.topics[-1]
                offset_topic_id = last_topic.id
                offset_id = getattr(last_topic, 'top_message', 0)
                
                # Para quando a lista retornada for menor que o limite (fim dos tópicos)
                if len(res.topics) < 100:
                    break

    except Exception as e:
        print(f"❌ Erro de execução no Hydrogram RAW: {e}")

    total_animes = len(animes_encontrados)
    print(f"📊 Total real de animes encontrados: {total_animes}")

    nodes = [
        {"tag": "h3", "children": ["Yggdrasil Animes VIP - Catálogo Oficial"]},
        {"tag": "p", "children": [f"📊 Total de animes disponíveis: {total_animes}"]},
        {"tag": "p", "children": ["Clique no título do anime para acessar via bot:"]},
        {"tag": "hr", "children": []}
    ]

    lista_items = []
    for anime in sorted(animes_encontrados, key=lambda x: x["nome"].lower()):
        e_novo = (anime["id"] == maior_topic_id)

        children_elements = [
            {
                "tag": "a",
                "attrs": {"href": anime["link"]},
                "children": [anime["nome"]]
            }
        ]

        if e_novo:
            children_elements.append(" ")
            children_elements.append({
                "tag": "b",
                "children": ["🆕 NOVO"]
            })

        lista_items.append({
            "tag": "li",
            "children": children_elements
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
