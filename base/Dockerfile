FROM ubuntu:latest

RUN sed -i -e "s|http://archive.ubuntu.com|http://jp.archive.ubuntu.com|g" /etc/apt/sources.list \
 && apt-get -qq update  \
 && DEBIAN_FRONTEND=noninteractive apt-get -qq install --no-install-recommends \
      sudo \
      openjdk-8-jdk \
      curl \
      gnupg \
      procps \
      python3.11 \
      python3-pip \
      coreutils \
      libc6-dev \
 && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 2 \
 && update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

ARG USERNAME=jupyter
ARG GROUPNAME=jupyter
ARG UID=1001
ARG GID=1001

RUN echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
 && chmod 0440 /etc/sudoers.d/$USERNAME \
 && groupadd -g $GID $GROUPNAME \
 && useradd -m -s /bin/bash -u $UID -g $GID $USERNAME

USER $USERNAME

ENV JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64/

# Hadoop
ARG HADOOP_VERSION=3.3.6
ARG HADOOP_URL=https://archive.apache.org/dist/hadoop/common/hadoop-$HADOOP_VERSION/hadoop-$HADOOP_VERSION.tar.gz
ENV HADOOP_HOME=/opt/hadoop

RUN set -x \
 && curl -fsSL https://archive.apache.org/dist/hadoop/common/KEYS -o /tmp/hadoop-KEYS \
 && gpg --import /tmp/hadoop-KEYS \
 && sudo mkdir $HADOOP_HOME  \
 && sudo chown $USERNAME:$GROUPNAME -R $HADOOP_HOME \
 && curl -fsSL $HADOOP_URL -o /tmp/hadoop.tar.gz \
 && curl -fsSL $HADOOP_URL.asc -o /tmp/hadoop.tar.gz.asc \
 && gpg --verify /tmp/hadoop.tar.gz.asc \
 && tar -xf /tmp/hadoop.tar.gz -C $HADOOP_HOME --strip-components 1 \
 && mkdir $HADOOP_HOME/logs \
 && rm /tmp/hadoop*

ENV HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
ENV PATH=$HADOOP_HOME/sbin:$HADOOP_HOME/bin:$PATH
ENV LD_LIBRARY_PATH=$HADOOP_HOME/lib/native:$LD_LIBRARY_PATH

# Spark
ARG SPARK_VERSION=3.2.1
ARG SPARK_URL=https://archive.apache.org/dist/spark/spark-$SPARK_VERSION/spark-$SPARK_VERSION-bin-hadoop3.2.tgz
ENV SPARK_HOME=/opt/spark

RUN set -x \
 && curl -fsSL https://archive.apache.org/dist/spark/KEYS -o /tmp/spark-KEYS  \
 && gpg --import /tmp/spark-KEYS \
 && sudo mkdir $SPARK_HOME \
 && sudo chown $USERNAME:$GROUPNAME -R $SPARK_HOME \
 && curl -fsSL $SPARK_URL -o /tmp/spark.tgz \
 && curl -fsSL $SPARK_URL.asc -o /tmp/spark.tgz.asc \
 && tar -xf /tmp/spark.tgz -C $SPARK_HOME --strip-components 1 \
 && rm /tmp/spark* \
 && curl -fsSL https://jdbc.postgresql.org/download/postgresql-42.3.2.jar -o $SPARK_HOME/jars/postgresql-42.3.2.jar

ENV PYTHONHASHSEED=1
ENV PYSPARK_PYTHON=python3
ENV SPARK_CONF_DIR=$SPARK_HOME/conf
ENV PATH=$SPARK_HOME/sbin:$SPARK_HOME/bin:$PATH

# Config
COPY --chown=$USERNAME:$GROUPNAME conf/core-site.xml $HADOOP_CONF_DIR/
COPY --chown=$USERNAME:$GROUPNAME conf/hdfs-site.xml $HADOOP_CONF_DIR/
COPY --chown=$USERNAME:$GROUPNAME conf/yarn-site.xml $HADOOP_CONF_DIR/
COPY --chown=$USERNAME:$GROUPNAME conf/mapred-site.xml $HADOOP_CONF_DIR/
COPY --chown=$USERNAME:$GROUPNAME conf/workers $HADOOP_CONF_DIR/
COPY --chown=$USERNAME:$GROUPNAME conf/spark-defaults.conf $SPARK_CONF_DIR/
COPY --chown=$USERNAME:$GROUPNAME conf/log4j.properties $SPARK_CONF_DIR/

RUN ln $HADOOP_CONF_DIR/workers $SPARK_CONF_DIR/ 

# Entry point
COPY entrypoint.sh /usr/local/sbin/entrypoint.sh
RUN sudo chmod a+x /usr/local/sbin/entrypoint.sh
ENTRYPOINT ["entrypoint.sh"]