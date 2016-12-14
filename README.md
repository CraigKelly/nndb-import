# nndb-import

## Using this data

If a flat file of food and ingredients with the most common nutrients is all
you want, we've made that available at
[data.world](https://data.world/craigkelly/steam-game-data)

If you want a denormalized, integrated MongoDB database of the USDA's National
Nutrient database, then please see below.

## Using this code

Import USDA National Nutrient Database ASCII files in to a MongoDB collection.

We developed this small python against SR27. Those data files are available
from the download link at http://www.ars.usda.gov/Services/docs.htm?docid=8964

Some of the bulk operations we use weren't available until PyMongo version
3.0. Ubuntu packages a different version. As a result, we have supplied a
`setup.sh` script for setting up a virtualenv, and a `run.sh` to use it. If
you're already familiar with using virtualenv's then you can do it all yourself:

```
$ cd nndb-import
$ virtualenv venv
$ . venv/bin/activate
$ pip install -r requirements.txt
$ ./nndb_import.py
```

`./nndb_import.py` requires a specified directory containing the ASCII files
linked above. Run `./nndb_import.py --help` for details.

## Optimization

There is a small attempt at a GA optimization approach for recommended
nutritional intake based on an attempt at a fitness function tailored to my
goals. It's there for historical purposes.

I won't keep you in suspense. The best recommendations generated were either
nonsensical (3 pounds of celery seed?!) *or* a version of Michael Pollan's
[advice](http://www.nytimes.com/2007/01/28/magazine/28nutritionism.t.html):

> Eat food. Not too much. Mostly plants.

## Note

This is a Python 3 app - we're not supporting Python 2.7
