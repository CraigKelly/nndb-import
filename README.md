nndb-import
=================================

***NOTE:*** This is a Python 3 app - we're not supporting Python 2.7

Import USDA National Nutrient Database ASCII files in to a MongoDB collection.

We developed this small python against SR27. Those data files are available
from the download link at http://www.ars.usda.gov/Services/docs.htm?docid=8964

Some of the bulk operations we use weren't available until PyMongo version
3.0. Ubuntu packages a different version. As a result, we have supplied a
`setup.sh` script for setting up a virtualenv, and a `run.sh` to use it. If
you're already familiar with using virtualenv's then you should just install
the requirements.txt and run `./nndb_import.py`. It has some optional
parameters and requires a specified directory containing the ASCII files
linked above. Run `./nndb_import.py --help` for details.
