"""Micronutrient requirements that we know about

Each micronutrient that we care about is in the list ALL_MICROS, is also a
member of this module, and is a tuple of the form (name, id, units, RDA, UL)
where

    * Name  = A fairly standard name (at least in English in the US)
    * ID    = The nutrient number used as the key in the NUTR_DEF.txt file in the nndb
    * units = A string representing the units for RDA and UL
    * RDA   = Rec Daily Allow - calc from EAR to meet needs of 97-98% of pop
    * UL    = Upper intake Level - max safe intake level

Note that the RDA is generally calculated from an EAR (also available in the
literature but not recorded here), but may actually be an AI (see below). We
reserve the right to use silly ultra-high UL's for micronutrients that have no
known or recorded UL's. This is STRICTLY for the optimizations ran here and is
not an assertion of fact or theory.

When in doubt we use higher RDA numbers and lower UL numbers.

Mentioned above:

    * EAR = Est Avg Req - daily intake est to meet needs of 50% of pop
    * AI  = Adequate Intake - Guess at healthy levels for most ind's if EAR not avail

Nutrients skipped:

    * Biotin - will get from your protein sources and/or cheat meals
    * Choline - will get from your protein sources and/or cheat meals
    * Vitamin D - go outside
    * Vitamin K - nearly impossible to get too litle K and cause health issues
      without a specific syndrome
    * Pantothenic Acid - not a lot of actual nutrient info for this right now
    * Chromium - "widely distributed in the food supply", little required, data
      is spotty
    * Fluoride - we live in a civilized area with fluoridated water
    * Iodine - not in the nndb
    * Molybdenum - not in nndb
    * K, Na, Cl - assuming we'll get enough. (Note that an optimization strategy
      might want K > Na by mass though... cough, cough...)
    * Arsenic - no RDA or AI
    * Boron - no RDA or AI
    * Nickel - no RDA or AI
    * Silicon - no RDA or AI
    * Vanadium - no RDA or AI

Special Notes:

    * Vit A is in RAE mcg: 1 mcg RAE = 1 mcg retinol, 12 mcg b-carotene, and
      24 mcg a-carotene or b-cryptoxanthin.

    * Magnesium has a UL **less than** the RDA for pharmacological magnesium

    * The RDA for Iron for females 19-50 is 18.0 (vs the 8.0 we list per the
      amount for males). Since this is currently a hobby project and I'm a male
      we go with 8.0. Caveat researcher.
"""

import sys

# TODO: 320 is RAE vit A, but there are also 318,319,321,322 - are there any
#       foods with those specified but not 320?

# TODO: 435 is DFE Folate - what about 417,431,432? Are they all always reported?


ALL_MICROS = [
    # Name           ID     Units    RDA       UL
    # -------------  ---    ----- ------   ------
    ("Vitamin A",   "320", "mcg",  900.0,  3000.0),
    ("Vitamin B6",  "415", "mg",     1.7,   100.0),
    ("Vitamin B12", "418", "mcg",    2.4,   500.0),  # No UL spcified - guessed
    ("Vitamin C",   "401", "mg",    90.0,  2000.0),
    ("Vitamin E",   "323", "mg",    15.0,  1000.0),
    ("Folate",      "435", "mcg",  400.0,  1000.0),
    ("Niacin",      "406", "mg",    16.0,    35.0),
    ("Riboflavin",  "405", "mg",     1.3,  1000.0),  # No UL specified - guessed
    ("Thiamin",     "404", "mg",     1.2,  1000.0),  # No UL specified - guessed
    ("Calcium",     "301", "mg",  1200.0,  2500.0),
    ("Copper",      "312", "mcg",  900.0, 10000.0),
    ("Iron",        "303", "mg",     8.0,    45.0),  # RDA for females 19-50 is 18.0
    ("Magnesium",   "304", "mg",   420.0, 10000.0),  # Note that the UL is guessed
    ("Manganese",   "315", "mg",     2.3,    11.0),  # No RDA - using AI and UL
    ("Phosphorus",  "305", "mg",   700.0,  4000.0),
    ("Selenium",    "317", "mcg",   55.0,   400.0),
    ("Zinc",        "309", "mg",    11.0,    40.0),
]


def _create_top_level(module):
    for n in ALL_MICROS:
        name = n[0].replace(' ', '_').upper()
        setattr(module, name, n)

_create_top_level(sys.modules[__name__])
