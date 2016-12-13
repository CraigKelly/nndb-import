#!/bin/bash

NBDIR=$(pwd)

if [ x"$DOCKER_NAME" == x ]; then
    DOCKER_NAME=jupy-ds-nb-01
fi
if [ x"$DOCKER_IMG" == x ]; then
    DOCKER_IMG=jupyter/datascience-notebook
fi

export NBDIR
export DOCKER_IMG
export DOCKER_NAME

# break down the command line
CL_VOLUME="$NBDIR:/home/jovyan/work"
CL_PORT="127.0.0.1:8888:8888"
CL_SCRIPT="start-notebook.sh"

echo "Starting $DOCKER_NAME"
echo "  Docker image:   $DOCKER_IMG"
echo "  Volume mapping: $CL_VOLUME"
echo "  Port mappping:  $CL_PORT"
echo "  Run target:     $CL_SCRIPT"
sudo docker run --name "$DOCKER_NAME" --link main-mongo:mainmongo -v "$CL_VOLUME" -p "$CL_PORT" "$DOCKER_IMG" "$CL_SCRIPT"
