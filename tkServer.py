wsurl = 'wss://ws-feed.exchange.coinbase.com'
#{'type':'subscribe','product_ids':self.tickers,'channels':['level2_batch']}

import tkinter as tk
import tkinter.ttk as ttk
import threading
import websocket
import asyncio
import websockets
import json
import numpy as np

class CoinbaseOrderbook:

    bid = {}
    ask = {}

    def OrganizeBook(self):
        result = {}
        for tick in self.bid:
            if tick in self.bid.keys() and tick in self.ask.keys():
                X = list(sorted(self.bid[tick].items(), reverse=True))[:self.current_depth]
                Y = list(sorted(self.ask[tick].items()))[:self.current_depth]
                bp, bv = np.array(X).T.tolist()
                ap, av = np.array(Y).T.tolist()
                bid_sum = [sum(bv[:i+1]) for i in range(self.current_depth)]
                ask_sum = [sum(av[:i+1]) for i in range(self.current_depth)]

                result[tick] = {'bidPrice':bp[::-1], 'bidVol':bid_sum[::-1],
                                'askPrice':ap, 'askVol':ask_sum, 'id': tick}
                

        return result

    def ParseBook(self, resp):
        if 'type' in resp.keys():
            if resp['type'] == 'snapshot':
                ticker = resp['product_id']
                self.bid[ticker] = {float(price):float(volume) for price, volume in resp['bids']}
                self.ask[ticker] = {float(price):float(volume) for price, volume in resp['asks']}
            if resp['type'] == 'l2update':
                ticker = resp['product_id']
                for (side, price, volume) in resp['changes']:
                    price, volume = float(price), float(volume)
                    if side == 'buy':
                        if volume == 0:
                            if price in self.bid[ticker].keys():
                                del self.bid[ticker][price]
                        else:
                            self.bid[ticker][price] = volume
                    else:
                        if volume == 0:
                            if price in self.ask[ticker].keys():
                                del self.ask[ticker][price]
                        else:
                            self.ask[ticker][price] = volume

    def InitFeed(self):
        def Socket():
            conn = websocket.create_connection(wsurl)
            msg = {'type':'subscribe','product_ids':self.tickers,'channels':['level2_batch']}
            conn.send(json.dumps(msg))
            while True:
                resp = json.loads(conn.recv())
                self.ParseBook(resp)
        return threading.Thread(target=Socket)

class WebSocketServer(CoinbaseOrderbook):

    async def ChartServer(self, ws, path):
        while True:
            try:
                books = self.OrganizeBook()
                await ws.send(json.dumps(books[self.current_ticker]))
            except:
                pass
            await asyncio.sleep(0.7)

    def InitServer(self):
        def Serve():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(websockets.serve(self.ChartServer, self.host, self.port))
            loop.run_forever()
        return threading.Thread(target=Serve)

class Home(tk.Tk, WebSocketServer):

    current_ticker = 'BTC-USD'
    current_depth = 10

    def __init__(self, tickers=['BTC-USD','ETH-USD','LTC-USD'], host='localhost', port=8080):
        tk.Tk.__init__(self)
        tk.Tk.wm_title(self, 'Control GUI')
        self.geometry('350x175')

        self.tickers = tickers
        self.host = host
        self.port = port

        ctrl_frame = tk.Frame(self)
        ctrl_frame.pack(side=tk.TOP)
        self.controlFrame(ctrl_frame)

    def controlFrame(self, frame):
        def change():
            self.current_ticker = self.ticker_entry.get()
            self.current_depth = int(self.depth_entry.get())  
        tk.Label(frame, text='\t').grid(row=1, column=1)
        self.ticker_entry = ttk.Entry(frame, justify='center')
        self.depth_entry = ttk.Entry(frame, justify='center')
        self.ticker_entry.insert('', self.current_ticker)
        self.depth_entry.insert('', self.current_depth)
        tk.Label(frame, text='Ticker').grid(row=2, column=1)
        self.ticker_entry.grid(row=3, column=1)
        tk.Label(frame, text='Depth').grid(row=4, column=1)
        self.depth_entry.grid(row=5, column=1)
        tk.Button(frame, text='Update', command=lambda: change()).grid(row=6, column=1)
        


home = Home()
home.InitFeed().start()
home.InitServer().start()
home.mainloop()

    
