#!/usr/bin/env python3
# -*- coding: latin_1 -*-

# Note that the file encoding we use is the same as the ASCII files -
# see nndb_recs below

"""nndb-import.py

These are the files that we support as documented in the file sr27_doc.pdf
as given in the SR27 distribution of these files. The four files identified
as the four "principal" files are the first four listed:

   Name      Descrip
   ========= ==========================================
   FOOD_DES  food descriptions
   NUT_DATA  nutrient data
   WEIGHT    weights
   FOOTNOTE  footnotes
   --------
   FD_GROUP  food group descriptions
   LANGUAL   LanguaL Factors
   LANGDESC  LanguaL Factors descriptions
   NUTR_DEF  Nutrient definitions
   SRC_CD    source code
   DERIV_CD  data derivation code description
   DATA_SRC  Sources of data
   DATSRCLN  Sources of data Link
"""

import sys
import os
import argparse
import collections
import functools


class BulkFailure(Exception):
    """Custom bulk import failure exception"""

    pass

try:
    import pymongo
except:
    sys.stderr.write("\n\nCould not import PyMongo - it is required\n\n")
    raise
if (2, 6) > tuple([int(i) for i in getattr(pymongo, 'version', '0.0.0').split('.')][:2]):
    sys.stderr.write("\n\nNeed at version 2.6 of PyMongo because we use bulk loading\n\n")
    raise BulkFailure("PyMongo version too low")


# Use the unit abbreviations we like - this means that the units to expect are:
#   mcg  - micrograms
#   mg   - milligrams
#   g    - grams
#   IU   - Intl Units
#   kcal - kilocalories
#   kJ   - kilojoules
UNIT_REPLACEMENTS = {
    "µg": "mcg",   # micrograms
    "�g":  "mcg",
}


def report_bulk(results):
    """pretty print results and raise an exception if there is an error."""
    from pprint import pprint
    pprint(results)
    if results.get('writeConcernErrors', []) or results.get('writeErrors', []):
        raise BulkFailure("Failed on bulk insertion")


def nndb_recs(filename, field_names=None):
    """Iterator that yields a dictionary of (field-name,value) pairs.
    Note that the order of field_names is important!
    """
    if not field_names:
        raise ValueError("No fields specified for nndb recs")

    # Filter for a single field in the file
    def filt(f):
        if len(f) > 1 and f[0] == '~' and f[-1] == '~':
            f = f[1:-1]
        return f

    # Note the encoding - the documentation says the files are in
    # "ASCII (ISO/IEC 8859-1)" which might make you think you could assume
    # an encoding of ASCII or UTF-8, but they actually do use 8859-1 (latin_1)
    # characters that are not valid ASCII or UTF-8.
    with open(filename, "r", encoding="latin_1") as datafile:
        for line in datafile:
            line = line.strip()
            if len(line) < 1:
                continue
            yield dict([
                (name, filt(fld))
                for name, fld in zip(field_names, line.split('^'))
            ])


def recs_to_dict(keyfldname, recs):
    """Given an iterable of recs and a keyfldname, build and return a
    dictionary of records"""
    d = dict()
    for rec in recs:
        d[rec[keyfldname]] = rec
    return d


def recs_to_lookup(filename):
    """Unlike recs_to_dict, we turn a 2-column data file (where the cols are
    assumed to be key and value) into a dictionary
    """
    d = {"": ""}
    for flds in nndb_recs(filename, ["key", "val"]):
        d[flds["key"]] = flds["val"]
    return d


food_des_recs = functools.partial(nndb_recs, field_names=[
    "_id",  # aka NDB_No
    "food_group_code",  # references the food group descriptions
    "descrip",
    "short_descrip",
    "common_name",
    "mfg_name",
    "survey",  # if used in FNDDS (if so, nutrient data should be complete)
    "refuse_descrip",  # description of inedible parts (seed, bone, etc)
    "refuse",  # percentage of refuse
    "scientific_name",  # generally for least processed, raw form if applicable
    "n_factor",  # factor for nitrogen to protein
    "protein_factor",  # factor for calories from protein
    "fat_factor",  # factor for calories from fat
    "carb_factor",  # factor for calories from carbohydrates
])


