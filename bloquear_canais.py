import time
from telethon import TelegramClient
from telethon.tl import functions, types
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantCreator

# Suas credenciais do Telegram
API_ID = "28196030"
API_HASH = "db0ec388f4ff19cbb5ce0ce06e117566"

client = TelegramClient('sessao_userbot', API_ID, API_HASH)

async def main():
    print("Conectando ao Telegram e fazendo a varredura dos seus canais...")
    
    canais_para_bloquear = []

    # Passo 1: Varredura para filtrar apenas onde você é o CRIADOR (Dono)
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        
        if isinstance(entity, types.Channel):
            try:
                me = await client(GetParticipantRequest(
                    channel=entity,
                    participant='me'
                ))
                
                if isinstance(me.participant, ChannelParticipantCreator):
                    canais_para_bloquear.append(entity)
                    print(f"[ENCONTRADO - DONO] {dialog.title}")
            except Exception:
                continue

    print(f"\nVarredura concluída. Encontrados {len(canais_para_bloquear)} canais/grupos onde você é dono.")
    print("Aplicando a proteção contra encaminhamento...\n")

    # Passo 2: Ativa o NoForwards em cada canal de forma segura
    for entity in canais_para_bloquear:
        try:
            # Ativa a proteção contra encaminhamento/cópia de conteúdo (NoForwards)
            await client(functions.messages.ToggleNoForwardsRequest(
                peer=entity,
                enabled=True
            ))
            
            print(f"[SUCESSO] Encaminhamento bloqueado em: {entity.title}")
            
        except Exception as e:
            print(f"[AVISO] Não foi possível alterar '{entity.title}': {e}")
        
        # Delay obrigatório de 5 segundos entre as requisições
        print("Aguardando 5 segundos...")
        time.sleep(5)

    print("\nProcesso concluído com sucesso!")

with client:
    client.loop.run_until_complete(main())

