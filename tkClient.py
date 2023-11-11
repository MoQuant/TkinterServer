import websocket
import matplotlib.pyplot as plt
import json

fig = plt.figure()
ax = fig.add_subplot(111)


conn = websocket.create_connection('ws://localhost:8080')

while True:
    resp = json.loads(conn.recv())
    ax.cla()
    ax.set_title(resp['id'])
    ax.bar(resp['bidPrice'], resp['bidVol'], 1, 1, color='red')
    ax.bar(resp['askPrice'], resp['askVol'], 1, 1, color='limegreen')
    plt.pause(0.5)


plt.show()
