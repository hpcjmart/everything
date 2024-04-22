build:
	docker build --no-cache -t hpcjmart/spark-base ./base
	docker build --no-cache -t hpcjmart/spark-master ./master
	docker build --no-cache -t hpcjmart/spark-worker ./worker
	docker build --no-cache -t hpcjmart/spark-history ./history
	docker build --no-cache -t hpcjmart/spark-jupyter ./jupyter
	docker build --no-cache -t hpcjmart/grafana ./grafana
