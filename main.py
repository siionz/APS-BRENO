from colorama import init, Fore, Style
import pyfiglet
import os
import time
import hashlib
import json
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table
import datetime

# >>> ALTERAÇÃO: integrações de criptografia simétrica (Fernet) e MQTT
from cryptography.fernet import Fernet  # criptografia reversível
import paho.mqtt.client as mqtt         # comunicação MQTT

# -------------------------
# inicializações
# -------------------------
init(autoreset=True)  # >>> ALTERAÇÃO: autoreset para não “prender” cor no terminal
console = Console()

arquivoUser = "usuarios.json"
arquivoMsgs = "mensagens.json"  # (mantido, mas não é mais usado como “lista”; ver salvarMensagemJson)
arquivoChave = "chave.key"      # >>> ALTERAÇÃO: arquivo para armazenar a chave Fernet

# >>> ALTERAÇÃO: função utilitária para carregar/gerar chave Fernet
def carregar_ou_gerar_chave():
    """
    Carrega a chave Fernet de 'chave.key' ou gera uma nova se não existir.
    A MESMA chave deve estar presente em todas as máquinas que trocam mensagens.
    """
    if os.path.exists(arquivoChave):
        with open(arquivoChave, "rb") as f:
            return f.read()
    chave = Fernet.generate_key()
    with open(arquivoChave, "wb") as f:
        f.write(chave)
    return chave

# instância global do fernet (compartilhada por envio/recebimento)
FERNET = Fernet(carregar_ou_gerar_chave())

# >>> ALTERAÇÃO: SHA-256 continua para SENHAS; salt agora é pedido só 1x e usado para senha
salt_digitado = input("Insira um salt (para senhas): ").strip()

# -------------------------
# utilitários de sistema
# -------------------------
def LimparTela():
    # >>> ALTERAÇÃO: compatível com Windows e Linux/Mac
    os.system('cls' if os.name == 'nt' else 'clear')

def titulo(texto):
    banner = pyfiglet.figlet_format(texto, font="slant")
    console.print(f"[bold blue]{banner}[/bold blue]")

# -------------------------
# persistência JSON
# -------------------------
def carregarJson(arquivo):
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {} if arquivo == arquivoUser else []

def salvar_dados(arquivo, dados):
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)

# -------------------------
# segurança: senhas (SHA-256 + salt)
# -------------------------
def criptografarSenha(senha):
    """
    Gera hash SHA-256 da senha com salt (IRREVERSÍVEL) — para autenticação.
    """
    senhaComSalt = senha + salt_digitado
    return hashlib.sha256(senhaComSalt.encode()).hexdigest()

def verificarSenha(senhaDigitada, hashArmazenado):
    return criptografarSenha(senhaDigitada) == hashArmazenado

# -------------------------
# segurança: mensagens (Fernet) + integridade (SHA-256 da mensagem)
# -------------------------
def hash_mensagem(msg: str, salt: str = "") -> str:
    """
    Gera hash SHA-256 da mensagem (opcionalmente com sal adicional).
    Serve para demonstrar integridade no relatório.
    """
    return hashlib.sha256((msg + salt).encode('utf-8')).hexdigest()

# >>> ALTERAÇÃO: criptografia reversível para MENSAGENS (Fernet)
def cifrar_mensagem(msg: str) -> str:
    """
    Cifra a mensagem com Fernet (reversível). Retorna base64 (str).
    """
    return FERNET.encrypt(msg.encode()).decode()

def decifrar_mensagem(msg_cripto: str) -> str:
    """
    Decifra a mensagem com Fernet (reversível). Recebe base64 (str).
    """
    return FERNET.decrypt(msg_cripto.encode()).decode()

# -------------------------
# fluxo de login e usuários
# -------------------------
def loginUser():
    LimparTela()
    titulo("Login de Usuários")
    usuarios = carregarJson(arquivoUser)
    username_digitado = input(Fore.CYAN + "\nDigite seu username: " + Style.RESET_ALL).strip()
    senha = input(Fore.CYAN + "Digite sua senha: " + Style.RESET_ALL).strip()

    for userId, user in usuarios.items():
        if user.get('username') == username_digitado:
            if verificarSenha(senha, user.get('passwordHash', '')):
                console.print("\n[bold green]✔ Login realizado com sucesso![/bold green]")
                time.sleep(1)
                tipo = user.get('tipo', 'usuario').lower()
                return {"id": userId, "username": username_digitado, "tipo": tipo}

            console.print("\n[bold red]Senha incorreta. Tente novamente.[/bold red]")
            time.sleep(2)
            return None

    console.print("[bold red]Usuário não encontrado.[/bold red]")
    time.sleep(2)
    return None

