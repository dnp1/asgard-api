#!/bin/bash


# Porque não fizemos isso aqui com docker-commpose?
# 1. Existem inúmeras variaveias compartilhadas, por exmeplo, o IP dos ZKs.
# Fazendo isso com compose teríamos que repetir esses valores para todos os compose-files que precisassem deles,
# 2. Existem variáveis compostas por valores de outras variáveis e não podemos fazer essa composição em um envfile; Por isso não usamos envfile.
# 3. Não é possivel passar um envfile pro docker-compose, apenas dentro do compose-file. Se pudéssemos passar até seria pssível
# criar um grande arquivo de env e passar para todas as chamadas do compose.

# VARIAVEIS COMUNS A TODOS OS PROCESSOS
NETWORK_NAME="asgard"
ZK_1_IP=172.18.0.2
ZK_2_IP=172.18.0.3
ZK_3_IP=172.18.0.4
ZK_CLUSTER_IPS=${ZK_1_IP}:2181,${ZK_2_IP}:2181,${ZK_3_IP}:2181

MESOS_MASTER_IP=172.18.0.11
MESOS_SLAVE_IP=172.18.0.21
MESOS_SLAVE_IPS_ACCOUNT_ASGARD_INFRA="172.18.0.51 172.18.0.52 172.18.0.53 172.18.0.54 172.18.0.55"
MESOS_SLAVE_IPS_ACCOUNT_ASGARD_DEV="172.18.0.61 172.18.0.62 172.18.0.63 172.18.0.64 172.18.0.65"
MARATHON_IP=172.18.0.31

POSTGRES_IP=172.18.0.41

echo "Removing any old containers..."
docker rm -f $(docker ps -aq -f name=asgard_)
echo "Recreating network=${NETWORK_NAME}"
docker network rm ${NETWORK_NAME}
docker network create --subnet 172.18.0.0/16 ${NETWORK_NAME}
sleep 2

#Postgres

echo -n "Postgres (${POSTGRES_IP}) "
docker run -d --rm -it --ip ${POSTGRES_IP} \
  --name asgard_pgsql \
  --net ${NETWORK_NAME} \
  -v ${PWD}/scripts/sql/:/docker-entrypoint-initdb.d/:ro \
  postgres:9.4

# ZK Cluster

ZOO_SERVERS="server.1=${ZK_1_IP}:2888:3888 server.2=${ZK_2_IP}:2888:3888 server.3=${ZK_3_IP}:2888:3888"
ZOO_PURGE_INTERVAL=10
echo -n "ZK (${ZK_1_IP}) "
docker run -d \
  --name asgard_zk_1 \
  --rm -it --ip ${ZK_1_IP} \
  -e ZOO_MY_ID=1 \
  --net ${NETWORK_NAME} \
  --env-file <(
echo ZOO_SERVERS=${ZOO_SERVERS}
echo ZOO_PURGE_INTERVAL=${ZOO_PURGE_INTERVAL}
) docker.sieve.com.br/infra/zookeeper:0.0.1

echo -n "ZK (${ZK_2_IP}) "
docker run -d --rm -it --ip ${ZK_2_IP} \
  --name asgard_zk_2 \
  -e ZOO_MY_ID=2 \
  --net ${NETWORK_NAME} \
  --env-file <(
echo ZOO_SERVERS=${ZOO_SERVERS}
echo ZOO_PURGE_INTERVAL=${ZOO_PURGE_INTERVAL}
) docker.sieve.com.br/infra/zookeeper:0.0.1

echo -n "ZK (${ZK_3_IP}) "
docker run -d --rm -it --ip ${ZK_3_IP} \
  --name asgard_zk_3 \
  -e ZOO_MY_ID=3 \
  --net ${NETWORK_NAME} \
  --env-file <(
echo ZOO_SERVERS=${ZOO_SERVERS}
echo ZOO_PURGE_INTERVAL=${ZOO_PURGE_INTERVAL}
) docker.sieve.com.br/infra/zookeeper:0.0.1


## MARATHON
MARATHON_HOSTNAME=${MARATHON_IP}
MESOS_IP=${MARATHON_IP}
LIBPROCESS_IP=${MARATHON_IP}
MARATHON_MASTER=zk://${ZK_CLUSTER_IPS}/mesos
MARATHON_ZK=zk://${ZK_CLUSTER_IPS}/mesos
MARATHON_TASK_LOST_EXPUNGE_GC=150000
MARATHON_TASK_LOST_EXPUNGE_INTERVAL=3600000
MARATHON_TASK_LOST_EXPUNGE_INITIAL_DELAY=300000
MARATHON_TASK_LAUNCH_TIMEOUT=300000
MARATHON_RECONCILIATION_INITIAL_DELAY=15000
MARATHON_RECONCILIATION_INTERVAL=600000
MARATHON_ZK_TIMEOUT=10000
MARATHON_ZK_SESSION_TIMEOUT=10000
MARATHON_ZK_MAX_VERSIONS=25
JAVA_OPTS=-Xms2g
MARATHON_HTTP_CREDENTIALS=marathon:pwd
MARATHON_ACCESS_CONTROL_ALLOW_ORIGIN=http://localhost:4200

