### Gemini Orderbook

#### Setup Install
``` python3 -m venv venv```
``` source ./venv/bin/activate```
``` pip3 install -r requirements.txt ```
``` python3 gemini.py ```

#### Task
The objective of the programming assignment is to write a simple text-based terminal/command prompt application that connects to the WebSocket market data feed of Gemini, a digital asset exchange, and, until terminated, on each update prints out the best bid and ask price and quantity of the BTCUSD asset pair. For example:
6748.70 0.03700000 - 6748.71 4.27506690 6739.70 0.20000000 - 6739.71 4.63391087
Above, the first column contains the best bid price, the second column the total quantity available on the best bid price level, and the third and fourth columns the same for the ask side. Whenever any of these values changes, the application prints out a line with the latest values.
The protocol specification for the WebSocket market data feed is available at:
https://docs.gemini.com/websocket-api/#market-data
For the purposes of this assignment, you should either omit the top_of_book parameter or set it to false.
You are free to implement the application in a programming language of your choice. You are also free to use any appropriate libraries e.g. for handling JSON and WebSocket. However, you should not use any ready-made Gemini client libraries.
Hint: If you use an efficient data structure for the orderbook reconstruction then this is a plus.

#### Organisation: 
- using the OrderSource class we create a websocket connection and populate a queue of Orders
- this queue of orders is consumed in a seperate thread by the Orderbook

#### Datastructures

To represent both sides of the book I use two identical ```defaultdict(list)``` structures for **ASK** and **BID**
An improvement that could be made would be to replace the structures with
```from sortedcontainers import SortedDict```
using ```SortedDict()``` instead of ```defaultdict(list)```