nut_data_recs = functools.partial(nndb_recs, field_names=[
    "ndb_num",  # aka NDB_No, the _id to FOOD_DES
    "nutrient_id",  # aka Nutr_No
    "nutrient_val",  # Num edible portion in 100g
    "data_point_count",  # Num data points used for analysis
    "std_error",  # std err of mean, can be null (if data_point_count < 3)
    "source_code",
    "derivation_code",
    "ref_nbd_id",  # May refer to another item used to calc a missing value
    "add_nutrition_mark",  # Used for fortified cereals
    "num_studies",  # Num
    "min_value",  # Num
    "max_value",  # Num
    "degrees_freedom",  # Num
    "lower_err_bound",  # Num - lower 95% error bound
    "upper_err_bound",  # Num - lower 95% error bound
    "statistical_comments",
    "confidence_code",  # Indicates overall assessment of quality
])


nutr_def_recs = functools.partial(nndb_recs, field_names=[
    "nutrient_id",  # aka Nutr_No
    "units",  # mg, g, lb, etc
    "tagname",  # INFOODS tag
    "descrip",
    "decimal_places",
    "sr_sort_order",  # num
])


def num(s, filt=float):
    """Helper for numeric fields - we accept a string, convert it using filt,
    and will return an empty string if there is a ValueError converting
    """
    if not s:
        return ""
    try:
        return filt(s)
    except ValueError:
        return ""


def nums(rec, field_names, filt=float):
    """Mutate rec using num (with filt) for all given field names."""
    for fn in field_names:
        rec[fn] = num(rec.get(fn, ""), filt=filt)


