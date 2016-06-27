#neuron_server
import ConfigParser
import base64
import sys, socket, select
from Crypto.Cipher import AES
import hashlib
import os
import signal

os.system("clear")
print """
	  ___  ___ __ _________  ___ 
	 / _ \/ -_) // / __/ _ \/ _ \ 
	/_//_/\__/\_,_/_/  \___/_//_/
	server v 1.2 | susmithHCK                  

"""

def sigint_handler(signum, frame):
    print '\n user interrupt ! shutting down'
    print "[info] shutting down NEURON \n\n"
    sys.exit()	
    
signal.signal(signal.SIGINT, sigint_handler)

def hasher(key):
	hash_object = hashlib.sha512(key)
	hexd = hash_object.hexdigest()
	hash_object = hashlib.md5(hexd)
	hex_dig = hash_object.hexdigest()
	return hex_dig	
	

def encrypt(secret,data):
	BLOCK_SIZE = 32
	PADDING = '{'
	pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
	EncodeAES = lambda c, s: base64.b64encode(c.encrypt(pad(s)))
	cipher = AES.new(secret)
	encoded = EncodeAES(cipher, data)
	return encoded

def decrypt(secret,data):
	BLOCK_SIZE = 32
	PADDING = '{'
	pad = lambda s: s + (BLOCK_SIZE - len(s) % BLOCK_SIZE) * PADDING
	DecodeAES = lambda c, e: c.decrypt(base64.b64decode(e)).rstrip(PADDING)
	cipher = AES.new(secret)
	decoded = DecodeAES(cipher, data)
	return decoded

config = ConfigParser.RawConfigParser()   
config.read(r'neuron.conf')

HOST = config.get('config', 'HOST')
PORT = int(config.get('config', 'PORT'))
PASSWORD = config.get('config', 'PASSWORD')
VIEW = str(config.get('config', 'VIEW'))
key = hasher(PASSWORD)
SOCKET_LIST = []
RECV_BUFFER = 4096


def chat_server():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(10)

    SOCKET_LIST.append(server_socket)

    print "neuron server started on port " + str(PORT)

    while 1:

        ready_to_read,ready_to_write,in_error = select.select(SOCKET_LIST,[],[],0)

        for sock in ready_to_read:

            if sock == server_socket:
                sockfd, addr = server_socket.accept()
                SOCKET_LIST.append(sockfd)
                print "user (%s, %s) connected" % addr

                broadcast(server_socket, sockfd, encrypt(key,"[%s:%s] entered our chatting room\n" % addr))

            else:
                try:
                    data = sock.recv(RECV_BUFFER)
                    data = decrypt(key,data)
                    if data:

                        broadcast(server_socket, sock,encrypt(key,"\r" + data))
                        if VIEW == '1':
                          print data
                    else:

                        if sock in SOCKET_LIST:
                            SOCKET_LIST.remove(sock)

                        broadcast(server_socket, sock,encrypt(key,"user (%s, %s) is offline\n" % addr))

                except:
                    broadcast(server_socket, sock, "user (%s, %s) is offline\n" % addr)
                    continue

    server_socket.close()

def broadcast (server_socket, sock, message):
    for socket in SOCKET_LIST:

        if socket != server_socket and socket != sock :
            try :
                socket.send(message)
            except :

                socket.close()

                if socket in SOCKET_LIST:
                    SOCKET_LIST.remove(socket)

if __name__ == "__main__":

    sys.exit(chat_server())
