import os
from turtle import title
from flask import Flask, request, jsonify, abort
from werkzeug.exceptions import NotFound
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! Running this funciton will add one
'''
db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods = ['GET'])
def get_drinks():
    try:
        drinks = Drink.query.all()
        short_drinks = [drink.short() for drink in drinks]

        return jsonify({
            'success': True,
            'drinks': short_drinks
        })
    except NotFound:
        print('Drink resource not found in the database.')
        abort(404)
    except Exception as error:
        print(error)
        abort(422)

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail', methods = ['GET'])
@requires_auth(permission='get:drinks-detail')
def get_drinks_detail(payload):
    print(payload)
    try:
        drinks = Drink.query.all()
        long_drinks = [drink.long() for drink in drinks]

        return jsonify({
            'success': True,
            'drinks': long_drinks
        })
    except NotFound:
        print('Drink resource not found in the database.')
        abort(404)
    except Exception as error:
        print(error)
        abort(422)

'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks', methods = ['POST'])
@requires_auth(permission='post:drinks')
def create_drink(payload):
    try:
        body = request.get_json()

        title = body.get('title', None)
        recipe = body.get('recipe', None)
        
        if not title or not recipe: abort(422)

        # I observed that the POST /drinks request from postman collection 
        # sent recipe as a dictionary while the frontend app sends it as a list.
        # Consequently, if a new drink is created using postman, the frontend app
        # results in error when fetching drinks, hence the type check below.
        if isinstance(recipe, list): recipe = recipe
        if isinstance(recipe, dict): recipe = [recipe]

        # Here, SQLAlchemy raise error about field type not being supported so 
        # I had to convert inputs to string which seems to be same as defined in model.py file
        recipe = json.dumps(recipe)

        drink = Drink(title=title, recipe=recipe)
        drink.insert()

        return jsonify({
            'success': True,
            'drinks': [drink.long()]
        })
    except Exception as error:
        print(error)
        abort(422)

'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods = ['PATCH'])
@requires_auth(permission='patch:drinks')
def update_drink(payload, id):
    try:
        body = request.get_json()
        title = body.get('title', None)
        recipe = body.get('recipe', None)
        
        if not id: abort(404)
        
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink is None: abort(404)

        if title: drink.title = title
        if recipe:
            if isinstance(recipe, list): recipe = recipe
            if isinstance(recipe, dict): recipe = [recipe]
        
            drink.recipe = json.dumps(recipe)

        drink.update()

        long_drink = drink.long()

        return jsonify({
            'success': True,
            'drinks': [long_drink]
        })
    except NotFound:
        print('Drink resource not found in the database.')
        abort(404)
    except Exception as error:
        print(error)
        abort(422)

'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>', methods = ['DELETE'])
@requires_auth(permission='delete:drinks')
def delete_drink(payload, id):
    try:
        if not id: abort(404)
        
        drink = Drink.query.filter(Drink.id == id).one_or_none()
        if drink is None: abort(404)

        drink.delete()

        return jsonify({
            'success': True,
            'delete': id
        })
    except NotFound:
        print('Drink resource not found in the database.')
        abort(404)
    except Exception as error:
        print(error)
        abort(422)


# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        'success': False,
        'error': 422,
        'message': 'unprocessable'
    }), 422

'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''

@app.errorhandler(401)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 401,
        'message': 'authorization header not found'
    }), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 404,
        'message': 'resource not found'
    }), 404

'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''
@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        'success': False,
        'error': 403,
        'message': 'authentication/authorization error'
    }), 403

@app.errorhandler(500)
def server_error(error):
    return jsonify({
        'success': False,
        'error': 500,
        'message': 'internal server error'
    }), 500
