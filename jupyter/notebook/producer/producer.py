import os
import websocket
import json
import io
import avro.schema
import avro.io

from kafka import KafkaProducer

# https://finnhub.io/docs/api/websocket-trades
class FinnhubProducer:
    def __init__(self):
        """
        Producer class that connects to the finnhub websocket, encodes & validates the JSON payload
        in avro format against pre-defined schema then sends data to kafka.
        """

        # define config from config file
        self.config = self.load_config('config.json')

        # define the kafka producer here. This assumes there is a kafka server already setup at the address and port
        self.producer = KafkaProducer(bootstrap_servers=f"{self.config['KAFKA_SERVER']}:{self.config['KAFKA_PORT']}",api_version=(0, 10, 1))
        
        # define the avro schema here. This assumes the schema is already defined in the src/schemas folder
        # this helps us enforce the schema when we send data to kafka
        self.avro_schema = avro.schema.parse(open('trades.avsc').read())
        print("AVRO schema loaded")

        # define the websocket client
        self.ws = websocket.WebSocketApp(f"wss://ws.finnhub.io?token={self.config['FINNHUB_API_KEY']}",
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)
        self.ws.on_open = self.on_open
        self.ws.run_forever()
    
    def load_config(self, config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
        
    def avro_encode(self, data, schema):
        """
        Avro encode data using the provided schema.

        Parameters
        ----------
        data : dict
            Data to encode.
        schema : avro.schema.Schema
            Avro schema to use for encoding.
        
        Returns
        -------
        bytes : Encoded data.
        """

        writer = avro.io.DatumWriter(schema)
        bytes_writer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        writer.write(data, encoder)
        return bytes_writer.getvalue()

    def on_message(self, ws, message):
        """
        Callback function that is called when a message is received from the websocket.

        Parameters
        ----------
        ws : websocket.WebSocketApp
            Websocket client.
        message : str
            Message received from the websocket.
        """
        message = json.loads(message)
        avro_message = self.avro_encode(
            {
                'data': message['data'],
                'type': message['type']
            }, 
            self.avro_schema
        )
        self.producer.send(self.config['KAFKA_TOPIC_NAME'], avro_message)

    def on_error(self, ws, error):
        """
        Websocket error callback. This currently just prints the error to the console.
        In a production environment, this should be logged to a file or sent to a monitoring service.

        Parameters
        ----------
        ws : websocket.WebSocketApp
            Websocket client.
        error : str
            Error message.
        """
        print(error)

    def on_close(self, ws):
        """
        Websocket close callback. This currently just prints a message to the console.
        In a production environment, this should be logged to a file or sent to a monitoring service.

        Parameters
        ----------
        ws : websocket.WebSocketApp
            Websocket client.
        """
        print("### closed ###")

    def on_open(self, ws):
        """
        Websocket open callback. This subscribes to the MSFT stock topic on the websocket.
        
        Parameters
        ----------
        ws : websocket.WebSocketApp
            Websocket client.
        """
        print("sending subscribe message")
        self.ws.send('{"type":"subscribe","symbol":"BINANCE:BTCUSDT"}')
        print("subscribed to AAPL")


if __name__ == "__main__":
    FinnhubProducer()
