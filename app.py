import json
from flask import Flask, request
from matching import match_receipt, match_receipt_advanced
from recommend import recommend_recipes, missingIngredients

app = Flask(__name__)


@app.route('/match', methods=['POST'])
def match():
    lines = eval(request.data)
    for i in range(len(lines)):
        lines[i] = lines[i].upper()
    result = match_receipt_advanced(lines)
    return str(result)


@app.route('/recommend', methods=['POST'])
def recommend_():
    ingredients = eval(request.data)
    result = recommend_recipes(ingredients)
    return json.dumps(result)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
