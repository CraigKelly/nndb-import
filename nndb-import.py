#!/usr/bin/env python

"""nndb-import.py
"""

import sys
import os
import argparse
import collections

try:
    import pymongo
except:
    sys.stderr.write("\n\nCould not import PyMongo - it is required\n\n")
    raise

#We go ahead and define field names: one day it might be useful to have these
#accessible to code
FOOD_DES_FIELDS = [
    "_id", #aka NDB_No
    "food_group_code", #
    "descrip", #
    "short_descrip", #
    "common_name", #
    "mfg_name", #
    "survey", #if used in FNDDS (if so, nutrient data should be complete)
    "refuse_descrip", #description of inedible parts (seed, bone, etc)
    "refuse", #percentage of refuse
    "scientific_name", #generally for least processed, raw form if applicable
    "n_factor", #factor for nitrogen to protein
    "protein_factor", #factor for calories from protein
    "fat_factor", #factor for calories from fat
    "carb_facto", #factor for calories from carbohydrates
]

NUT_DATA_FIELDS = [
    "ndn_num", #aka NDB_No, the _id to FOOD_DES
    "nutrient_id", #aka Nutr_No
    "nurtient_val", #Num edible portion in 100g
    "data_point_count", #Num data points used for analysis (0 means calc, etc)
    "std_error", #Num - std err of mean, can be null (if data_point_count < 3)
    "source_code",
    "derivation_code",
    "ref_nbd_id", #May refer to another item used to calc a missing value
    "add_nutrition_mark", #Used for fortified cereals
    "num_studies", #Num
    "min_value", #Num
    "max_value", #Num
    "degrees_freedom", #Num
    "lower_err_bound", #Num - lower 95% error bound
    "upper_err_bound", #Num - lower 95% error bound
    "statistical_comments",
    "confidence_code", #Indicates overall assessment of quality for sampling, etc
]

def nndb_recs(filename, field_names):
    """Iterator that yields a dictionary of (field-name,value) pairs. Note that
    the order of field_names is important!
    """

    #Filter for a single field in the file
    def filt(f):
        if len(f) > 1 and f[0] == '~' and f[-1] == '~':
            f = f[1:-1]
        return f

    for line in open(filename, "r"):
        line = line.strip()
        if len(line) < 1:
            continue
        yield dict([
            (name,filt(fld))
            for name,fld in zip(field_names, line.split('^'))
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
    """Mutate rec using num (with filt) for all given field names
    """
    for fn in field_names:
        rec[fn] = num(rec.get(fn, ""), filt=filt)

def process_directory(mongo, dirname):
    #Shorten our code a little
    j = os.path.join

    #First create all the entries with default values from the main file
    #Note that we use upsert - one of main goals is to be restartable and
    #re-runnable.
    print "Creating entries..."
    count = 0
    survey_stats = collections.defaultdict(int, [("", 0), ("Y", 0)])
    for entry in nndb_recs(j(dirname, "FOOD_DES.txt"), FOOD_DES_FIELDS):
        #Just in case we ever decide to use something else for _id
        entry['nbd_num'] = entry['_id']
        #Handle numeric fields
        nums(entry, ["n_factor", "protein_factor", "fat_factor", "carb_factor"])
        #Setup defaults
        entry.update({
            'nutrients': list(),
            'food_group_descrip': '', #TODO: pre-read these
            'footnotes': list(),
            'langual_entries': list(),
            'measures': list(),
        })
        #Upsert our entry (already have an _id, so this will be an upsert)
        mongo.save(entry)
        count += 1
        survey_stats[entry['survey']] += 1
    print "...Created %d" % count
    print "Survey stats:"
    for k,v in survey_stats.iteritems():
        print "  %4s: %12d" % (k,v)
    print ""


#TODO: we're going to want a check that all nutrients in an entry have their
#      seq num equal to their array index in nutrients

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("targetdir",
        help="The directory containing the ASCII data files from "
    )
    parser.add_argument("--mongourl",
        help="The MongoDB URL to use for connection",
        default="mongodb://localhost:27017/nutrition"
    )
    parser.add_argument("--collection",
        help="The collection where the data will be loaded",
        default="nndb"
    )
    args = parser.parse_args()

    print args.targetdir

    print "Connecting to %s" % args.mongourl
    client = pymongo.MongoClient(args.mongourl)
    db = client.get_default_database()
    print "Using collection %s" % args.collection
    coll = db[args.collection]
    print "Processing files using directory %s" % args.targetdir
    process_directory(coll, args.targetdir)


if __name__ == "__main__":
    main()
