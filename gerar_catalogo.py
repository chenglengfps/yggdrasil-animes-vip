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
JSON_FILE = "catalogo_memoria.json"

def limpar_nome_para_slug(texto):
    texto_sem_emoji = emoji.replace_emoji(texto, replace='')
    slug = re.sub(r'[^a-zA-Z0-9_]', '_', texto_sem_emoji.strip().lower())
    slug = re.sub(r'_+', '_', slug).strip('_')
    return slug

def carregar_memoria():
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Erro ao ler {JSON_FILE}: {e}")
    return {}

def salvar_memoria(dados):
    try:
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Erro ao salvar {JSON_FILE}: {e}")

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

    IGNORAR_TOPICOS = [
        "general", "geral", "bate-papo", "sugestões", "sugestoes", 
        "bate papo", "chat", "regras", "avisos"
    ]

    memoria_animes = carregar_memoria()
    e_primeira_execucao = (len(memoria_animes) == 0)
    novos_animes_detectados = []

    try:
        async with app:
            print(f"📌 Buscando novos tópicos no grupo: {TARGET_GROUP_ID}...")
            
            async for topic in app.get_forum_topics(TARGET_GROUP_ID):
                nome_topico = getattr(topic, 'title', '').strip()
                topic_id = getattr(topic, 'id', None)

                if not nome_topico or not topic_id:
                    continue

                str_id = str(topic_id)
                nome_limpo = emoji.replace_emoji(nome_topico, replace='').strip().lower()
                
                if any(termo in nome_limpo for termo in IGNORAR_TOPICOS):
                    continue

                slug = limpar_nome_para_slug(nome_topico) or "anime"
                link_bot = f"https://t.me/{BOT_TARGET}?start={slug}"
                
                # Link direto para o tópico dentro do grupo VIP
                grupo_clean_id = str(TARGET_GROUP_ID).replace("-100", "")
                link_topico_direto = f"https://t.me/c/{grupo_clean_id}/{topic_id}"

                item_anime = {
                    "id": topic_id,
                    "nome": nome_topico,
                    "link_bot": link_bot,
                    "link_direto": link_topico_direto
                }

                # Se o tópico ainda não consta na memória local
                if str_id not in memoria_animes:
                    memoria_animes[str_id] = item_anime
                    if not e_primeira_execucao:
                        novos_animes_detectados.append(item_anime)

            # Notificações no grupo Telegram
            if e_primeira_execucao:
                msg_teste = "✅ **O bot foi configurado com sucesso!**\n\n A partir de agora, o catálogo será atualizado automaticamente e novos animes serão notificados aqui no grupo."
                try:
                    await app.send_message(TARGET_GROUP_ID, msg_teste)
                    print("📢 Mensagem de teste enviada com sucesso no grupo VIP!")
                except Exception as ex_msg:
                    print(f"⚠️ Não foi possível enviar a mensagem no grupo: {ex_msg}")
            else:
                for novo in novos_animes_detectados:
                    msg_novo = (
                        f"🎉 **Novo anime disponível, acompanhe já!**\n\n"
                        f"📺 **{novo['nome']}**\n"
                        f"🔗 [Clique aqui para acessar o tópico]({novo['link_direto']})"
                    )
                    try:
                        await app.send_message(TARGET_GROUP_ID, msg_novo, disable_web_page_preview=True)
                        print(f"📢 Notificação enviada no grupo para: {novo['nome']}")
                    except Exception as ex_novo:
                        print(f"⚠️ Erro ao enviar notificação de novo anime: {ex_novo}")

    except Exception as e:
        print(f"❌ Erro de execução no Hydrogram: {e}")

    salvar_memoria(memoria_animes)

    animes_encontrados = list(memoria_animes.values())
    total_animes = len(animes_encontrados)
    print(f"📊 Total acumulado de animes na memória: {total_animes}")

    if total_animes == 0:
        print("⚠️ Nenhum anime na memória. Abortando atualização do Telegraph.")
        return

    # Descobre o ID mais alto para marcar com "🆕 NOVO"
    maior_topic_id = max([a["id"] for a in animes_encontrados]) if animes_encontrados else -1

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
                "attrs": {"href": anime["link_bot"]},
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
