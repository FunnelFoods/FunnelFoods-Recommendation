import csv
import numpy as np
import ast
import nltk
from pattern.text.en import singularize

# import expiration data
reader = csv.DictReader(open("./data/expiration_data.csv"))
expiration = []
for line in reader:
    expiration.append(line)
for i in range(len(expiration)):
    expiration[i] = dict(expiration[i])

# import recipe
reader = csv.DictReader(open("./data/recipe.csv"))
recipe = []
for line in reader:
    recipe.append(line)
for i in range(len(recipe)):
    recipe[i] = dict(recipe[i])
    recipe[i]['ingredients'] = ast.literal_eval(recipe[i]['ingredients'])

# import foodlist
foodList = open("./data/foodList.txt")
foodList = foodList.readlines()
for i in range(len(foodList)):
    foodList[i] = foodList[i][:-1]

nltk.download('averaged_perceptron_tagger')

patterns = """
    NP: {<JJ>*<NN*>+}
    {<JJ>*<NNS>}
    {<JJ>*<NN*><CC>*<NN*>+}
    {<NP><CC><NP>}
    {<RB><JJ>*<NN*>+}
    """

NPChunker = nltk.RegexpParser(patterns)


def prepare_text(input):
    sentences = nltk.sent_tokenize(input)
    sentences = [nltk.word_tokenize(sent) for sent in sentences]
    sentences = [nltk.pos_tag(sent) for sent in sentences]
    sentences = [NPChunker.parse(sent) for sent in sentences]
    return sentences


def parsed_text_to_NP(sentences):
    nps = []
    for sent in sentences:
        tree = NPChunker.parse(sent)
        # print(tree)
        for subtree in tree.subtrees():
            if subtree.label() == 'NP':
                t = subtree
                # t = ' '.join(word for word, tag in t.leaves())
                t = ' '.join(word for word, tag in t.leaves() if (tag == 'NNS') or (tag == 'NN'))
                nps.append(t)
    return nps


def sent_parse(input):
    sentences = prepare_text(input)
    nps = parsed_text_to_NP(sentences)
    return nps


def addExpirationDates(user, expiration):
    for userItem in user:
        curr = userItem['name']
        curr_split = curr.split(' ')
        curr_max = [0, float('inf')]
        exactMatched = False
        for expItem in expiration:

            # exact match
            if curr == expItem['name']:
                userItem['expireIn'] = int(expItem['expireIn'])
                exactMatched = True
                break

            # split into set and find the maximum number of names that also exist in expiration data
            expItem_split = expItem['name'].split(' ')
            # calculate curr overlap score
            overlapped = 0
            for i in curr_split:
                if i in expItem_split:
                    overlapped += 1
            if overlapped > curr_max[0]:
                curr_max = [overlapped, int(expItem['expireIn'])]
            elif overlapped == curr_max[0]:
                curr_max[1] = min(curr_max[1], int(expItem['expireIn']))
        if curr_max[0] > 0:
            userItem['expireIn'] = curr_max[1]
        # if no matching found, set -1 as indicator value
        elif not exactMatched:
            userItem['expireIn'] = -1


def generate_parsed(item, foodList):
    results = []
    if item in foodList:
        results += [item]
    else:
        for w in item.split(' '):
            if w in foodList:
                results += [w]
    return list(set(results))


def addParsedUserData(user, foodList):
    for item in user:
        item['parsed_name'] = generate_parsed(item['name'], foodList)


def calculateOverlapScore(user, recipe_item):
    score = 0
    for userItem in user:
        for i in userItem['parsed_name']:
            if i in recipe_item['ingredients_processed']:
                score += 1
    return score


def calculateExpireScore(user, recipe_item):
    score = 0
    for userItem in user:
        for i in userItem['parsed_name']:
            if i in recipe_item['ingredients_processed']:
                score += (1 / userItem['expireIn']) ** 2
    return score


# due to replicate recipe in recipe data, remove replicate item in top_5
def checkRepeated(recipe_item, curr_list):
    for i in curr_list:
        if recipe_item['title'] == i[0]['title']:
            return True
    return False


def top_5(user, recipe):
    top_5 = []
    min_score = float('inf')
    min_index = 0
    for recipe_item in recipe:
        if checkRepeated(recipe_item, top_5):
            continue
        curr_score = calculateOverlapScore(user, recipe_item) + 10 * calculateExpireScore(user, recipe_item)
        if len(top_5) < 5:
            top_5 += [[recipe_item, curr_score]]
            if curr_score < min_score:
                min_score = curr_score
                min_index = len(top_5) - 1
        else:
            if curr_score > min_score:
                top_5[min_index] = [recipe_item, curr_score]
                new_min = float('inf')
                for i in range(5):
                    if top_5[i][1] < new_min:
                        new_min = top_5[i][1]
                        min_index = i
                min_score = new_min
    return top_5


# return an array of indices which rank the recipes in recipe list in descending order
def recipeRank(user, recipe):
    scoreArray = np.zeros(len(recipe))
    for i in range(len(recipe)):
        curr_score = calculateOverlapScore(user, recipe[i]) + 10 * calculateExpireScore(user, recipe[i])
        scoreArray[i] = curr_score
    return np.flip(np.argsort(scoreArray), axis=0)


# create user data dictionary given a list of scanned food names and return user data
def createUserDict(names):
    user = []
    for name in names:
        user += [{'name': name}]
    addExpirationDates(user, expiration)
    addParsedUserData(user, foodList)
    return user


def processIngredients(ingredient):
    results = []
    parsed = [singularize(e) for e in sent_parse(ingredient)]
    for element in parsed:
        # exact match
        if element in foodList:
            results += [element]
        # split current word and exact match each sub-word
        else:
            for w in element.split(' '):
                if w in foodList:
                    results += [w]
    return list(set(results))


# return overlap percentage for recipeIngredients given userData and recipeIngredients (two lists of strings)
def overlapPercentage(userData, recipeIngredients):
    count = 0
    for i in recipeIngredients:
        if i in userData:
            count += 1
    return count / len(recipeIngredients)


def missingIngredients(recipe, user):
    ingredients = recipe['ingredients']
    results = []
    userSimplified = []
    for u in user:
        userSimplified += u['parsed_name']
    for i in range(len(ingredients)):
        simplified = processIngredients(ingredients[i])
        if len(simplified) == 0:
            results += [ingredients[i]]
        elif overlapPercentage(userSimplified, simplified) < 0.5:
            results += [ingredients[i]]
    return results


def recommend_recipes(lst):
    # ['olive','cheese','mozzarella','flour','pepperoni','sausage','yeast','ham','dough','pineapple','artichoke']
    user = createUserDict(lst)
    ranking = recipeRank(user, recipe)
    # to obtain the titles of the top 5 recommended recipes for the user
    result = []
    for i in range(5):
        result.append(recipe[ranking[i]]['id'])
    return result

