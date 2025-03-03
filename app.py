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
from flask import abort


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

# Register route

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Get form data
        username = request.form['username']
        password = request.form['password']
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Username already taken"
        
        # Create the new user (plain-text password)
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()

        # Optional: Log the user in immediately
        login_user(new_user)
        
        return redirect(url_for('login'))
    
    # If GET, just show the register form
    return render_template('register.html')

# Search Route
@app.route('/search')
@login_required
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
@login_required
def github_trending():
    # Searching for AI-related repos, sorted by stars
    url = "https://api.github.com/search/repositories?q=AI&sort=stars&order=desc"
    response = requests.get(url)
    data = response.json()
    items = data.get('items', [])[:20]  # top 20
    
    # Pass these items to a template
    return render_template('github.html', repos=items)

@app.route('/bookmark/<int:resource_id>', methods=['POST'])
@login_required
def bookmark_resource(resource_id):
    # Check if user is logged in (we’ll implement login later)
    user_id = 1  # For demo, assume user 1
    
    new_bookmark = Bookmark(user_id=user_id, resource_id=resource_id)
    db.session.add(new_bookmark)
    db.session.commit()
    flash("Resource bookmarked!")
    return redirect(url_for('search'))

@app.route('/toggle_bookmark/<int:resource_id>', methods=['POST'])
@login_required
def toggle_bookmark(resource_id):
    user_id = current_user.id
    data = request.get_json()
    is_bookmarked = data.get('bookmarked')

    if is_bookmarked:
        # Add bookmark
        if not Bookmark.query.filter_by(user_id=user_id, resource_id=resource_id).first():
            db.session.add(Bookmark(user_id=user_id, resource_id=resource_id))
    else:
        # Remove bookmark
        Bookmark.query.filter_by(user_id=user_id, resource_id=resource_id).delete()

    db.session.commit()

    return jsonify({'success': True, 'bookmarked': is_bookmarked})


@app.route('/dashboard')
@login_required
def dashboard():
    #user_id = 1  # for demonstration, in real, use,  user_id = session.get('user_id')
    user_id = current_user.id
    resources = Resource.query.filter(Resource.approved == True).order_by(Resource.category, Resource.title).all()
    #bookmarked_ids = [b.resource_id for b in Bookmark.query.filter_by(user_id=user_id).all()]
    #bookmarked_resources = Resource.query.filter(Resource.id.in_(bookmarked_ids)).all()
    if user_id:
        bookmarked_ids = [b.resource_id for b in Bookmark.query.filter_by(user_id=user_id).all()]
    else:
        bookmarked_ids = []  # No user logged in
    return render_template('dashboard.html', resources=resources, bookmarked_ids=bookmarked_ids)
    #return render_template('dashboard.html', resources=bookmarked_resources)


@app.route('/chatbot', methods=['GET', 'POST'])
@login_required#
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
@login_required
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
@login_required
def approve_resource(resource_id):
    if current_user.username != 'admin':  # Ensure only admin can approve
        abort(403)  # Forbidden error if non-admin tries

    resource = Resource.query.get(resource_id)
    if resource:
        resource.approved = True
        db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.username != 'admin':  # Restrict access
        abort(403)  # Forbidden error if non-admin tries

    pending = Resource.query.filter_by(approved=False).all()
    return render_template('admin_dashboard.html', pending=pending)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:  # plain-text check
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