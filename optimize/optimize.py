#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# pylama:ignore=D213,D400,E501,E221,D103,D205,D209,E124,E127,E128

"""Find optimal nutritional combinations

This optimizer assumes that the foods to be targeted are in the file
foods.jsontxt.gz as created by build_foods.sh. That means that each line is the
JSON representation of a record as created by nndb-import (see
https://github.com/CraigKelly/nndb-import)
"""

import sys
import gzip

from functools import partial

# Try to use various speedy json libraries then fall back to stdlib
try:
    import ujson as json
except:
    try:
        sys.stderr.write("No ujson, trying cjson\n")
        import cjson as json
    except:
        sys.stderr.write("No cjson, using stdlib json\n")
        import json


import scipy
import scipy.stats
sp = scipy
stats = sp.stats

from micro_reqs import ALL_MICROS  #NOQA


# Parameters we use
INIT_RANDOMS    = 10000                       # Initial random members of population
RND_EXP_ENTRIES = 4                           # Exp value for # of non-zero entries
MAX_AMT         = 5.0                         # Non-zero entry max value
POP_SIZE        = 200                         # Pop size (after initial population)
MUTATE_RATE     = 0.20                        # Rate at which entry is mutated
MUTATE_BIG      = MUTATE_RATE * 0.20          # Part of mutate rate, chance of "big" mutation
IMMORTALS       = 5                           # Number of pop members that carry over
MERGE_SIZE      = 4                           # Number of solutions we sample for merge
SPARSITY_MAX    = (RND_EXP_ENTRIES-1) * (MAX_AMT*0.75)


# We pre-define random routines so that we can swap out (Python's native
# Mersenne twister is fine but a little slow for what we're doing)
randrange = partial(sp.random.randint, 0)
rand = sp.random.rand


def choice(lst):
    return lst[randrange(len(lst))]


# Simple logistic function for scipy arrays
def logistic(spa):
    return 1.0 / (1.0 + scipy.exp(-spa))


# Simple logging stand-in
def info(s, *args):
    if args:
        s = s % args
    print(s)


FILTER_WORDS = [i.replace('\s', ' ') for i in """
    applesauce        mashed
    bacon             meatless
    beverage          millet
    breaded           nectar
    bulgur            noodles
    candied           oil-roasted
    catsup            pork
    celery\sflakes
    chili             products
    chowchow          puffs
    cocktail          ranch
    cilantro
    cornmeal          relish
    cornstarch        rice
    couscous          soymilk
    dehydrated        spaghetti
    flour             spread
    franks            succotash
    fried             syrup
    groats            tapioca
    hash brown        taro
    hominy            tomato\sproducts
    hummus            vegetables
    juice             vegetarian
    lambsquarters     veggie
    liquid\sfrom      vermicelli
    macaroni          wheat
""".split()]

FILTER_SPLITS = ["sweet", "sweetened" "wheat", ]


def food_filter(line):
    line = line.strip()
    if not line:
        return None

    food = json.loads(line)
    if not food:
        return None

    descrip = food.get('descrip', '').lower()
    if not descrip:
        return None

    for word in FILTER_WORDS:
        if word in descrip:
            return None

    parts = descrip.split(',')
    for part in parts:
        part = part.strip()
        if not part:
            continue
        for check in FILTER_SPLITS:
            if check == part:
                return None

    return food


def read_foods(filename):
    # Test show zcat subprocess MUCH faster then `with gzip.open(filename, 'r')`
    with gzip.open(filename) as fh:
        for line in fh:
            food = food_filter(line.decode('utf-8'))
            if food:
                yield food


def extract_nutrients(food):
    contains = dict(
        (n["nutrient_id"], n["nutrient_val"]) for n in food["nutrients"]
    )
    return [contains.get(nid, 0.0) for _, nid, _, _, _ in ALL_MICROS]