def adicionarUsers():
    LimparTela()
    titulo("ADICIONAR USUÁRIOS")
    usuarios = carregarJson(arquivoUser)
    if not isinstance(usuarios, dict):
        usuarios = {}

    username = input(Fore.CYAN + "Digite o username do novo usuário: " + Style.RESET_ALL).strip()
    if any(u.get('username') == username for u in usuarios.values()):
        console.print("[bold red]Username já existe. Tente novamente.[/bold red]")
        time.sleep(2)
        return

    senha = input(Fore.CYAN + "Digite a senha do novo usuário: " + Style.RESET_ALL).strip()
    tipo = input(Fore.CYAN + "Digite o tipo do usuário (admin/usuario): " + Style.RESET_ALL).strip().lower()  # >>> ALTERAÇÃO: () faltavam no .lower
    senha_hash = criptografarSenha(senha)
    novo_id = str(len(usuarios) + 1)
    usuarios[novo_id] = {
        'username': username,
        'passwordHash': senha_hash,
        'tipo': tipo if tipo in ['admin', 'usuario'] else 'usuario'
    }
    salvar_dados(arquivoUser, usuarios)
    console.print(f"[bold green]Usuário '{username}' adicionado com sucesso![/bold green]")
    time.sleep(2)

def modificarUser():
    LimparTela()
    titulo("MODIFICAR USUÁRIOS")
    usuarios = carregarJson(arquivoUser)
    if not usuarios:
        console.print("[bold red]Nenhum usuário cadastrado.[/bold red]")
        time.sleep(2)
        return

    for uid, dados in usuarios.items():
        console.print(f"ID: [yellow]{uid}[/yellow] | Usuário: [magenta]{dados.get('username','')}[/magenta] | Tipo: [green]{dados.get('tipo','usuario')}[/green]")

    uid = input(Fore.CYAN + "\nDigite o ID do usuário que deseja modificar: " + Style.RESET_ALL).strip()
    if uid not in usuarios:
        console.print("[bold red]Usuário não encontrado.[/bold red]")
        time.sleep(2)
        return

    user = usuarios[uid]
    novo_username = input(Fore.CYAN + f"Novo username (Enter p/ manter '{user.get('username','')}'): " + Style.RESET_ALL).strip()
    nova_senha = input(Fore.CYAN + "Nova senha (Enter p/ manter): " + Style.RESET_ALL).strip()
    novo_tipo = input(Fore.CYAN + f"Novo tipo (admin/usuario) (Enter p/ manter '{user.get('tipo','usuario')}'): " + Style.RESET_ALL).strip().lower()

    if novo_username:
        if any(d.get('username') == novo_username for k, d in usuarios.items() if k != uid):
            console.print("[bold red]Username já existe.[/bold red]"); time.sleep(2); return
        user['username'] = novo_username
    if nova_senha:
        user['passwordHash'] = criptografarSenha(nova_senha)
    if novo_tipo in ['admin', 'usuario']:
        user['tipo'] = novo_tipo

    salvar_dados(arquivoUser, usuarios)
    console.print("[bold green]Usuário modificado com sucesso![/bold green]")
    time.sleep(2)

def excluirUsers():
    LimparTela()
    titulo("EXCLUIR USUÁRIOS")
    usuarios = carregarJson(arquivoUser)
    if not usuarios:
        console.print("[bold red]Nenhum usuário cadastrado.[/bold red]")
        time.sleep(2)
        return

    table = Table(title="[bold cyan]Usuários Cadastrados[/bold cyan]", title_style="bold cyan")
    table.add_column("ID", justify="center", style="bright_cyan", no_wrap=True)
    table.add_column("Username", justify="center", style="magenta")
    table.add_column("Tipo", justify="center", style="green")
    for userId, dados in usuarios.items():
        table.add_row(userId, dados.get('username', ''), dados.get('tipo', 'usuario'))
    console.print(table)

    userIdExcluir = Prompt.ask("\n[bold yellow]Digite o ID do usuário que deseja excluir[/bold yellow]").strip()

    # >>> ALTERAÇÃO: corrigido bug (usava 'userId' errado na verificação)
    if userIdExcluir not in usuarios:
        console.print("[bold red]Usuário não encontrado.[/bold red]")
        time.sleep(2)
        return

    confirm = Prompt.ask(f"Tem certeza que deseja excluir '{usuarios[userIdExcluir]['username']}'? (s/n)", default="n").lower()
    if confirm == 's':
        del usuarios[userIdExcluir]
        salvar_dados(arquivoUser, usuarios)
        console.print("[bold green]Usuário excluído com sucesso![/bold green]")
    else:
        console.print("[bold yellow]Operação cancelada.[/bold yellow]")
    time.sleep(2)

