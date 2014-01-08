from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from rango.models import Category
from rango.models import Page
from rango.models import UserProfile
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rango.bing_search import run_query
from django.contrib.auth.models import User
from datetime import datetime
from django.shortcuts import redirect

def index(request):
    # Obtain the context from the HTTP request.
    context = RequestContext(request)
    category_list = Category.objects.order_by('-name')[:5]
    context_dict = {'categories': category_list}

    for category in category_list:
        category.url = encode_url(category.name)
        
    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list
    # Render the response and send it back!
    
    page_list = Page.objects.order_by('-views')[:5]
    context_dict['pages'] = page_list
    
    response = render_to_response('rango/index.html', context_dict, context)
    
    visits = int(request.COOKIES.get('visits','0'))
    
    if request.COOKIES.has_key('last_visit'):
        last_visit = request.COOKIES['last_visit']
        last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")
        
        if (datetime.now() - last_visit_time).days > 0:
            response.set_cookie('visit', visits+1)
            response.set_cookie('last_visit', datetime.now())
    else:
        response.set_cookie('last_visit', datetime.now())

        
    return response

    
    
    return render_to_response('rango/index.html', context_dict, context)
    
def decode_url(str):
    return str.replace('_',' ')

def encode_url(str):
    return str.replace(' ','_')

def category(request, category_name_url):
    context = RequestContext(request)
    cat_list = get_category_list()
    category_name = decode_url(category_name_url)
    
    context_dict = {'category_name': category_name, 'category_name_url':category_name_url, 'cat_list' : cat_list}


    try:
        category = Category.objects.get(name=category_name)
        context_dict['category'] = category
        pages = Page.objects.filter(category=category)
        context_dict['pages'] = pages

    except Category.DoesNotExist:
        pass
    
    if request.method == 'POST':
        query = request.POST.get('query')         
        if query:
            query = query.strip()
            result_list = run_query(query)              
            context_dict['result_list'] = result_list
    
    
    return render_to_response('rango/category.html', context_dict, context)

@login_required    
def like_category(request):
    context = RequestContext(request)
    cat_id = None
    if request.method == 'GET':
        cat_id = request.GET['category_id']
    likes = 0
    if cat_id:
        category = Category.objects.get(id=int(cat_id))
        if category:
                likes = category.likes + 1
                category.likes = likes
                category.save()
    return HttpResponse(likes)  
    
def get_category_list(max_results=0, starts_with=''):
    cat_list = []
    
    if starts_with:
        cat_list = Category.objects.filter(name__startswith=starts_with)
    else:
        cat_list = Category.objects.all()
        

    if max_results > 0:
        if len(cat_list) > max_results:
            cat_list = cat_list[:max_results]
            
    for cat in cat_list:
        cat.url = encode_url(cat.name)
    
    return cat_list

def suggest_category(request):
        context = RequestContext(request)
        cat_list = []
        starts_with = ''
        if request.method == 'GET':
                starts_with = request.GET['suggestion']
        else:
                starts_with = request.POST['suggestion']

        cat_list = get_category_list(8, starts_with)

        return render_to_response('rango/category_list.html', {'cat_list': cat_list }, context)
         
    
def add_category(request):
    context = RequestContext(request)
    
    cat_list = get_category_list()

    context_dict = {}

    context_dict['cat_list'] = cat_list
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        
        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            print form.errors
    else:
        form = CategoryForm()
    
    context_dict['form'] = form
    return render_to_response('rango/add_category.html', context_dict, context)


def add_page(request, category_name_url):
    context = RequestContext(request)

    cat_list = get_category_list()

    context_dict = {}

    context_dict['cat_list'] = cat_list
    
    category_name = decode_url(category_name_url)
    
    if request.method == 'POST':
        form = PageForm(request.POST)

        if form.is_valid():
            # This time we cannot commit straight away.
            # Not all fields are automatically populated!
            page = form.save(commit=False)

            # Retrieve the associated Category object so we can add it.
            cat = Category.objects.get(name=category_name)
            page.category = cat

            # Also, create a default value for the number of views.
            page.views = 0

            # With this, we can then save our new model instance.
            page.save()

            # Now that the page is saved, display the category instead.
            return category(request, category_name_url)
        else:
            print form.errors
    else:
        form = PageForm()
    
    context_dict['category_name_url'] = category_name_url
    context_dict['category_name'] = category_name
    context_dict['form'] = form

    return render_to_response( 'rango/add_page.html',
            context_dict,
             context)

