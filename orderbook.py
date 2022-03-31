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
            on_message=self.on_message,
            on_open=self.on_open,
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
    BUY = "buy"
    SELL = "sell"

@dataclass
class Order:
    price: float
    remaining: float
    side: Side
    reason: str

    def __repr__(self):
        return f"{self.price} {self.remaining}"



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

    def print_summary(self):
        print(self)
        self.print()

    def print(self):
        print(f"{self.bid_head}\t{self.ask_head}")

    def process_order(self, order: Order):
        if order.remaining == 0:
            # if remaining is 0, all orders at this price level have been filled or cancelled.
            # remove the price level from the order book
            # and reset current_bid / current_ask
            if order.side == "bid":
                if self.bids[order.price]:
                    self.bids.pop(order.price)
            else:
                if self.asks[order.price]:
                    self.asks.pop(order.price)
                    if self.ask_head == order.price:
                        self.ask_head = None

        else:
            if order.reason == "cancel":
                # delete the order from price level
                if order.side == "bid":
                    # list comprehesnsion removes the matched order from the list
                    self.bids[order.price] = [o for o in self.bids[order.price] if o.remaining != order.remaining ]
                    
                    if len(self.bids[order.price]) == 0 and self.bid_head.price == order.price and self.bid_head.remaining == order.remaining:
                        self.bid_head = None
                else:
                    self.asks[order.price] = [o for o in self.asks[order.price] if o.remaining != order.remaining ]

                    if len(self.asks[order.price]) == 0 and self.ask_head.price == order.price and self.ask_head.remaining == order.remaining:
                        self.ask_head = None
            elif order.reason == "initial" or order.reason == "place":
                # if price level doesnt exist, defaultdict will create it for us
                if order.side == "bid":
                    # set current bid
                    if self.bid_head == None:
                        self.bid_head = order
                    else:
                        # set the best bid (highest price)
                        if order.price > self.bid_head.price:
                            self.bid_head = order
                    # add order to bids
                    self.bids[order.price].append(order)
                else:
                    if self.ask_head == None:
                        self.ask_head = order
                    else:
                        # set the best ask (lowest price offer)
                        if order.price < self.ask_head.price:
                            self.ask_head = order
                    # add order to asks
                    self.asks[order.price].append(order)



def run(queue: Queue, book: OrderBook):
    print(f"====== RUN =======")
    while True:
        order = queue.get()

        if order:
            book.process_order(order)

        book.print_summary()
        queue.task_done()


if __name__ == "__main__":
    order_pool = Queue(maxsize=0) # FIFO Queue
    order_book = OrderBook()
    data_source = DataSource(queue=order_pool)

    thread_data_stream = threading.Thread(target=data_source.start, daemon=True)
    thread_output = threading.Thread(target=run, args=(order_pool, order_book))

    thread_data_stream.start()
    thread_output.start()
