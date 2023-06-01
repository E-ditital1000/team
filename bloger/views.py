from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User, auth
from django.contrib import messages
from .models import Blog_Post
from .forms import CommentForm
from .forms import BlogPostForm
# Create your views here.

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']

        if password == password2:
            if User.objects.filter(username=username).exists():
                messages.info(request, 'Username Already used')
                return redirect('register')
            elif User.objects.filter(email=email).exists():
                messages.info(request, 'email Already used')
                return redirect('register')
            else:
                user = User.objects.create_user(username=username, email=email, password=password)
                user.save();
                return redirect('login')
        else:
            messages.info(request, 'Password Not The Same')
            return redirect('register')
    else:
        return render(request, 'register.html')

from cloudinary_storage.forms import CloudinaryFileField

def create_blog_post(request):
    if request.method == 'POST':
        form = BlogPostForm(request.POST, request.FILES)
        if form.is_valid():
            blog_post = form.save(commit=False)
            blog_post.writer = request.user
            image_field = form.cleaned_data['image']
            
            # Check if the image field contains a Cloudinary file
            if isinstance(image_field, CloudinaryFileField):
                # Assign the Cloudinary file URL to the image field
                blog_post.image = image_field.url
            
            blog_post.save()
            return redirect('blog_detail', slug=blog_post.slug)
    else:
        form = BlogPostForm()
    return render(request, 'create_blog_post.html', {'form': form})



def search_results(request):
    query = request.GET.get('query')
    results = Blog_Post.objects.filter(title__icontains=query)
    return render(request, 'search_results.html', {'query': query, 'results': results})

def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
         
        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('index')
        else:
            messages.info(request, 'Credentials Invalid')
            return redirect('login')

    else:
        return render(request, 'login.html')

 
def logout(request):
    auth.logout(request)
    return redirect('index')

template_name = 'register.html'
def index(request):
    posts = Blog_Post.objects.all()
    return render(request, 'index.html',{'posts' : posts})

def blog_detail_view(request, slug):
    post = Blog_Post.objects.get(slug=slug)
    comments = post.comments.all()
    new_comment = None

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.post = post
            new_comment.save()
            return redirect('blog_detail', slug=slug)
    else:
        form = CommentForm()

    return render(request, 'blog_detail.html', {'post': post, 'comments': comments, 'form': form})