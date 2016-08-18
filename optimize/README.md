recommend-intake README
===========================

This project is for attempting to optimize nutritional intake. It assumes a
MongoDB database created as per `../nndb_import.py`.

We used
[Dietary Reference Intakes](http://www.nap.edu/catalog/11537/dietary-reference-intakes-the-essential-guide-to-nutrient-requirements)
from the National Academies Press as the reference for the list of
micronutrients encoded in `micro_reqs.py`

`build_foods.sh` uses `food_query.js` to create our list of foods from the
MongoDB database (with nutrient info) to use as input


`optimize.py` is the actual optimization program

If you've already populated a MongoDB via the nndb project, you
should be able to just:

    ./build_food.sh
    ./optmize.py
