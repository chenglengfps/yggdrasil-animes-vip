import os
import json
import base64
import requests
from nacl import encoding, public

print("=== CONFIGURAÇÃO DO ECOSSISTEMA YGGDRASIL ANIMES VIP ===")

# Token do Telegraph já embutido
TELEGRAPH_TOKEN = "1728a95864f11a6f0eeb66046f2ed0c2d70e3f412f7de2a26b48dc169412"
BOT_TOKEN = "7652023850:AAFg09BA7-Detoauqk3GOR2_w2_hMWkvVc0"
GROUP_ID = "-1004388024164"
BOT_TARGET = "Quinellaadm_bot"
REPO_NAME = "yggdrasil-animes-vip"

GITHUB_TOKEN = input("Cole seu GitHub Personal Access Token (PAT): ").strip()

headers_gh = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

# 1. Autenticação no GitHub via Token
user_res = requests.get("https://api.github.com/user", headers=headers_gh)
if user_res.status_code != 200:
    print("❌ Erro ao autenticar no GitHub. Verifique seu Token.")
    exit(1)

username = user_res.json()["login"]
print(f"✅ Autenticado como: {username}")

# 2. Criar Repositório na sua conta
repo_payload = {
    "name": REPO_NAME,
    "description": "Automação do Catálogo Telegraph Yggdrasil Animes VIP",
    "private": False
}
create_repo_res = requests.post("https://api.github.com/user/repos", headers=headers_gh, json=repo_payload)

if create_repo_res.status_code in [201, 422]:
    print(f"✅ Repositório '{REPO_NAME}' pronto no GitHub!")
else:
    print(f"❌ Erro ao criar repositório: {create_repo_res.json()}")
    exit(1)

# Função para Criptografar e Adicionar Secrets no Repositório
def set_secret(secret_name, secret_value):
    key_url = f"https://api.github.com/repos/{username}/{REPO_NAME}/actions/secrets/public-key"
    key_res = requests.get(key_url, headers=headers_gh).json()
    public_key = key_res["key"]
    key_id = key_res["key_id"]

    pk = public.PublicKey(public_key.encode('utf-8'), encoding.Base64Encoder())
    sealed_box = public.SealedBox(pk)
    encrypted = sealed_box.encrypt(secret_value.encode('utf-8'))
    encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')

    secret_url = f"https://api.github.com/repos/{username}/{REPO_NAME}/actions/secrets/{secret_name}"
    payload = {"encrypted_value": encrypted_b64, "key_id": key_id}
    requests.put(secret_url, headers=headers_gh, json=payload)
    print(f"🔒 Secret '{secret_name}' adicionada com sucesso!")

# 3. Cadastrar Secrets automaticamente
set_secret("BOT_TOKEN", BOT_TOKEN)
set_secret("TELEGRAPH_TOKEN", TELEGRAPH_TOKEN)

# 4. Criar Estrutura de Arquivos Locais
os.makedirs(".github/workflows", exist_ok=True)

