
import array
from email import errors
from flask import jsonify, render_template, redirect, session, request, flash
from flask_app import app
from flask_app.models.interest import Interest
from flask_app.models.articles import Article
from flask_app.models.user import User

#SAVED ARTICLES

@app.route('/saveArticle',methods=['POST'])
def save():
    if 'user_id' not in session:
        return redirect('/')
    data = {
        'user_id' : session['user_id'],
        'title' : request.form['title'],
        'url' : request.form['url'],
    }

    Article.save(data)
    flash("Artcile Saved", 'articlesaved')
    return redirect(request.referrer)

@app.route('/unsaveArticle',methods=['POST'])
def unsavedash():
    if 'user_id' not in session:
        return redirect('/')
    data = {
        'title':request.form['title'],
        'url':request.form['url'],
        'user_id': session['user_id']
    }
    Article.unsave(data)
    flash("Artcile Unsaved", 'articleunsaved')
    return redirect(request.referrer)

@app.route('/unsaveArticleprof',methods=['POST'])
def unsave():
    if 'user_id' not in session:
        return redirect('/')
    data = {
        'id': request.form['id']
    }
    Article.unsave_with_id(data)
    flash("Artcile Unsaved", 'articleunsaved')
    return redirect(f"/profile/{session['user_id']}")

@app.route('/deleteInterest',methods=['POST'])
def delete():
    if 'user_id' not in session:
        return redirect('/')
    data = {
        'id': request.form['id']
    }
    Interest.removeInterest(data)
    return jsonify({'path':"/profile/<session['user_id']>"})

@app.route('/setInterests',methods=['POST'])
def set():
    if 'user_id' not in session:
        return redirect('/')
    array = request.form['all'].split(',')
    for topic in array:
        data = {
            'key_word': topic,
            'user_id': session['user_id']
        }
        Interest.addInterest(data)
    return jsonify({'path':'/dashboard'})

@app.route('/addInterest',methods=['POST'])
def add():
    if 'user_id' not in session:
        return redirect('/')
    data = {
        'user_id': session['user_id'],
        'key_word': request.form['key_word']
    }
    Interest.addInterest(data)
    return redirect(request.referrer)

@app.route('/editArticle',methods=['POST'])
def edit():
    if 'user_id' not in session:
        return redirect('/')
    errors = {}
    if len(request.form['title']) < 1:
        errors['title'] = "Name can not be empty!"
    if errors:
        return jsonify({"valid": False, "errors": errors})
    data = {
        'title': request.form['title'],
        'id': request.form['id']
    }
    Article.update(data)
    return jsonify({"valid": True, "path": "/edit/<session['user_id']>"})