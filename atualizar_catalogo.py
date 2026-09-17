import os
import json
import re
import asyncio
import emoji
from dotenv import load_dotenv
from pyrogram import Client
from pyrogram.raw import functions
from telegraph import Telegraph

load_dotenv()

# Tenta ler das Secrets ou .env
API_ID_RAW = os.getenv("API_ID", "0")
API_ID = int(API_ID_RAW) if API_ID_RAW.isdigit() else 0
API_HASH = os.getenv("API_HASH", "")
PYROGRAM_SESSION = os.getenv("PYROGRAM_SESSION") or os.getenv("SESSION_STRING", "")
TELEGRAPH_TOKEN = os.getenv("TELEGRAPH_TOKEN", "")
CHAT_ID_RAW = os.getenv("CHAT_ID", "0")
CHAT_ID = int(CHAT_ID_RAW) if CHAT_ID_RAW.lstrip('-').isdigit() else 0

BOT_TARGET = "Quinellaadm_bot"
PATH_PAGINA = "Lista-de-animes-09-16-4"
JSON_FILE = "catalogo_memoria.json"

IGNORAR_TOPICOS = [
    "general", "geral", "bate-papo", "sugestões", "sugestoes", 
    "bate papo", "chat", "regras", "avisos"
]

def limpar_nome_para_slug(texto):
    texto_sem_emoji = emoji.replace_emoji(texto, replace='')
    slug = re.sub(r'[^a-zA-Z0-9_]', '_', texto_sem_emoji.strip().lower())
    slug = re.sub(r'_+', '_', slug).strip('_')
    return slug

async def main():
    print("🔎 Verificando credenciais carregadas...")
    print(f"-> API_ID: {API_ID}")
    print(f"-> API_HASH presente: {bool(API_HASH)}")
    print(f"-> PYROGRAM_SESSION presente: {bool(PYROGRAM_SESSION)}")
    print(f"-> TELEGRAPH_TOKEN presente: {bool(TELEGRAPH_TOKEN)}")
    print(f"-> CHAT_ID: {CHAT_ID}")

    if not API_ID or not API_HASH or not PYROGRAM_SESSION or not CHAT_ID:
        raise ValueError("❌ Uma ou mais Secrets/variáveis obrigatórias estão ausentes no GitHub Actions!")

    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r", encoding="utf-8") as f:
            memoria = json.load(f)
    else:
        memoria = {}

    novos_animes = []

    app = Client("ygg_userbot", api_id=API_ID, api_hash=API_HASH, session_string=PYROGRAM_SESSION, in_memory=True)

    async with app:
        chat_obj = await app.get_chat(CHAT_ID)
        peer = await app.resolve_peer(chat_obj.id)
        
        offset_date = 0
        offset_id = 0
        offset_topic_id = 0
        limit = 100
        todos_topicos = []

        while True:
            res = await app.invoke(
                functions.channels.GetForumTopics(
                    channel=peer,
                    q="",
                    offset_date=offset_date,
                    offset_id=offset_id,
                    offset_topic=offset_topic_id,
                    limit=limit
                )
            )

            if not res.topics:
                break

            todos_topicos.extend(res.topics)

            if len(res.topics) < limit:
                break

            ultimo = res.topics[-1]
            offset_topic_id = ultimo.id
            offset_id = getattr(ultimo, "top_message", 0)
            offset_date = getattr(ultimo, "date", 0)

        todos_topicos.sort(key=lambda x: getattr(x, 'id', 0))

        vistos_slugs = {limpar_nome_para_slug(v["nome"]) for v in memoria.values()}

        for topic in todos_topicos:
            nome_topico = getattr(topic, 'title', '').strip()
            topic_id = getattr(topic, 'id', None)

            if not nome_topico or not topic_id:
                continue

            nome_limpo = emoji.replace_emoji(nome_topico, replace='').strip().lower()
            if any(termo in nome_limpo for termo in IGNORAR_TOPICOS):
                continue

            slug = limpar_nome_para_slug(nome_topico)
            str_id = str(topic_id)

            if slug not in vistos_slugs and str_id not in memoria:
                item = {
                    "id": topic_id,
                    "nome": nome_topico,
                    "link_bot": f"https://t.me/{BOT_TARGET}?start={slug}",
                    "link_direto": ""
                }
                memoria[str_id] = item
                vistos_slugs.add(slug)
                novos_animes.append(item)

        if novos_animes:
            print(f"✨ {len(novos_animes)} novo(s) anime(s) encontrado(s)!")

            with open(JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(memoria, f, ensure_ascii=False, indent=2)

            html = f"<h3>Yggdrasil Animes VIP - Catálogo Oficial</h3><p>📊 Total de animes disponíveis: {len(memoria)}</p><p>Clique no título para acessar via bot:</p><hr><ul>"
            for a in sorted(memoria.values(), key=lambda x: x["nome"].lower()):
                html += f'<li><a href="{a["link_bot"]}">{a["nome"]}</a></li>'
            html += "</ul>"

            t = Telegraph(access_token=TELEGRAPH_TOKEN)
            t.edit_page(path=PATH_PAGINA, title="Lista de Animes", html_content=html, author_name="Yggdrasil VIP")
            print("🎉 Telegraph atualizado!")

            for a in novos_animes:
                msg = (
                    f"🆕 **NOVO ANIME ADICIONADO AO CATÁLOGO!**\n\n"
                    f"📌 **Nome:** {a['nome']}\n"
                    f"🤖 **Acesse via Bot:** {a['link_bot']}\n\n"
                    f"📖 **Catálogo Completo:** https://telegra.ph/{PATH_PAGINA}"
                )
                await app.send_message(CHAT_ID, msg)
                print(f"📢 Aviso enviado no grupo: {a['nome']}")
        else:
            print("✅ Nenhum novo anime. Tudo atualizado!")

if __name__ == "__main__":
    asyncio.run(main())
