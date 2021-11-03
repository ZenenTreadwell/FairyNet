from digi.xbee.devices import XBeeDevice
from flask import Flask, render_template
from flask_socketio import SocketIO
import socket, time, serial

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

node_data = []
for entry in nodes:
    node_data.append(Node(entry))

print('nodes')
for node in node_data:
    print(node.name)
    print(node.address)

app = Flask(__name__)
app.config['SECRET_KEY'] = "well-kept_secret"
socketio = SocketIO(app)

@app.route('/')
def chat():
    return render_template('chat.html', nodes=node_data)

@app.route('/send/<message>')
def send_msg(message):
    xbee.send_data_broadcast(message)


@app.route('/dm/<id>/<message>')
def send_dm(node_addr, message):
    node = next((node for node in node_data if node.address == node_addr), None)
    xbee.send_data(node, message)


def msg_rcv(methods = ['GET', 'POST']):
    print('got a message')

@socketio.on('msg')
def handle_msg(json, methods = ['GET', 'POST']):
    print('received an event: ' + str(json))
    socketio.emit('resp', json, callback=msg_rcv)

if __name__ == '__main__':
    socketio.run(app, debug=True, port=7000)
