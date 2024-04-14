docker exec kafka \
kafka-topics --bootstrap-server kafka:9092 \
             --create \
             --topic market
