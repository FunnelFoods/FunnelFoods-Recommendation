import re
import pandas as pd
import ast
from fuzzywuzzy import fuzz

with open("./data/foodList.txt") as f:
    foodList = f.read().splitlines()

food_nutrient_large = pd.read_csv('./data/food_nutrients_dict.csv')

# Reads categorized food with 16,000 rows
food_categ = pd.read_csv('./data/food_categorized_nurtrients_w_name.csv')

# Clean up foodList
foodList = list(filter(
    lambda x: x not in ['baby', 'producer', 'red', '85% lean', 'baked', 'leg', 'greater than 3% juice', 'family style'
        , 'polish', 'greek', 'on the border', 'tlc', 'low calorie', 'milk producer', 'producer milk', 'green', 'grade'],
    foodList))

# Creates a series of food_names with comma, for regex extracting purposes
food_comma = food_categ['food_name'] + ','

# Extracts the food's generic names
food_categ['generic'] = food_comma.str.extract(r'^([^,]*),')[0]

# Get rid of commas, colons, and other special characters
food_clean_name = food_categ['food_name'].str.replace(r'[^a-zA-Z0-9 ]', "").str.replace(r' +', ' ')

# Compiles a list of foodnames with 200k data and with 16k data respectively
foodlist_large = food_nutrient_large['name'].tolist()
foodlist_categ = food_clean_name.tolist()
foodlist_generic = food_categ['generic'].tolist()

# RegEx generator to match with decimals surrounded by indices
regexp = re.compile(r'^[^a-z]+\d\.\d')
findFoodName = re.compile("([^\.]+) \d+\.")

all_scores = []


# Finds the best match of the food item on the receipt from the database. Outputs a list of dictionaries.
def match_receipt(inp):
    food = []
    for line in inp:
        if regexp.search(line):
            if findFoodName.search(line):
                words = findFoodName.search(line).group(0)
                bestRatio = 0
                pos = 0
                name = ""
                for i, f in enumerate(foodlist_categ):
                    r = fuzz.token_set_ratio(words, f)
                    if r > bestRatio:
                        pos = i
                        name = f
                        bestRatio = r
                if bestRatio > 50:
                    d = food_categ.loc[pos, 'nutrients']
                    gen = food_categ.loc[pos, 'generic']
                    food.append([words, name, gen, ast.literal_eval(d)])
    return food


def match_receipt_advanced(inp):
    final = []
    clean_orig_pair = {}
    for line in inp:
        if regexp.search(line):
            if findFoodName.search(line):
                orig = findFoodName.search(line).group(0)
                bestRatio = 0
                name = ""
                for i, f in enumerate(foodList):
                    r = fuzz.token_set_ratio(orig, f)
                    if r > bestRatio:
                        name = f
                        bestRatio = r
                if bestRatio > 65:
                    clean_orig_pair[name] = [orig, bestRatio]
    for clean in clean_orig_pair.keys():
        bestRatio = 0
        pos = 0
        name = ""
        for i, f in enumerate(foodlist_categ):
            r = fuzz.token_set_ratio(clean, f) * 0.5 + fuzz.token_set_ratio(clean_orig_pair[clean][0], f) * 0.5
            if r > bestRatio:
                pos = i
                name = f
                bestRatio = r
        if bestRatio > 60:
            d = food_categ.loc[pos, 'nutrients']
            nutri = ast.literal_eval(d)
            final.append([clean_orig_pair[clean][0], clean, name, nutri])
    return final
