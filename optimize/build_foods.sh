#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

DB="127.0.0.1:27017/nutrition"
QUERY="$SCRIPT_DIR/food_query.js"
OUTPUT="$(pwd)/foods.jsontxt.gz"

echo "DB:     $DB"
echo "Query:  $QUERY"
echo "Output: $OUTPUT"

echo "WORKING..."
mongo --quiet "$DB" "$QUERY" | gzip > $OUTPUT

echo "...Done: wc stats are"
zcat $OUTPUT | wc
