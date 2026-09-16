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
    topicos_dict = {}
    maior_topic_id = -1

    IGNORAR_TOPICOS = [
        "general", "geral", "bate-papo", "sugestões", "sugestoes", 
        "bate papo", "chat", "regras", "avisos"
    ]

    try:
        async with app:
            print(f"📌 Varrendo historico do grupo para extrair TODOS os topicos...")
            
            # Varre o histórico de mensagens para pegar os tópicos de todas as postagens
            async for msg in app.get_chat_history(TARGET_GROUP_ID, limit=3000):
                # Tenta pegar informacoes de forum/topico da mensagem
                reply_to = getattr(msg, "reply_to_message", None)
                thread_id = getattr(msg, "message_thread_id", None)
                
                nome_topico = None
                topic_id = thread_id

                # Se for mensagem de criacao de topico
                if msg.service and hasattr(msg, "forum_topic_created") and msg.forum_topic_created:
                    nome_topico = msg.forum_topic_created.title
                    topic_id = msg.id

                # Se a mensagem pertence a um topico e ainda nao temos o nome dele
                if topic_id and topic_id not in topicos_unicos:
                    if not nome_topico and reply_to and hasattr(reply_to, "forum_topic_created") and reply_to.forum_topic_created:
                        nome_topico = reply_to.forum_topic_created.title

                if topic_id and nome_topico and topic_id not in topicos_unicos:
                    nome_limpo = emoji.replace_emoji(nome_topico, replace='').strip().lower()
                    if any(termo in nome_limpo for termo in IGNORAR_TOPICOS):
                        continue

                    topicos_unicos.add(topic_id)
                    topicos_dict[topic_id] = nome_topico

            # Varredura complementar via get_forum_topics para garantir
            try:
                async for topic in app.get_forum_topics(TARGET_GROUP_ID):
                    t_id = getattr(topic, "id", None)
                    t_title = getattr(topic, "title", "").strip()
                    if t_id and t_title and t_id not in topicos_unicos:
                        nome_limpo = emoji.replace_emoji(t_title, replace='').strip().lower()
                        if not any(termo in nome_limpo for termo in IGNORAR_TOPICOS):
                            topicos_unicos.add(t_id)
                            topicos_dict[t_id] = t_title
            except Exception as ex_tp:
                print(f"⚠️ Aviso no get_forum_topics: {ex_tp}")

            for t_id, t_nome in topicos_dict.items():
                if t_id > maior_topic_id:
                    maior_topic_id = t_id

                slug = limpar_nome_para_slug(t_nome) or "anime"
                link_bot = f"https://t.me/{BOT_TARGET}?start={slug}"
                animes_encontrados.append({
                    "id": t_id,
                    "nome": t_nome,
                    "link": link_bot
                })

    except Exception as e:
        print(f"❌ Erro de execução no Hydrogram: {e}")

    total_animes = len(animes_encontrados)
    print(f"📊 Total de animes encontrados: {total_animes}")

    if total_animes == 0:
        print("⚠️ NENHUM ANIME ENCONTRADO! Abortando atualização para proteger o catálogo atual.")
        return

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

    nodes.append({"tag": "ul", "children": lista_items})

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

    if resp.get("ok"):
        print(f"🎉 CATÁLOGO ATUALIZADO COM SUCESSO! Link: {resp['result']['url']}")
    else:
        print(f"⚠️ Erro no Telegraph: {resp}")

if __name__ == "__main__":
    asyncio.run(main())