def about(request):
    # Request the context.
    context = RequestContext(request)
    context_dict = {}
    
    cat_list = get_category_list()

    context_dict['cat_list'] = cat_list
    # If the visits session varible exists, take it and use it.
    # If it doesn't, we haven't visited the site so set the count to zero.
    count = request.session.get('visits',0)

    context_dict['visit_count'] = count

    # Return and render the response, ensuring the count is passed to the template engine.
    return render_to_response('rango/about.html', context_dict , context)
    

def register(request):
    context = RequestContext(request)
    cat_list = get_category_list()
    context_dict = {}
    context_dict['cat_list'] = cat_list
    
    registered = False
    
    if request.method == 'POST':
        # Grab raw form data - making use of both FormModels.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            
            user.set_password(user.password)
            user.save()
        
            profile = profile_form.save(commit=False)
            profile.user = user

            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            profile.save()

            registered = True

        else:
            print user_form.errors, profile_form.errors

    else:
        user_form = UserForm()
        profile_form = UserProfileForm()


    context_dict['user_form'] = user_form
    context_dict['profile_form'] = profile_form
    context_dict['registered'] = registered

    return render_to_response(
        'rango/register.html',
        context_dict,
        context)

def user_login(request):
    # Obtain our request's context.
    context = RequestContext(request)
    context_dict = {}
    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list
    
    # If HTTP POST, pull out form data and process it.
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        # Attempt to log the user in with the supplied credentials.
        # A User object is returned if correct - None if not.
        user = authenticate(username=username, password=password)

        # A valid user logged in?
        if user is not None:
            # Check if the account is active (can be used).
            # If so, log the user in and redirect them to the homepage.
            if user.is_active:
                login(request, user)
                return HttpResponseRedirect('/rango/')
            # The account is inactive; tell by adding variable to the template context.
            else:
                context_dict['disabled_account'] = True
                return render_to_response('rango/login.html', context_dict, context)
        # Invalid login details supplied!
        else:
            print "Invalid login details: {0}, {1}".format(username, password)
            context_dict['bad_details'] = True
            return render_to_response('rango/login.html', context_dict, context)

    # Not a HTTP POST - most likely a HTTP GET. In this case, we render the login form for the user.
    else:
        return render_to_response('rango/login.html', context_dict, context)

@login_required    
def restricted (request):
    return HttpResponse("Since you're logged in, you can see this text")

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/rango/')	

def search(request):
        context = RequestContext(request)
        
        cat_list = get_category_list()
        context_dict = {}
        context_dict['cat_list'] = cat_list
        
        result_list = []
        
        if request.method == 'POST':
            query = request.POST['query'].strip()
            
            if query:
                result_list = run_query(query)
                
        context_dict['result_list'] = result_list
                
        return render_to_response('rango/search.html', context_dict, context)

@login_required        
def profile(request):
    context = RequestContext(request)
    context_dict = {}
    cat_list = get_category_list()
    context_dict['cat_list'] = cat_list
    
    u = User.objects.get(username=request.user)
    
    try:
        up = UserProfile.objects.get(user=u)
    except:
        up = None
        
    context_dict['user'] = u
    context_dict['userprofile'] = up
    return render_to_response('rango/profile.html', context_dict , context)

def track_url(request):
    context = RequestContext(request)
    page_id = None
    url = '/rango/'
    if request.method =='GET':
        if 'page_id' in request.GET:
            page_id = request.GET['page_id']
            try:
                page = Page.objects.get(id=page_id)
                page.views += 1
                page.save()
                url = page.url
            except:
                pass
    return redirect(url)

@login_required
def auto_add_page(request):
    context = RequestContext(request)
    cat_id = None
    url = None
    title = None
    context_dict = {}
    if request.method == 'GET':
        cat_id = request.GET['category_id']
        url    = request.GET['url']
        title  = request.GET['title']
        if cat_id:
            category = Category.objects.get(id=int(cat_id))
            p = Page.objects.get_or_create(category=category, title=title, url=url)
            
            pages = Page.objects.filter(category=category).order_by('-views')
            
            context_dict['pages'] = pages
    return render_to_response('rango/page_list.html', context_dict, context)