# Gemini Orderbook

[Github Repository](https://github.com/Rcsuax/GeminiOrderbook)

A simple text-based terminal/command prompt application that connects to the WebSocket market data feed of Gemini, a digital asset exchange.
On each update it prints out the **best bid** and **ask price** and **quantity** of the BTCUSD asset pair. 

## Installation
 
```bash
# optionally use venv to manage python enviroments
python3 -m venv venv
source ./venv/bin/activate

# install dependencies 
pip3 install -r requirements.txt
# run program
python3 orderbook.py
```

additionally you can use the provided **Dockerfile** to build a runnable container image
```bash
# build image
docker build -t orderbook .
# run image
docker run -d --name orderbookcontainer orderbook
# see logs
docker logs orderbookcontainer
```


## Usage


```bash
python3 orderbook.py
```

| best bid | quantity    | best ask  | quantity   | 
| ---------| ----------- | --------- | ---------- |
| 6748.70  | 0.03700000  | 6748.71   | 4.27506690 | 
| 6739.70  | 0.20000000  | 6739.71   | 4.63391087 | 

Whenever any of these values changes, the application prints out a line with the latest values.
## Additonal Information

The protocol specification for the WebSocket market data feed is available at:

https://docs.gemini.com/websocket-api/#market-data

For the purposes of this assignment, you should either omit the top_of_book parameter or set it to false.
You are free to implement the application in a programming language of your choice. You are also free to use any appropriate libraries e.g. for handling JSON and WebSocket. However, you should not use any ready-made Gemini client libraries.
Hint: If you use an efficient data structure for the orderbook reconstruction then this is a plus.

## Implementation Notes

To represent both sides of the book I use two identical ```defaultdict(list)``` structures for **ASK** and **BID**
Since Python 3.7 dicts maintain insertion order

If I were to redo this; I would change my implementation. 

- Class Order: Double linked list data structure referencing Orders in same price level. Arranged by price time priority 
```python
class Order:
    def __init__(self, price, quantity, timestamp):
        self.price = price
        self.quantity = quantity
        self.timestamp = timestamp
        self.prev = None
        self.next = None
```


- Class PriceLevel: would represent all orders at a given price and this class would handle responsibilities    like fufilling a trade.
```python
class PriceLevel:
    def __init__(self, price, quantity):
        self.price = price
        self.quantity = quantity
        self.head = None
```

- Class Orderbook: representing both sides of the book (bid/ask), possible use a sortedcontainers. 
    SortedDict here or use perhaps use pythons std lib heapq which is a minheap (bid) and inverse heapq for a maxheap (asks)
    Would have helper methods suchas:
    add_order() remove_order() add_level() remove_level() print_summary()

```python
class Orderbook:
    def __init__(self):
        self.bids = sortedcontainers.SortedDict(PriceLevel)
        self.asks = sortedcontainers.SortedDict(PriceLevel)

    def add_order(self):
        pass

    def remove_order(self):
        pass
    
    def add_level(self, price, qty):
        pass

    def add_level(self, price, qty):
        pass

    def print_summary():
        pass
```