def gerenciamentoUser():
    while True:
        LimparTela()
        titulo("GERENCIAMENTO DE USUÁRIOS")
        console.print("[1] - Adicionar\n[2] - Modificar\n[3] - Excluir\n[4] - Voltar")
        try:
            result = int(input("➤ "))
        except ValueError:
            console.print(Fore.RED + "Digite um número válido"); time.sleep(1); continue

        if result == 1:
            adicionarUsers()
        elif result == 2:
            modificarUser()
        elif result == 3:
            excluirUsers()
        elif result == 4:
            break
        else:
            console.print(Fore.RED + "Digite algo válido")
    LimparTela()

# -------------------------
# MQTT + Fernet (envio/recebimento)
# -------------------------
BROKER_PADRAO = "test.mosquitto.org"

# >>> ALTERAÇÃO: salvar cada mensagem em ARQUIVO INDIVIDUAL (envio e recepção)
def salvarMensagemJson(remetente, destinatario, msg_plain, msg_cripto, topico, broker, direcao="enviada"):
    """
    Antes: acumulava tudo em 'mensagens.json' (lista).
    Agora: salva CADA mensagem em um arquivo JSON separado.
    'direcao' = 'enviada' ou 'recebida' (usado no nome do arquivo).
    """
    # >>> ALTERAÇÃO: cria nome único com microsegundos para evitar colisão
    nome_arquivo = f"msg_{direcao}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"

    registro = {
        "direcao": direcao,                          # enviada/recebida
        "remetente": remetente,
        "destinatario": destinatario,
        "mensagem_plain": msg_plain,                 # OBS: útil para relatório escolar
        "mensagem_cripto": msg_cripto,
        "hash_plain": hash_mensagem(msg_plain),      # demonstra integridade (opcional)
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "topico": topico,
        "broker": broker
    }

    with open(nome_arquivo, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)

    console.print(f"[dim]Arquivo salvo:[/dim] {nome_arquivo}")

# >>> ALTERAÇÃO: envio CRIPTOGRAFADO + salvamento individual
def enviarMensagem(usuario_logado):
    """
    Permite enviar mensagem criptografada via MQTT para um destinatário (por tópico).
    Qualquer usuário logado pode enviar.
    """
    LimparTela()
    titulo("ENVIAR MENSAGEM (CRIPTOGRAFADA)")

    broker = Prompt.ask("[cyan]Broker[/cyan] (Enter p/ padrão)", default=BROKER_PADRAO)
    destinatario = Prompt.ask("Destinatário (username)")
    topico = f"minharede/chat/{destinatario}"

    cliente = mqtt.Client()
    cliente.connect(broker, 1883, 60)
    cliente.loop_start()

    console.print(f"[green]Publicando em:[/green] {topico}")
    console.print("[dim]Digite 'sair' para encerrar[/dim]")

    try:
        while True:
            msg = input(f"{usuario_logado['username']}: ").strip()
            if not msg:
                continue

            # cifra com Fernet
            msg_cripto = cifrar_mensagem(msg)  # >>> ALTERAÇÃO: cifrando antes de enviar
            cliente.publish(topico, msg_cripto)

            # >>> ALTERAÇÃO: salva CADA mensagem em um arquivo JSON separado (direcao='enviada')
            salvarMensagemJson(
                remetente=usuario_logado['username'],
                destinatario=destinatario,
                msg_plain=msg,
                msg_cripto=msg_cripto,
                topico=topico,
                broker=broker,
                direcao="enviada"
            )

            if msg.lower() == "sair":
                break
    except KeyboardInterrupt:
        pass
    finally:
        cliente.loop_stop()
        cliente.disconnect()

