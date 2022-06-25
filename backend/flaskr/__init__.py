import os
import random

from flask import Flask, abort, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import null
from models import Category, Question, setup_db

QUESTIONS_PER_PAGE = 10

def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    curr_questions = questions[start:end]

    return curr_questions

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    setup_db(app)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={r'*' : {'origins': '*'}})
    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type, Authorization"
        )
        response.headers.add(
            "Access-Control-Allow-Headers", "GET, POST, PATCH, DELETE, OPTION"
        )
        return response


    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    @app.route('/categories')
    def fetch_categories():
        cats = {}
        categories = Category.query.all()
        for cat in categories:
            cats[str(cat.id)] = cat.type

        if cats is None:
            abort(404)

        return jsonify({
            'success': True,
            'categories': cats,
        })


    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """
    @app.route('/questions')
    def fetch_questions():
        selection = Question.query.order_by(Question.id).all()

        curr_questions = paginate_questions(request, selection)
        categories = Category.query.all()

        if len(curr_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': curr_questions,
            'totalQuestions': len(selection),
            'categories': [category.type for category in categories],
            'currentCategory': None
        })
    

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.
    

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.get(question_id)
            if question is None:
                abort(422)
            question.delete()
            selection = Question.query.order_by(Question.id).all()
            currentQuestions = paginate_questions(request, selection)

            return jsonify(
                {
                    "success": True,
                    "deleted": question_id,
                    "questions": currentQuestions,
                    "total_books": len(Question.query.all()),
                }
            )
            
        except:
            abort(422)

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    @app.route('/questions', methods=['POST'])
    def create_questions():
        body = request.get_json()

        if not ('question' in body and 'answer' in body and 'difficulty' in body and 'category' in body):
            abort(422)

        new_question = body.get('question')
        new_answer = body.get('answer')
        new_difficulty = body.get('difficulty')
        new_category = body.get('category')

        try:
            question = Question(question=new_question, answer=new_answer, difficulty=new_difficulty, category=new_category)
            question.insert()

            selection = Question.query.order_by(Question.id).all()
            currQuestion = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'created': question.id,
                'questions': currQuestion,
                "totalQuestions": len(Question.query.all())
            })
        except:
            abort(422)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    @app.route('/questions/search', methods=['POST'])
    def search_questions():
        body = request.get_json()

        search = body.get('searchTerm', None)
        if search is None:
            abort(404)

        selection = Question.query.order_by(Question.id).filter(Question.question.ilike("%{}%".format(search))).all()

        currQuestion = paginate_questions(request, selection)

        return jsonify({
            'success': True,
            'questions': currQuestion,
            'current_category': None,
            "total_questions": len(selection)
        })

    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    @app.route('/categories/<int:category_id>/questions')
    def specific_question(category_id):
        selection = Question.query.filter(Question.category == str(category_id + 1)).all()

        if len(selection) == 0:
            abort(404)
        currQuestion = paginate_questions(request, selection)
        
        return jsonify({
            'success': True,
            'questions': currQuestion,
            'total_questions': len(currQuestion),
            'current_category': category_id + 1
        })

    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        try:
            body = request.get_json()
            if not ('quiz_category' in body and 'previous_questions' in body):
                abort(422)
            category = body.get('quiz_category')
            previous_questions = body.get('previous_questions')

            if category['type'] == 'click':
                new_question = Question.query.filter(
                Question.id.notin_((previous_questions))
                ).all()
            else:
                new_question = Question.query.filter_by(
                category=category['id']
                ).filter(Question.id.notin_((previous_questions))).all()

            return jsonify({
                'success': True,
                'question': random.choice(new_question).format() if new_question else None,
            })
        
        except:
            abort(422)
        



    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
        }), 400

    return app