main_py_code = f'''import os
import re
import json
import requests
import emoji
from telegram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAPH_TOKEN = os.getenv("TELEGRAPH_TOKEN")
GROUP_ID = "{GROUP_ID}"
BOT_TARGET = "{BOT_TARGET}"
CACHE_FILE = "animes_cache.json"

def contem_emoji(texto):
    return bool(re.search(r'[\U00010000-\U0010ffff]|:\w+:', emoji.demojize(texto)))

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
    
    url_topics = f"https://api.telegram.org/bot{{BOT_TOKEN}}/getForumTopics"
    params = {{"chat_id": GROUP_ID}}
    res = requests.get(url_topics, params=params).json()

    animes_encontrados = []

    if res.get("ok") and "topics" in res.get("result", {{}}):
        topics = res["result"]["topics"]
        for topic in topics:
            nome_topico = topic.get("name", "").strip()
            
            # Pula tópicos que possuem emojis (bate-papo/avisos)
            if contem_emoji(nome_topico):
                print(f"Ignorado (Contém Emoji): {{nome_topico}}")
                continue
            
            slug = re.sub(r'[^a-zA-Z0-9_]', '_', nome_topico.lower())
            link_bot = f"https://t.me/{{BOT_TARGET}}?start={{slug}}"
            
            animes_encontrados.append({{"nome": nome_topico, "link": link_bot}})

    cache_anterior = carregar_cache()
    nomes_anteriores = [a["nome"] for a in cache_anterior]
    novos_titulos = [a["nome"] for a in animes_encontrados if a["nome"] not in nomes_anteriores]

    total_animes = len(animes_encontrados)

    nodes = [
        {{"tag": "h3", "children": ["Yggdrasil Animes VIP - Catálogo Oficial"]}},
        {{"tag": "p", "children": [f"📊 Total de animes disponíveis: {{total_animes}}"]}},
        {{"tag": "p", "children": ["Clique no título do anime para acessar via bot:"]}},
        {{"tag": "hr", "children": []}}
    ]

    lista_items = []
    for anime in sorted(animes_encontrados, key=lambda x: x["nome"]):
        lista_items.append({{
            "tag": "li",
            "children": [
                {{
                    "tag": "a",
                    "attrs": {{"href": anime["link"]}},
                    "children": [anime["nome"]]
                }}
            ]
        }})

    if lista_items:
        nodes.append({{"tag": "ul", "children": lista_items}})
    else:
        nodes.append({{"tag": "p", "children": ["Nenhum anime cadastrado no momento."]}})

    url_telegraph = "https://api.telegra.ph/createPage"
    payload = {{
        "access_token": TELEGRAPH_TOKEN,
        "title": "Yggdrasil Animes VIP",
        "author_name": "Yggdrasil VIP",
        "content": str(nodes).replace("'", '"'),
        "return_content": True
    }}
    
    resp = requests.post(url_telegraph, data=payload).json()
    if resp.get("ok"):
        catalogo_url = resp['result']['url']
        print(f"✅ Catálogo atualizado com sucesso! Link: {{catalogo_url}}")
        
        # Avisa no grupo sobre os títulos novos informando o nome do anime
        if novos_titulos:
            for novo in novos_titulos:
                msg_notificacao = f"📣 *Novo anime adicionado ao catálogo:* {{novo}}"
                url_send = f"https://api.telegram.org/bot{{BOT_TOKEN}}/sendMessage"
                payload_msg = {{
                    "chat_id": GROUP_ID,
                    "text": msg_notificacao,
                    "parse_mode": "Markdown"
                }}
                requests.post(url_send, data=payload_msg)
        
        salvar_cache(animes_encontrados)
    else:
        print(f"❌ Erro ao atualizar Telegraph: {{resp}}")

if __name__ == "__main__":
    atualizar_catalogo()
'''

with open("main.py", "w", encoding="utf-8") as f:
    f.write(main_py_code)

with open("requirements.txt", "w", encoding="utf-8") as f:
    f.write("python-telegram-bot\nrequests\nemoji\npynacl\n")

workflow_code = '''name: Atualizar Catalogo Telegraph

on:
  schedule:
    - cron: '0 * * * *'
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Baixar Código
        uses: actions/checkout@v3

      - name: Configurar Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Instalar Dependências
        run: |
          pip install -r requirements.txt

      - name: Executar Atualização
        env:
          BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
          TELEGRAPH_TOKEN: ${{ secrets.TELEGRAPH_TOKEN }}
        run: python main.py

      - name: Salvar Cache no Git
        run: |
          git config --global user.name "Yggdrasil Bot"
          git config --global user.email "bot@yggdrasil.com"
          git add animes_cache.json
          git commit -m "Atualizar cache de animes" || exit 0
          git push
'''

with open(".github/workflows/update.yml", "w", encoding="utf-8") as f:
    f.write(workflow_code)

# 5. Inicializar Git Local e Fazer Push Direto com o Token
os.system("git init")
os.system("git config user.name 'Yggdrasil Bot'")
os.system("git config user.email 'bot@yggdrasil.com'")
os.system("git add .")
os.system("git commit -m 'Setup inicial do ecossistema de catálogo'")
os.system("git branch -M main")
os.system(f"git remote add origin https://{GITHUB_TOKEN}@github.com/{username}/{REPO_NAME}.git")
os.system("git push -u origin main --force")

print("\n🚀 TUDO PRONTO! Seu repositório foi criado e subido para o GitHub com sucesso!")

