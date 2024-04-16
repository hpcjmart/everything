build:
	docker build -t hadoop-spark-base ./base
	docker build -t hadoop-spark-master ./master
	docker build -t hadoop-spark-worker ./worker
	docker build -t hadoop-spark-history ./history
	docker build -t hadoop-spark-jupyter ./jupyter
	docker build -t grafana ./grafana
