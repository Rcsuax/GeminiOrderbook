#!/usr/bin/env python3
import ssl
import enum
import json
import websocket
import threading
from decimal import Decimal
from queue import Queue
from dataclasses import dataclass
from collections import defaultdict

class DataSource:
    def __init__(self, queue: Queue):
        """
        Data Source for MARKET DATA Gemini Websockets API, primary job is to populate a queue of orders
        """
        self.queue = queue
        self.ws = websocket.WebSocketApp(
            "wss://api.gemini.com/v1/marketdata/btcusd",
            on_open=self.on_open,
            on_message=self.on_message,
        )

    def start(self):
        """ 
        Start the websocket connection 
        """
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def on_open(self, _):
        print("====== CONNECTED TO GEMINI ======")

    def on_message(self, _, message):
        """
        The initial response message will show the existing state of the order book. 
        Subsequent messages will show all executed trades, orders placed or canceled.
        """
        msg = json.loads(message)
        events = msg["events"]

        for event in events:
            if event:
                px = Decimal(event["price"])
                qty = Decimal(event["remaining"])
                side = event["side"]
                reason = event["reason"]
                self.queue.put(Order(px, qty, side, reason))



class Side(enum.Enum):
    BUY = "bid"
    SELL = "ask"



@dataclass
class Order:
    price: Decimal
    remaining: Decimal
    side: Side
    reason: str

    def __repr__(self):
        return f"{self.price} x {self.remaining}"



class OrderBook:
    def __init__(self):
        """
        initialize the order book with a defaultdict of lists
        where the index is the price and the value is a list of orders
        self.bids = { (price): [order1, order2, ...] }
        self.asks = { (price): [order1, order2, ...] }
        """
        self.bids = defaultdict(list)
        self.asks = defaultdict(list)
        self.bid_head = None
        self.ask_head = None

    def __str__(self) -> str:
        return f"============ BOOK STATE ============\nBids: {len(self.bids)}\nAsks: {len(self.asks)}"
    
    def __len__(self) -> int:
        return len(self.bids) + len(self.asks)

    def get_max_bid(self):
        if(self.bids):
            return self.bids[max(self.bids)][0]
        else:
            return 0

    def get_min_ask(self):
        if(self.asks):
            return self.asks[min(self.asks)][0]
        else:
            return 0
    
    def get_string(self):
            return f"{self.get_max_bid()}\t - \t{self.get_min_ask()}"

    def print_summary(self):
        print(self)
        self.print()

    def print(self):
        # should cache this then eval the heap at the end. average case should be O(1)
        print(f"{self.get_max_bid()}\t - \t{self.get_min_ask()}")

    def process_order(self, order: Order):
        if order.remaining == 0:
            # if remaining is 0, all orders at this price level have been filled or cancelled.
            # remove the price level from the order book
            if order.side == "bid":
                if self.bids[order.price]:
                    del self.bids[order.price]
            else:
                if self.asks[order.price]:
                    del self.asks[order.price]
        else:
            if order.reason == "cancel":
                # delete the order from price level
                if order.side == "bid":
                    # list comprehesnsion removes the matched order from the list
                    self.bids[order.price] = [o for o in self.bids[order.price] if o.remaining != order.remaining ]
                else:
                    self.asks[order.price] = [o for o in self.asks[order.price] if o.remaining != order.remaining ]
            elif order.reason == "initial" or order.reason == "place":
                # if price level doesnt exist, defaultdict will create it for us
                if order.side == "bid":
                    # add order to bids
                    self.bids[order.price].append(order)
                else:
                    # add order to asks
                    self.asks[order.price].append(order)
            else:
                print(f"TRADE: {order}")
    
    def run(self, queue: Queue):
        print(f"====== RUN =======")
        
        while True:
            order = queue.get()
            if order:
                self.process_order(order)

            self.print()
            queue.task_done()



if __name__ == "__main__":
    order_pool = Queue(maxsize=0) # FIFO Queue
    order_book = OrderBook()
    data_source = DataSource(queue=order_pool)

    thread_data_stream = threading.Thread(target=data_source.start, daemon=True)
    thread_output = threading.Thread(target=order_book.run, args=(order_pool,))

    thread_data_stream.start()
    thread_output.start()
