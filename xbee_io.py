#! venv/bin/python

from digi.xbee.devices import XBeeDevice
import serial
import time

# ser = serial.Serial('/dev/ttyUSB0', 9600)
# ser.close()

xbee = XBeeDevice('/dev/ttyUSB0', 9600)
# print('XBee Attributes')
# print(dir(xbee))

xbee.open()

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
