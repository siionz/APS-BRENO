from colorama import init, Fore, Style
import pyfiglet
import os
import time
import hashlib
import json
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

init()
console = Console()

arquivoUser = "usuarios.json"   # Faz o arquivoUser receber o json usuarios
salt_digitado = input("Insira um salt para você utilizar: ")

def LimparTela(): # Função para limpar a tela do prompt
    os.system('cls')

def titulo(texto): # Função para estilizar o titulo
    banner = pyfiglet.figlet_format(texto, font="slant")
    print(Fore.BLUE + banner + Style.RESET_ALL)

def criptografarSenha(senha): # Criptografa a senha com SHA-256
    salt = salt_digitado  # Salt recebe o que o usuário escrever.
    senhaComSalt = senha + salt
    hashSenha = hashlib.sha256(senhaComSalt.encode()).hexdigest()
    return hashSenha

def verificarSenha(senhaDigitada, hashArmazenado):
    """Verifica se a senha digitada confere com o hash armazenado"""
    hashDigitada = criptografarSenha(senhaDigitada)
    return hashDigitada == hashArmazenado

def carregarJson(arquivo):  # Carrega o json (usuários) para leitura
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
            return {}

def salvar_dados(arquivo, dados): # Insere os dados no json (usuarios)

    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f)

def loginUser():     # Função para fazer o login 

    LimparTela()
    titulo("Login de Usuarios")
    usuarios = carregarJson(arquivoUser) 

    username_digitado = input("Digite seu username: ").strip()
    senha = input("Digite sua senha: ").strip()

    for userId, username in usuarios.items():
        if username['username'] == username_digitado:
            # Verifica a senha
            if verificarSenha(senha, username.get('passwordHash', '')):
                console.print("\n[bold green]Login realizado com sucesso![/bold green]")
                time.sleep(1)

                username['id'] = userId

                # normaliza o tipo para comparar de forma segura
                tipo = username.get('tipo', 'usuario').lower()


                # Direciona para o menu correspondente
                if tipo == 'admin':
                    MenuPrincipalADM()
                else:
                    MenuPrincipalUser()

                return username 
            else:
                console.print("\n[bold red]Senha incorreta. Tente novamente[/bold red]")
                time.sleep(2)
                return 

    console.print("[bold red]Usuário não encontrado[/bold red]")
    time.sleep(2)
    return None    

def adicionarUsers():
    return
def modificarUser():
    return
def excluirUsers():
    return

def gerenciamentoUser():
    while True:
        titulo("GERENCIAMENTO DE USUÁRIOS")
        print("  [1] - Adicionar Usuários")
        print("  [2] - Modificar Usuários")
        print("  [3] - Excluir Usuários")
        print("  [4] - Sair")

        result = int (input("Escolha uma opção: "))

        if result == 1:
            listager = adicionarUsers()
        elif result == 2:
            listaenviar = modificarUser()
        elif result == 3:
            listaenviar = excluirUsers()
        elif result == 4:
            break
        else:
            print(Fore.RED + "Digite algo válido")
    LimparTela()

def salvarMensagemJson(msg_original, msg_criptografada):
    return
    
def enviarMensagem():
    loginUser()
    return

def MenuPrincipalADM():
    while True:
        titulo("MENU PRINCIPAL")
        print("  [1] - Gerenciamento de Usuários")
        print("  [2] - Envio de Mensagens")
        print("  [3] - Sair")

        result = int (input("Escolha uma opção: "))

        if result == 1:
            listaLogin = gerenciamentoUser()
        elif result == 2:
            listaCadastro = enviarMensagem()
        elif result == 3:
            break
        else:
            print(Fore.RED + "Digite algo válido")
    LimparTela()


def MenuPrincipalUser():
    while True:
        titulo("MENU PRINCIPAL")
        print("  [1] - Envio de Mensagens")
        print("  [2] - Sair")

        result = int (input("Escolha uma opção: "))

        if result == 1:
            listaLogin = gerenciamentoUser()
        elif result == 2:
            break
        else:
            print(Fore.RED + "Digite algo válido")
    LimparTela()

print (MenuPrincipalADM())