echo -n "Marathon (${MARATHON_IP}) "
docker run -d -it --ip ${MARATHON_IP} \
  --name asgard_marathon \
  --net ${NETWORK_NAME} \
  --env-file <(
echo MARATHON_HOSTNAME=${MARATHON_HOSTNAME}
echo MESOS_IP=${MESOS_IP}
echo LIBPROCESS_IP=${LIBPROCESS_IP}
echo MARATHON_MASTER=${MARATHON_MASTER}
echo MARATHON_ZK=${MARATHON_ZK}
echo MARATHON_TASK_LOST_EXPUNGE_GC=${MARATHON_TASK_LOST_EXPUNGE_GC}
echo MARATHON_TASK_LOST_EXPUNGE_INTERVAL=${MARATHON_TASK_LOST_EXPUNGE_INTERVAL}
echo MARATHON_TASK_LOST_EXPUNGE_INITIAL_DELAY=${MARATHON_TASK_LOST_EXPUNGE_INITIAL_DELAY}
echo MARATHON_TASK_LAUNCH_TIMEOUT=${MARATHON_TASK_LAUNCH_TIMEOUT}
echo MARATHON_RECONCILIATION_INITIAL_DELAY=${MARATHON_RECONCILIATION_INITIAL_DELAY}
echo MARATHON_RECONCILIATION_INTERVAL=${MARATHON_RECONCILIATION_INTERVAL}
echo MARATHON_ZK_TIMEOUT=${MARATHON_ZK_TIMEOUT}
echo MARATHON_ZK_SESSION_TIMEOUT=${MARATHON_ZK_SESSION_TIMEOUT}
echo MARATHON_ZK_MAX_VERSIONS=${MARATHON_ZK_MAX_VERSIONS}
echo JAVA_OPTS=${JAVA_OPTS}
#echo #MARATHON_HTTP_CREDENTIALS=${MARATHON_HTTP_CREDENTIALS}
echo MARATHON_ACCESS_CONTROL_ALLOW_ORIGIN=${MARATHON_ACCESS_CONTROL_ALLOW_ORIGIN}
) \
  mesosphere/marathon:v1.3.13 --enable_features gpu_resources --mesos_role asgard

#--default_accepted_resource_roles asgard


## MESOS
MESOS_QUORUM=1
MESOS_IP=${MESOS_MASTER_IP}
MESOS_WORK_DIR=/var/lib/mesos
MESOS_HOSTNAME_LOOKUP=false
MESOS_ZK=zk://${ZK_CLUSTER_IPS}/mesos
#  volumes:
#    - /var/lib/mesos/:/var/lib/mesos/:rw

echo -n "Mesos Master (${MESOS_MASTER_IP}) "
docker run -d --rm -it --ip ${MESOS_MASTER_IP} \
  --name asgard_mesosmaster \
  --net ${NETWORK_NAME} \
  --env-file <(
echo MESOS_QUORUM=${MESOS_QUORUM}
echo MESOS_IP=${MESOS_IP}
echo MESOS_WORK_DIR=${MESOS_WORK_DIR}
echo MESOS_HOSTNAME_LOOKUP=${MESOS_HOSTNAME_LOOKUP}
echo MESOS_ZK=${MESOS_ZK}
) daltonmatos/mesos:0.0.3 /usr/sbin/mesos-master


## MESOS SLAVE
MESOS_ATTRIBUTES=";mesos:slave;workload:general"
MESOS_RESOURCES="cpus(*):4;mem(*):4096;ports(*):[31000-31999];cpus(asgard):1;mem(asgard):1024;ports(asgard):[30000-30999]"
MESOS_MASTER=zk://${ZK_CLUSTER_IPS}/mesos

for SLAVE_IP in `echo ${MESOS_SLAVE_IPS_ACCOUNT_ASGARD_INFRA}`;
do
    echo -n "Mesos Slave (namespace=asgard-infra (${SLAVE_IP}) "
    docker run -d --rm -it --ip ${SLAVE_IP} \
      --name asgard_mesosslave_${RANDOM} \
      --net ${NETWORK_NAME} \
      --env-file <(
    echo MESOS_IP=${SLAVE_IP}
    echo LIBPROCESS_ADVERTISE_IP=${SLAVE_IP}
    echo MESOS_ATTRIBUTES="${MESOS_ATTRIBUTES};owner:asgard-infra"
    echo MESOS_MASTER=${MESOS_MASTER}
    echo MESOS_RESOURCES=${MESOS_RESOURCES}
    ) \
      -v /sys/fs/cgroup:/sys/fs/cgroup \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -v $(dirname $(readlink --canonicalize ${0}))/scripts/docker.tar.bz2:/etc/docker.tar.bz2 \
      daltonmatos/mesos:0.0.3
done

for SLAVE_IP in `echo ${MESOS_SLAVE_IPS_ACCOUNT_ASGARD_DEV}`;
do
    echo -n "Mesos Slave (namespace=asgard-dev (${SLAVE_IP}) "
    docker run -d --rm -it --ip ${SLAVE_IP} \
      --name asgard_mesosslave_${RANDOM} \
      --net ${NETWORK_NAME} \
      --env-file <(
    echo MESOS_IP=${SLAVE_IP}
    echo LIBPROCESS_ADVERTISE_IP=${SLAVE_IP}
    echo MESOS_ATTRIBUTES="${MESOS_ATTRIBUTES};owner:asgard-dev"
    echo MESOS_MASTER=${MESOS_MASTER}
    echo MESOS_RESOURCES=${MESOS_RESOURCES}
    ) \
      -v /sys/fs/cgroup:/sys/fs/cgroup \
      -v /var/run/docker.sock:/var/run/docker.sock \
      -v $(dirname $(readlink --canonicalize ${0}))/scripts/docker.tar.bz2:/etc/docker.tar.bz2 \
      daltonmatos/mesos:0.0.3
done

#CREATE INITIAL GROUP
echo "Creating initial groups. Waiting for Marathon to come up..."
while true; do
  curl -s -X PUT -d '{"id": "/", "groups": [{"id": "/asgard-dev"}, {"id": "/asgard-infra"}]}' http://${MARATHON_IP}:8080/v2/groups
  if [ $? -eq 0 ]; then
    break;
  fi
done

