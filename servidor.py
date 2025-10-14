import paho.mqtt.client as mqtt

#teste mandando mensagem para outro computador usando mqtt

broker = "test.mosquitto.org" # servidor MQTT público conectado nas duas maquinas
topico = "minharede/chat"   #tópico para enviar mensagens

cliente = mqtt.Client() #cria uma janela de comunicação
cliente.connect(broker, 1883, 60)

while True: #loop infinito para enviar mensagens
    msg = input("Você: ")
    cliente.publish(topico, msg)
    if msg.lower() == "sair":
        break

cliente.disconnect()

#na outra maquina, use o cliente_sub.py para receber as mensagens,
#primeiro execute o cliente_sub.py e depois o servidor.py

