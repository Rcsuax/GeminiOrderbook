#!/usr/bin/env python3
import ssl
import json
import websocket
import threading
from queue import Queue
from dataclasses import dataclass
from collections import defaultdict


class OrderSource:
    def __init__(self, queue):
        """
        Interface with the Gemini Websockets API to
        receive live order book data then submits it to a queue
        to be processed by the main thread.
        """
        self.queue = queue
        self.ws = websocket.WebSocketApp(
            "wss://api.gemini.com/v1/marketdata/btcusd",
            on_message=self.on_message,
            on_open=self.on_open,
        )

    def start(self):
        self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

    def on_open(self, _):
        print("====== CONNECTED TO GEMINI ======")

    def on_message(self, _, message):
        msg = json.loads(message)
        events = msg["events"]

        for event in events:
            if event:
                px = float(event["price"])
                qty = float(event["remaining"])
                side = event["side"]
                reason = event["reason"]
                self.queue.put(Order(px, qty, side, reason))


@dataclass
class Order:
    price: float
    remaining: float
    side: str
    reason: str

    def __repr__(self):
        return f"{self.price} x {self.remaining}"


class OrderBook:
    def __init__(self):
        """
        initialize the order book with a defaultdict of deques
        where the index is the price and the value is a list of orders
        expect O(1) lookup time and O(1) insertion time
        expect O(n) lookup time for worst case

        self.bids = { (price): [order1, order2, ...] }
        self.asks = { (price): [order1, order2, ...] }
        """
        self.bids = defaultdict(list)
        self.asks = defaultdict(list)
        self.bid_head = None
        self.ask_head = None

    def __str__(self):
        return f"============ BOOK STATE ============\nBids: {len(self.bids)}\nAsks: {len(self.asks)}"

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
                # delete order from price level
                if order.side == "bid":
                    # list comprehesnsion removes the matched order from the list
                    self.bids[order.price] = [o for o in self.bids[order.price] if o.remaining != order.remaining ]
                    
                    if self.bid_head.price == order.price and self.bid_head.remaining == order.remaining:
                        self.bid_head = None
                else:
                    self.asks[order.price] = [o for o in self.asks[order.price] if o.remaining != order.remaining ]

                    if self.ask_head.price == order.price and self.ask_head.remaining == order.remaining:
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

    def print_summary(self):
        print(self)
        print(f"{self.bid_head}\t{self.ask_head}")


def run(queue: Queue, book: OrderBook):
    print(f"====== RUN =======")
    while True:
        order = queue.get()

        if order:
            book.process_order(order)

        book.print_summary()
        queue.task_done()


if __name__ == "__main__":
    order_pool = Queue(maxsize=0) # FIFO Queue or PRIORITY Queue
    order_book = OrderBook()
    order_source = OrderSource(queue=order_pool)

    thread_data_stream = threading.Thread(target=order_source.start, daemon=True)
    thread_output = threading.Thread(target=run, args=(order_pool, order_book))

    thread_data_stream.start()
    thread_output.start()
