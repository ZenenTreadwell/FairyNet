from digi.xbee.devices import XBeeDevice
from flask import Flask, render_template
from flask_socketio import SocketIO
import socket, time, serial, json

xbee = XBeeDevice('/dev/cu.usbserial-AG0JYQVE', 9600)
xbee.open()
xbee.set_sync_ops_timeout(10)

xnet = xbee.get_network()
xnet.start_discovery_process()
print('Discovering Network...', end='', flush=True)
while xnet.is_discovery_running():
    time.sleep(0.5)
    print('...', end='', flush=True)

print('\nDone!')
nodes = xnet.get_devices()
print(f'Found {len(nodes)} peer(s)!')

class Node:
    def __init__(self, raw_node):
        self.name = raw_node.get_node_id()
        self.address = raw_node.get_64bit_addr()

myNode = Node(xbee)

class Message:
    def __init__(self, message, node_name):
        self.sender = node_name
        self.text = message

    def toDiv(self):
        return f'<div><b>{self.sender}: </b>{self.text}</div>'


node_data = []
chat_history = []
for entry in nodes:
    node_data.append(Node(entry))

print('nodes')
for node in node_data:
    print(node.name)
    print(node.address)

print(dir(node_data[0].address))

app = Flask(__name__)
app.config['SECRET_KEY'] = "well-kept_secret"
socketio = SocketIO(app)

def msg_rcv(methods = ['GET', 'POST']):
    print('got a message')

def parseBytes(data):
    return ''.join(list(map(chr, map(int, data.split(',')))))

def rcv_callback(xbee_message):
    addr = xbee_message.remote_device.get_64bit_addr()
    node_id = xbee_message.remote_device.get_node_id()
    data = xbee_message.data.decode('utf-8')
    msg = Message(data, node_id)
    print(msg.toDiv())
    socketio.emit('resp', {'message': parseBytes(data), 'username': node_id,
                           'broadcast': xbee_message.is_broadcast}, callback=msg_rcv)

xbee.add_data_received_callback(rcv_callback)

@app.route('/', methods=['GET','POST'])
def chat():
    return render_template('chat.html', nodes=node_data, chat=chat_history)

@app.route('/send/<message>', methods=['GET','POST'])
def send_msg(message):
    xbee.send_data_broadcast(message.encode('utf-8'))
    socketio.emit('resp', {'message': parseBytes(message), 'username': myNode.name + ' (me)',
                           'broadcast': True}, callback=msg_rcv)
    return ('Sent!')


@app.route('/dm/<node_address>/<message>', methods=['GET','POST'])
def send_dm(node_address, message):
    for node in nodes:
        print(f'{str(node.get_64bit_addr())} vs. {str(node_address)}')
        if (str(node.get_64bit_addr()) == str(node_address)):
            xbee.send_data(node, message.encode('utf-8'))
            socketio.emit('resp', {'message': parseBytes(message), 'username': f'{myNode.name} to {node.get_node_id()}',
                                   'broadcast': True}, callback=msg_rcv)
            return ('Sent!')
    return ('Failed to Send')


@socketio.on('msg')
def handle_msg(json, methods = ['GET', 'POST']):
    print('received an event: ' + str(json))
    socketio.emit('resp', json, callback=msg_rcv)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=7000)
