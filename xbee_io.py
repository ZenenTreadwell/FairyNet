#! venv/bin/python

from digi.xbee.devices import XBeeDevice
import serial
import time
import sys
import json
import socket
from flask import Flask, request

import socketserver
import multiprocessing as mp


# Each Mesh node needs one server socket for receiving requests
sock = socket.socket()
sock.bind((socket.gethostbyname('localhost'), 1618))
sock.listen()

# ser = serial.Serial('/dev/ttyUSB0', 9600)
# ser.close()

# xbee = XBeeDevice('/dev/ttyUSB0', 9600)
xbee = XBeeDevice('/dev/cu.usbserial-AG0JYQVE', 9600)

xbee.set_sync_ops_timeout(10)
# print('XBee Attributes')
# print(dir(xbee))

xbee.open()
xnet = xbee.get_network()
xnet.start_discovery_process(deep=True, n_deep_scans=1)
print('Discovering Network...', end='', flush=True)
while xnet.is_discovery_running():
    time.sleep(0.5)
    print('...', end='', flush=True)

print('\nDone!')
nodes = xnet.get_devices()
print(f'Found {len(nodes)} peer(s)!')

# For every other mesh node in the network, we need to open up a client connection to them so that
# we can address them as individuals... I think? Is my brain working right?
# sock_in = socket.socket()

# No! We need to start a server locally to receive data broadcasts and forward them to IPFS
# We also need to start another local server for each other node so that it can send those requests
# to those servers via Digimesh
#server = Flask('app')
#@server.route('/')
#def index():
#    print('got this request')
#    print(request)
#    print('as data')
#    data = request.get_data()
#    print(data)
#    print('sending it over xbee')
#    for node in nodes:
#       xbee.send_data_async(node, request.get_data())
#    return '<h1>Hello!</h1>'
#
#def start_server():
#    server.run(host = 'localhost', port = 8080)

#Flask was too complicated lol
class StreamRequestCompressor(socketserver.StreamRequestHandler):
    def handle(self):
        for node in nodes:
            xbee.send_data_async(node, 'REQ_START'.encode('utf-8'))

        data = self.rfile.readline().strip()
        while data:
            print('got this here data!')
            print(data)
            for node in nodes:
                xbee.send_data_async(node, data)

            self.wfile.write(data.upper())
            data = self.rfile.readline().strip()

        for node in nodes:
            xbee.send_data_async(node, 'REQ_END'.encode('utf-8'))

#class RequestCompressor(socketserver.BaseRequestHandler):
#    def handle(self):
#        self.data = self.request.recv(1024).strip()
#        print('got this here data!')
#        print(data)
#        xbee.send_data_async(nodes[0], self.data)
#        xbee.send_data_async(nodes[1], self.data)
#        self.request.sendall(self.data.upper())

def start_tcp_server():
    with socketserver.TCPServer(('localhost', 8080), StreamRequestCompressor) as server:
        server.serve_forever()

server_process = mp.Process(target=start_tcp_server)
server_process.start()

# No longer needed as we're not connecting to the other server by socket
# # Try 10 times, waiting 2 seconds between attempts
# for i in range(10):
#     time.sleep(2)
#     try:
#         sock_in.connect((socket.gethostname(), 16180))
#         print("Got a message from the server")
#     except ConnectionRefusedError:
#         print(f'Connection #{i+1} failed, trying again.')
#         continue

# for i in range(len(nodes)):
#     # Server socket
#     nodes[i].sock_out = socket.socket()
#     nodes[i].sock_out.bind((socket.gethostname(), 1618+i))

#     # Client socket
#     nodes[i].sock_in = socket.socket()
#     nodes[i].sock_in.bind((socket.gethostname(), 16180+i))



def rcv_callback(xbee_message):
    addr = xbee_message.remote_device.get_64bit_addr()
    node_id = xbee_message.remote_device.get_node_id()
    data = xbee_message.data.decode('utf-8')
    print(f'Recieved data: {data} from node {node_id} at address {addr}')

xbee.add_data_received_callback(rcv_callback)

while True:
    try:
        msg = input('Send broadcast message here: \n')
        xbee.send_data_broadcast(msg.encode('utf-8'))
    except KeyboardInterrupt:
        break

xbee.close()
