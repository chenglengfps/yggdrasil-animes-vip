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
    print("Conectando ao Telegram e escaneando seus canais...")
    
    canais_do_usuario = []

    # Passo 1: Varredura para filtrar apenas os canais onde você é o CRIADOR (Dono)
    async for dialog in client.iter_dialogs():
        entity = dialog.entity
        
        if isinstance(entity, types.Channel):
            try:
                me = await client(GetParticipantRequest(
                    channel=entity,
                    participant='me'
                ))
                
                if isinstance(me.participant, ChannelParticipantCreator):
                    canais_do_usuario.append(entity)
                    print(f"[ENCONTRADO - DONO] {dialog.title}")
            except Exception:
                continue

    print(f"\nVarredura concluída. Encontrados {len(canais_do_usuario)} canais onde você é dono.")
    
    # -------------------------------------------------------------
    # ETAPA 1: Desativar a aprovação de novos membros em cada canal
    # -------------------------------------------------------------
    print("\n--- ETAPA 1: Desativando a exigência de aprovação de novos membros ---")
    
    for entity in canais_do_usuario:
        try:
            await client(functions.channels.ToggleJoinRequests(
                channel=entity,
                enabled=False
            ))
            print(f"[SUCESSO] Aprovação desativada em: {entity.title}")
        except Exception as e:
            print(f"[AVISO] Não foi possível alterar '{entity.title}': {e}")
        
        # Delay de 5 segundos
        print("Aguardando 5 segundos...")
        time.sleep(5)

    # -------------------------------------------------------------
    # ETAPA 2: Verificar solicitações pendentes e aceitar todas
    # -------------------------------------------------------------
    print("\n--- ETAPA 2: Verificando e aceitando solicitações pendentes ---")

    for entity in canais_do_usuario:
        try:
            requests = await client(functions.messages.GetChatInviteImportersRequest(
                peer=entity,
                requested=True,
                limit=100
            ))
            
            if requests.users:
                print(f"[ANALISANDO] '{entity.title}': Encontradas {len(requests.users)} solicitações pendentes.")
                
                for user in requests.users:
                    try:
                        await client(functions.messages.HideChatJoinRequestRequest(
                            peer=entity,
                            user_id=user,
                            approved=True
                        ))
                    except Exception as sub_e:
                        print(f"  -> Erro ao aceitar usuário no canal '{entity.title}': {sub_e}")
                
                print(f"[SUCESSO] Todas as solicitações de '{entity.title}' foram aceitas.")
            else:
                print(f"[INFO] '{entity.title}': Nenhuma solicitação pendente.")
                
        except Exception as e:
            print(f"[AVISO] Erro ao checar solicitações em '{entity.title}': {e}")
        
        # Delay de 5 segundos entre os canais
        print("Aguardando 5 segundos...")
        time.sleep(5)

    print("\nProcesso completo finalizado com sucesso para todos os seus canais!")

with client:
    client.loop.run_until_complete(main())