class opt_engine(object):
    """Given a list of food objects from our file, perform the various
    optmization functions we want
    """

    def __init__(self, food_details):
        """Load initial matrices and create initial expanded population."""
        self.food_details = food_details
        self.food_count = len(food_details)

        # We want our random instances to have an expected number of entries
        # equal to RND_EXP_ENTRIES, which for Binomial(n,p) is np. So we know
        # p is RND_EXP_ENTRIES/n
        self.rnd_entries = partial(
            stats.binom.rvs,
            self.food_count,
            float(RND_EXP_ENTRIES) / float(self.food_count)
        )

        # |foods| x |nutrients| 2-d array
        self.foods = sp.array([extract_nutrients(f) for f in food_details])

        # RDA and UL vectors
        self.RDA, self.UL = [], []
        for _, _, _, r, u in ALL_MICROS:
            self.RDA.append(r)
            self.UL.append(u)
        self.RDA, self.UL = sp.array(self.RDA), sp.array(self.UL)

        # Our first generation contains all single foods and INIT_RANDOMS
        # inital random entries
        pop = []
        for i in range(self.food_count):
            one = [0.0] * self.food_count
            one[i] = 1.0
            pop.append(list(one))

        for _ in range(INIT_RANDOMS):
            pop.append(self.rand_inst())

        self.set_pop(pop)
        self.last_population = []
        self.last_popnutrition = []

    def set_pop(self, pop):
        """Directly set population and recalc the pop-nutrition grid."""
        # |members| x |foods| 2-d array
        self.population = sp.array(pop)
        self.popnutrition = sp.dot(self.population, self.foods)

    def rand_inst(self):
        """Return a random instance based on RND_EXP_ENTRIES and current foods."""
        inst = [0.0] * self.food_count

        entries = self.rnd_entries()
        if entries < 1:
            entries = RND_EXP_ENTRIES  # extra boost to our average

        idxs = set([randrange(len(inst))])
        while len(idxs) < entries:
            idxs.add(randrange(len(inst)))

        for idx in idxs:
            inst[idx] = choice([0.5, 1.0, 1.5, 2.0])

        return inst

    def calories(self, inst):
        """Given an instance, return the total calories and the total g's of sugar."""
        total_cals = 0.0
        total_sugar = 0.0

        for idx, amt in enumerate(inst):
            if abs(amt - 0.0) < 0.00001:
                continue

            food = self.food_details[idx]

            for n in food["nutrients"]:
                if n["nutrient_id"] == "208":
                    total_cals += float(n["nutrient_val"]) * amt
                if n["nutrient_id"] == "269":
                    total_sugar += float(n["nutrient_val"]) * amt

        return total_cals, total_sugar

    SCORE_WEIGHTS = sp.array([
        2.0,  # RDA
        1.0,  # nutrient per gram
        1.8,  # UL
        1.5,  # cals/gram
        1.2,  # sparsity
        1.0,  # sugar
    ])

    def score(self, inst, nutr):
        """Return a fitness score and the originating score vector for the given
        instance and it's nutrition space vector."""
        assert len(inst) == self.foods.shape[0]
        assert len(nutr) == self.foods.shape[1]
        assert len(self.RDA) == len(self.UL) == len(nutr)

        # Figure any nutrients above the upper limit in percentage units.
        too_much = (nutr - self.UL) / self.UL
        calories, sugar = self.calories(inst)
        grams = 100.0 * inst.sum()  # Our database measures everything in 100g units

        # nutrient as percent of RDA, clipped to remove advantage for going over
        nutr_scores = sp.clip(nutr / self.RDA, 0.0, 1.01)

        components = self.SCORE_WEIGHTS * sp.array([
            # good stuff (note that we want to MINIMIZE our score
            0.0 - nutr_scores.mean(),                                # RDA, but no credit for going over
            0.0 - (nutr_scores.sum() / grams),                       # Nutrient score per gram

            # bad stuff
            too_much[too_much > -0.01].sum(),                        # UL, but only as we get high
            logistic(calories / grams),                              # cals per gram
            logistic(len(inst[inst > 0]) / float(RND_EXP_ENTRIES)),  # Simpler is better
            logistic(sugar)                                          # sugar is bad, mmm-kay
        ])

        return components.mean(), components

    def mutate(self, inst):  #NOQA
        """Return a mutated copy of the given instance"""
        rnd_inst = list(inst)

        for idx, val in enumerate(inst):
            roll = rand()
            if roll > MUTATE_RATE:
                continue  # No mutation here

            if roll < MUTATE_BIG and val > 0.0:
                # Swapping with blank index - find the other, do the swap, and leave
                blank_idx = randrange(len(inst))
                while inst[blank_idx] > 0.0:
                    blank_idx = randrange(len(inst))
                rnd_inst[idx], rnd_inst[blank_idx] = rnd_inst[blank_idx], rnd_inst[idx]
                continue

            if roll < MUTATE_BIG:
                modifier = choice([1.5, 1.75, 2.0, 2.25])  # Big jump
            else:
                modifier = choice([0.25, 0.5, .75, 1.0, 1.25])  # Regular jump

            if val <= 0.0:
                val = modifier
            else:
                val = sp.clip(val + (choice([-1.0, 1.0]) * modifier), 0.0, MAX_AMT)

            rnd_inst[idx] = val

        # All of this is great, but we tend to just get bigger and bigger - we want
        # lots of sparsity AND a low total sum
        while sum(rnd_inst) > SPARSITY_MAX:
            for idx in range(len(rnd_inst)):
                if rnd_inst[idx] <= 0.1:
                    rnd_inst[idx] = 0.0
                elif rand() < 0.70:
                    rnd_inst[idx] *= 0.5
                else:
                    rnd_inst[idx] = 0.0

        return rnd_inst

    def crossover(self, inst1, inst2):
        """Return a new instance via cross over with the 2 given instances."""
        return [x if rand() < 0.5 else y for x, y in zip(inst1, inst2)]

    def winner(self):
        """Currently, chose a winner from the population with tournament sel."""
        idx1 = randrange(len(self.population))
        idx2 = randrange(len(self.population))
        return min(idx1, idx2)

    def generation(self):
        """Do a single generation of work."""
        all_scored = []
        for inst, nutr in zip(self.population, self.popnutrition):
            score, score_vector = self.score(inst, nutr)
            all_scored.append((score, inst))

        all_scored.sort(key=lambda one: one[0])

        # Keep previous generation in sorted order
        self.last_population = sp.array([inst for _, inst in all_scored])
        self.last_popnutrition = sp.dot(self.last_population, self.foods)

        # Now we are creating the next generation

        # Don't add dups to a generation
        new_gen = []
        seen = set()

        def add_to_gen(inst):
            key = tuple(inst)
            if key in seen:
                return
            seen.add(key)
            new_gen.append(inst)

        # Keep top N entries, top N entries with mutations, and top N entries with
        # one-off removed and then mutated
        for score, inst in all_scored[:IMMORTALS]:
            # top entries
            add_to_gen(inst)
            # mutated
            add_to_gen(self.mutate(inst))
            # one-off removed and then mutated
            for idx, val in enumerate(inst):
                if val > 0.0:
                    one_off = list(inst)
                    one_off[idx] = 0.0
                    add_to_gen(one_off)
                    add_to_gen(self.mutate(one_off))

        # Fill out the rest of the generation
        # Note we're actually TRIPLE our population size - We use the population
        # size for new random entries, tradition select/crossover/mutate entries,
        # and sample/sum/mutate entries. (NOte our sample/sum/mutate works because
        # our mutate routine has a final "re-balance + force sparsity step"
        for _ in range(POP_SIZE):
            # simple random entry
            add_to_gen(self.rand_inst())

            # Merged entry
            merged = sp.array(self.population[self.winner()])
            for _ in range(MERGE_SIZE-1):
                merged += sp.array(self.population[self.winner()])
            add_to_gen(self.mutate(list(merged)))

            # "Normal" creation via selection, crossover/breeding. and mutation
            add_to_gen(self.mutate(self.crossover(
                self.population[self.winner()],
                self.population[self.winner()]
            )))

        # Have a new generation
        self.set_pop(new_gen)

    def dump_instance(self, inst, nutr, info=info):
        """Given an instance and it's nutritional space vector (just like score),
        output a decent, printable representation of the instance
        """
        score, score_vector = self.score(inst, nutr)
        info("Solution with score %12.4f (vector %s)", score, score_vector)
        for mic, amt in zip(ALL_MICROS, nutr):
            name, _, units, rda, ul = mic
            info("  NUTR %-15s: %8.2f %-5s, %8.2f%% of RDA %8.2f (UL %8.2f)",
                         name,  amt, units, (amt/rda)*100.0, rda,      ul
            )

        total_cals = 0.0

        for idx, amt in enumerate(inst):
            if abs(amt - 0.0) < 0.00001:
                continue

            food = self.food_details[idx]

            cals = '?'*8
            for n in food["nutrients"]:
                if n["nutrient_id"] == "208":
                    cals = float(n["nutrient_val"]) * amt
                    total_cals += cals
                    cals = "%8.2f" % cals
                    break

            info("  FOOD %8.2f units (%s cals) of %s (grp %s)",
                amt,
                cals,
                food["short_descrip"],
                food["food_group_descrip"]
            )

        info("Total Calories: %8.2f", total_cals)


