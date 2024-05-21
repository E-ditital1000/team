Author
Abraham Elvis Bedell

Introduction
Welcome to the Blog Project! This project is a web application designed to allow users to create, read, update, and delete blog posts. Users can also like and comment on posts. The project leverages Django, a powerful web framework for building web applications quickly and with a clean and pragmatic design.

Features
User authentication (sign up, log in, log out)
Create, read, update, and delete blog posts
Like and unlike posts
Comment on posts
View the total number of likes on each post
Dynamic slug generation for blog post URLs
Responsive design
Technologies Used
Django
HTML
CSS
JavaScript (jQuery)
Bootstrap
SQLite (default database for development)
Setup and Installation
Clone the repository:

sh
Copy code
git clone https://github.com/E-ditital1000/team.git
cd blog-project
Create a virtual environment:

sh
Copy code
python -m venv env
source env/bin/activate  # On Windows use `env\Scripts\activate`
Install the dependencies:

sh
Copy code
pip install -r requirements.txt
Apply migrations:

sh
Copy code
python manage.py migrate
Create a superuser:

sh
Copy code
python manage.py createsuperuser
Run the development server:

sh
Copy code
python manage.py runserver
Access the application:

Open your web browser and go to http://localhost:8000

Usage
Sign Up:

Create a new account by signing up with your email and password.

Create a Blog Post:

After logging in, you can create a new blog post by navigating to the "Create Post" section.

Like a Post:

Click the "Like" button to like a post. Click it again to unlike the post.

Comment on a Post:

Scroll to the bottom of a post to add a comment.

Edit or Delete a Post:

You can edit or delete your own posts by navigating to the post and clicking the "Edit" or "Delete" button.

Folder Structure
blog_project/: Root directory of the project.
blog_app/: Contains the main application code.
migrations/: Database migrations.
static/: Static files (CSS, JavaScript).
templates/: HTML templates.
models.py: Database models.
views.py: Application views.
urls.py: URL routing.
media/: Uploaded media files.
requirements.txt: Python dependencies.
Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

License
This project is licensed under the MIT License.