# >>> ALTERAÇÃO: recepção + DESCRIPTOGRAFIA + salvamento individual
def receberMensagem(usuario_logado):
    """
    Assina o tópico do usuário logado e descriptografa mensagens recebidas com Fernet.
    Cada mensagem recebida também é salva em um arquivo JSON separado.
    """
    LimparTela()
    titulo(f"RECEBER MENSAGENS ({usuario_logado['username']})")

    broker = Prompt.ask("[cyan]Broker[/cyan] (Enter p/ padrão)", default=BROKER_PADRAO)
    topico = f"minharede/chat/{usuario_logado['username']}"

    def on_message(client, userdata, message):
        try:
            msg_cripto = message.payload.decode()
            msg = decifrar_mensagem(msg_cripto)  # >>> ALTERAÇÃO: decifrando ao receber
            hora = datetime.datetime.now().strftime("%H:%M:%S")
            console.print(f"[{hora}] [bold green]Mensagem:[/bold green] {msg}")

            # >>> ALTERAÇÃO: salvar cada mensagem RECEBIDA em um arquivo JSON separado
            salvarMensagemJson(
                remetente="remoto",                        # sem identificação no payload
                destinatario=usuario_logado['username'],
                msg_plain=msg,
                msg_cripto=msg_cripto,
                topico=topico,
                broker=broker,
                direcao="recebida"
            )

        except Exception as e:
            console.print(f"[red]Erro ao descriptografar:[/red] {e}")

    cliente = mqtt.Client()
    cliente.on_message = on_message
    cliente.connect(broker, 1883, 60)
    cliente.subscribe(topico)
    console.print(f"Assinado em: [yellow]{topico}[/yellow]\n[dim]Ctrl+C para sair[/dim]")

    try:
        cliente.loop_forever()
    except KeyboardInterrupt:
        pass
    finally:
        try:
            cliente.loop_stop()
            cliente.disconnect()
        except:
            pass

# -------------------------
# Menus principais
# -------------------------
def MenuPrincipalADM(usuario_logado):
    while True:
        LimparTela()
        titulo("MENU ADMINISTRADOR")
        console.print("[1] Gerenciar usuários")
        console.print("[2] Enviar mensagens (Fernet + MQTT)")
        console.print("[3] Receber mensagens (Fernet + MQTT)")
        console.print("[4] Sair")
        try:
            result = int(input("➤ "))
        except ValueError:
            console.print(Fore.RED + "Digite um número válido"); time.sleep(1); continue

        if result == 1:
            gerenciamentoUser()
        elif result == 2:
            enviarMensagem(usuario_logado)
        elif result == 3:
            receberMensagem(usuario_logado)
        elif result == 4:
            break
        else:
            console.print(Fore.RED + "Digite algo válido")
            time.sleep(1)

def MenuPrincipalUser(usuario_logado):
    while True:
        LimparTela()
        titulo(f"MENU DO USUÁRIO ({usuario_logado['username'].upper()})")
        console.print("[1] Enviar mensagens (Fernet + MQTT)")
        console.print("[2] Receber mensagens (Fernet + MQTT)")
        console.print("[3] Sair")
        try:
            result = int(input("➤ "))
        except ValueError:
            console.print(Fore.RED + "Digite um número válido"); time.sleep(1); continue

        if result == 1:
            enviarMensagem(usuario_logado)
        elif result == 2:
            receberMensagem(usuario_logado)
        elif result == 3:
            break
        else:
            console.print(Fore.RED + "Digite algo válido")
            time.sleep(1)

def menuPrincipal():
    while True:
        LimparTela()
        titulo("MENU PRINCIPAL")
        console.print("[1] Logar")
        console.print("[2] Cadastrar novo usuário")
        console.print("[3] Sair")
        try:
            result = int(input("➤ "))
        except ValueError:
            console.print(Fore.RED + "Digite um número válido"); time.sleep(1); continue

        if result == 1:
            user = loginUser()
            if user:
                if user['tipo'] == 'admin':
                    MenuPrincipalADM(user)
                else:
                    MenuPrincipalUser(user)
        elif result == 2:
            adicionarUsers()
        elif result == 3:
            break
        else:
            console.print(Fore.RED + "Digite algo válido")
            time.sleep(1)

# ponto de entrada
if __name__ == "__main__":
    menuPrincipal()
