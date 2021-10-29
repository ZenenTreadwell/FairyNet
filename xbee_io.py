#! venv/bin/python

from digi.xbee.devices import XBeeDevice
import serial
import time
import sys
import socket

# sock = socket.socket()
# sock.bind((socket.gethostname(), 1618))
sock.listen(3)



# ser = serial.Serial('/dev/ttyUSB0', 9600)
# ser.close()

xbee = XBeeDevice('/dev/ttyUSB0', 9600)
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

# Right now I'm only working with one peer, so I'm only listening for max 1 connection
sock_out = socket.socket()
sock_out.bind((socket.gethostname(), 1618))
sock_out.listen(1)

sock_in = socket.socket()
sock_in.connect((socket.gethostname(), 16180))

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