def food_scores(engine):
    """Just output all foods that we allow with the score that you would get."""
    one_hot = []
    for i in range(engine.food_count):
        one = [0.0] * engine.food_count
        one[i] = 1.0
        one_hot.append(list(one))

    engine.set_pop(one_hot)
    engine.generation()

    for food, nutr in zip(engine.last_population, engine.last_popnutrition):
        engine.dump_instance(food, nutr)
        info('='*78)


def main():
    input_file = "foods.jsontxt.gz"  # TODO: command line or stdin or...

    info("Micronutrients used for calcs: %d", len(ALL_MICROS))

    info("Reading input file %s", input_file)
    food_details = list(read_foods(input_file))

    engine = opt_engine(food_details)
    info("Init population shape: %s", engine.population.shape)
    info("Food matrix shape: %s", engine.foods.shape)

    if '-foodscores' in sys.argv[1:]:
        food_scores(engine)
        return
    elif '-topn' in sys.argv[1:]:
        print("TODO: top-n per nutrient output")
        return

    # Do our generations
    # TODO: good stopping criteria
    with open("results", "w") as results:
        def file_output(s, *args):
            if args:
                s = s % args
            results.write(s)
            results.write('\n')
            results.flush()

        info("Pre-Running 2 generations")
        engine.generation()
        engine.generation()

        seen = set()

        for gen in range(1, 5000+1):
            engine.generation()

            best_food, best_nutr = engine.last_population[0], engine.last_popnutrition[0]
            info("BEGIN Generation %d (pop size %d)", gen, len(engine.last_population))
            engine.dump_instance(best_food, best_nutr)
            info("END Generation %d", gen)
            info('-'*20)

            for food, nutr in zip(engine.last_population[:3], engine.last_popnutrition[:3]):
                key = tuple(food)
                if key in seen:
                    continue

                seen.add(key)

                file_output("First Seen Generation %d", gen)
                engine.dump_instance(food, nutr, info=file_output)
                file_output('='*78)


if __name__ == "__main__":
    main()
