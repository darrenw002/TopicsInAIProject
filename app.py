from flask import Flask, request, jsonify, render_template
from flask_migrate import Migrate 
from config import Config
from models import db, migrate, Resource
import requests
from flask import flash, redirect, url_for
from models import Bookmark
import openai
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from models import User

# Create the Flask Application
app = Flask(__name__)
app.config.from_object(Config)

# Initialize the database and migrations
db.init_app(app)
migrate.init_app(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home Route
@app.route('/')
def index():
    return render_template('index.html')

# Search Route
@app.route('/search')
def search():
    query = request.args.get('query', '')
    category = request.args.get('category', '')

    # Filter by both search query and category, only approved resources
    resources = Resource.query.filter(Resource.approved == True)
    if query:
        resources = resources.filter(Resource.title.ilike(f'%{query}%'))
    if category:
        resources = resources.filter_by(category=category)

    results = resources.all()
    # Render the results in a template
    return render_template('search.html', results=results, query=query, category=category)

@app.route('/github_trending')
def github_trending():
    # Searching for AI-related repos, sorted by stars
    url = "https://api.github.com/search/repositories?q=AI&sort=stars&order=desc"
    response = requests.get(url)
    data = response.json()
    items = data.get('items', [])[:5]  # top 5
    
    # Pass these items to a template
    return render_template('github.html', repos=items)

@app.route('/bookmark/<int:resource_id>', methods=['POST'])
def bookmark_resource(resource_id):
    # Check if user is logged in (we’ll implement login later)
    user_id = 1  # For demo, assume user 1
    
    new_bookmark = Bookmark(user_id=user_id, resource_id=resource_id)
    db.session.add(new_bookmark)
    db.session.commit()
    flash("Resource bookmarked!")
    return redirect(url_for('search'))

@app.route('/dashboard')
def dashboard():
    user_id = 1  # for demonstration
    bookmarked_ids = [b.resource_id for b in Bookmark.query.filter_by(user_id=user_id).all()]
    bookmarked_resources = Resource.query.filter(Resource.id.in_(bookmarked_ids)).all()
    return render_template('dashboard.html', resources=bookmarked_resources)


# AI Chatbot using OpenAI API
@app.route('/chatbot', methods=['GET', 'POST'])
def chatbot():
    bot_response = None
    user_input = None

    if request.method == 'POST':
        user_input = request.form.get('message')

        if user_input:
            openai.api_key = "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"

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": user_input}]
            )

            bot_response = response['choices'][0]['message']['content']

    return render_template('chatbot.html', user_input=user_input, bot_response=bot_response)

@app.route('/submit_resource', methods=['GET','POST'])
def submit_resource():
    if request.method == 'POST':
        title = request.form.get('title')
        category = request.form.get('category')
        link = request.form.get('link')
        desc = request.form.get('description')
        
        resource = Resource(
            title=title,
            category=category,
            link=link,
            description=desc,
            approved=False  # needs admin approval
        )
        db.session.add(resource)
        db.session.commit()
        return "Resource submitted successfully and awaiting approval."
    return render_template('submit_resource.html')

@app.route('/admin/approve/<int:resource_id>', methods=['POST'])
def approve_resource(resource_id):
    # Normally you'd check if user is admin
    resource = Resource.query.get(resource_id)
    if resource:
        resource.approved = True
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin')
def admin_dashboard():
    pending = Resource.query.filter_by(approved=False).all()
    return render_template('admin_dashboard.html', pending=pending)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# Run the app
if __name__ == '__main__':
    app.run(debug=True)
