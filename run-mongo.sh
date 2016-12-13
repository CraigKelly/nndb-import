#!/bin/bash

DBDIR=/data/mongo-data
DOCKER_NAME=main-mongo

export DBDIR
export DOCKER_NAME

echo "Insuring data directory $DBDIR"
mkdir -p $DBDIR

echo "Starting $DOCKER_NAME"
sudo docker run -p 127.0.0.1:27017:27017 --name $DOCKER_NAME -v $DBDIR:/data/db mongo:3.2