def process_directory(mongo, dirname):  #NOQA (ignore McCabe for this func)
    """Process single directory"""
    # Shorten our code a little
    def get_fn(fn):
        return os.path.join(dirname, fn)

    # Read in various dictionaries we need first
    print("Reading food group codes")
    food_grp_codes = recs_to_lookup(get_fn("FD_GROUP.txt"))

    print("Reading LanguaL codes")
    langual_codes = recs_to_dict(
        "code",
        nndb_recs(get_fn("LANGDESC.txt"), ["code", "descrip"])
    )
    langual_codes[""] = ""

    # Clearing previous entries
    print("Clearing database")
    bulk = mongo.initialize_ordered_bulk_op()
    bulk.find({}).remove()
    report_bulk(bulk.execute())

    # First create all the entries with default values from the main file
    # Note that we use upsert - one of main goals is to be restartable and
    # re-runnable.
    print("Creating entries...")
    count = 0

    survey_stats = collections.defaultdict(int, [("", 0), ("Y", 0)])
    entries = []

    for entry in food_des_recs(get_fn("FOOD_DES.txt")):
        # Just in case we ever decide to use something else for _id
        entry_id = entry['_id']
        entry['ndb_num'] = entry_id

        # Handle numeric fields
        nums(entry, ["n_factor", "protein_factor", "fat_factor", "carb_factor"])

        # Setup defaults
        entry.update({
            'nutrients': list(),
            'food_group_descrip': food_grp_codes[entry["food_group_code"]],
            'footnotes': list(),
            'langual_entries': list(),
            'measures': list(),
        })

        # Upsert our entry
        entries.append(entry)

        count += 1
        survey_stats[entry['survey']] += 1
        if count % 3000 == 0:
            print("  Created %7d" % count)

    # Perform bulk operation
    print("Sending bulked inserts")
    total_inserts = len(mongo.insert_many(entries, False).inserted_ids)
    entries = []   # Clean up

    print("...Total Records Seen: %d" % count)
    print("...Total Inserts Seen: %d" % total_inserts)
    print("Survey stats:")
    for k, v in survey_stats.items():
        print("  %4s: %12d" % (k, v))
    print("")

    if count != total_inserts:
        raise BulkFailure("Could not insert initial records")

    print("Loading weights/measures")
    weight_recs = nndb_recs(get_fn("WEIGHT.txt"), [
        "ndb_num",
        "seq",
        "amount",
        "descrip",
        "gram_weight",
        "num_data_points",
        "stddev"
    ])

    bulk = mongo.initialize_unordered_bulk_op()
    count = 0
    for entry in weight_recs:
        bulk.find({'_id': entry["ndb_num"]}).update({"$push": {"measures": entry}})
        count += 1
        if count % 10000 == 0:
            print("  weights: %7d" % count)
    print("...Total weights read: %d" % count)

    print("Bulk updating weights")
    report_bulk(bulk.execute())

    print("Loading LanguaL Codes...")
    bulk = mongo.initialize_unordered_bulk_op()
    count = 0
    for entry in nndb_recs(get_fn("LANGUAL.txt"), ["ndb_num", "code"]):
        lang = langual_codes[entry["code"]]
        bulk.find({'_id': entry["ndb_num"]}).update({"$push": {"langual_entries": lang}})
        count += 1
        if count % 10000 == 0:
            print("  LanguaL items: %7d" % count)
    print("...Total codes read: %d" % count)

    print("Bulk updating LanguaL codes")
    report_bulk(bulk.execute())

    print("Reading source code descrips")
    src_codes = recs_to_lookup(get_fn("SRC_CD.txt"))

    print("Reading data derivation code descrips")
    deriv_codes = recs_to_lookup(get_fn("DERIV_CD.txt"))

    print("Reading data sources for footnotes")
    data_srcs = recs_to_dict("datasrc_id", nndb_recs(get_fn("DATA_SRC.txt"), [
        "datasrc_id",
        "authors",
        "title",
        "year",
        "journal",
        "vol_city",
        "issue_state",
        "start_page",
        "end_page",
    ]))

    print("Adding footnotes to food items...")
    footnote_recs = nndb_recs(get_fn("FOOTNOTE.txt"), [
        "ndb_num",
        "footnote_num",
        "footnote_type",
        "nutr_num",
        "text"
    ])
    bulk = mongo.initialize_unordered_bulk_op()
    count = 0
    for entry in footnote_recs:
        entry["type"] = "footnote"
        bulk.find({'_id': entry["ndb_num"]}).update({"$push": {"footnotes": entry}})
        count += 1
        if count % 50000 == 0:
            print("  footnotes: %7d" % count)
    print("...Total foot notes: %7d" % count)

    print("Adding data sources to food items as footnotes...")
    count = 0
    for entry in nndb_recs(get_fn("DATSRCLN.txt"), ["ndb_num", "nutr_num", "datasrc_id"]):
        entry.update(data_srcs[entry["datasrc_id"]])
        entry["type"] = "data-source"
        bulk.find({'_id': entry["ndb_num"]}).update({"$push": {"footnotes": entry}})
        count += 1
        if count % 50000 == 0:
            print("  data sources: %7d" % count)
    print("...Total data sources: %7d" % count)

    print("Bulk updating footnotes")
    report_bulk(bulk.execute())

    print("Reading nutrient defs...")
    nutr_defs = recs_to_dict(
        "nutrient_id",
        nutr_def_recs(get_fn("NUTR_DEF.txt"))
    )

    print("Loading nutrition items...")
    bulk = mongo.initialize_unordered_bulk_op()
    count = 0
    for entry in nut_data_recs(get_fn("NUT_DATA.txt")):
        nums(entry, [
            "nutrient_val",
            "data_point_count",
            "std_error",
            "num_studies",
            "min_value", "max_value",
            "degrees_freedom",
            "lower_err_bound", "upper_err_bound",
        ])

        # Add descriptions for the codes we know
        entry["source_descrip"] = src_codes[entry["source_code"]]
        entry["derivation_descrip"] = deriv_codes[entry["derivation_code"]]

        # Just add the nutrient def info to the entry
        xtra = nutr_defs[entry["nutrient_id"]]
        entry.update(xtra)

        # Ensure units are the way we want them
        entry["units"] = UNIT_REPLACEMENTS.get(entry["units"], entry["units"])

        bulk.find({'_id': entry["ndb_num"]}).update({"$push": {"nutrients": entry}})
        count += 1
        if count % 50000 == 0:
            print("  nutrient items: %7d" % count)
    print("...Total nutrient items: %7d" % count)

    print("Bulk updating nutrient items")
    report_bulk(bulk.execute())


def main():
    """Entry point"""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "targetdir",
        help="The directory containing the ASCII data files from "
    )
    parser.add_argument(
        "--mongourl",
        help="The MongoDB URL to use for connection",
        default="mongodb://localhost:27017/nutrition"
    )
    parser.add_argument(
        "--collection",
        help="The collection where the data will be loaded (PREV DATA WILL BE DELETED)",
        default="nndb"
    )
    args = parser.parse_args()

    print(args.targetdir)

    print("Connecting to %s" % args.mongourl)
    client = pymongo.MongoClient(args.mongourl)
    db = client.get_default_database()
    print("Using collection %s" % args.collection)
    coll = db[args.collection]
    print("Processing files using directory %s" % args.targetdir)
    process_directory(coll, args.targetdir)


if __name__ == "__main__":
    main()
