from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rango.bing_search import run_query

def index(request):
    # Obtain the context from the HTTP request.
    context = RequestContext(request)
    category_list = Category.objects.order_by('-name')[:5]
    context_dict = {'categories': category_list}

    for category in category_list:
        category.url = encode_url(category.name)
    # Render the response and send it back!
	
	cat_list = get_category_list()
	context_dict['cat_list'] = cat_list
	
    return render_to_response('rango/index.html', context_dict, context)

def decode_url(str):
    return str.replace('_',' ')

def encode_url(str):
    return str.replace(' ','_')

def category(request, category_name_url):
	context = RequestContext(request)
	
	category_name = decode_url(category_name_url)
	
	context_dict = {'category_name': category_name, 'category_name_url' : category_name_url}
	
	cat_list = get_category_list()
	context_dict['cat_list'] = cat_list
	
	try:
		category = Category.objects.get(name=category_name)
		pages = Page.objects.filter(category=category)
		context_dict['pages'] = pages
        
		context_dict['category'] = category
	except Category.DoesNotExist:
		pass
    
	return render_to_response('rango/category.html', context_dict, context)

def get_category_list(max_results=0, starts_with=''):
	cat_list = []
	
	if starts_with:
		cat_list = Category.objects.filter(name__startswith=starts_with)
	else:
		cat_list = Category.objects.all()
		
	for cat in cat_list:
		cat.url = encode_url(cat.name)
	
	return cat_list
	
def add_category(request):
    context = RequestContext(request)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        
        if form.is_valid():
            form.save(commit=True)
            return index(request)
        else:
            print form.errors
    else:
        form = CategoryForm()
    
    return render_to_response('rango/add_category.html', {'form': form}, context)

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
    # Request the context.
    context = RequestContext(request)
    cat_list = get_category_list()
    context_dict = {}
    context_dict['cat_list'] = cat_list
    
    registered = False

    # If HTTP POST, we wish to process form data and create an account.
    if request.method == 'POST':
        # Grab raw form data - making use of both FormModels.
        user_form = UserForm(data=request.POST)
        profile_form = UserProfileForm(data=request.POST)

        # Two valid forms?
        if user_form.is_valid() and profile_form.is_valid():
            # Save the user's form data. That one is easy.
            user = user_form.save()

            # Now a user account exists, we hash the password with the set_password() method.
            # Then we can update the account with .save().
            user.set_password(user.password)
            user.save()

            # Now we can sort out the UserProfile instance.
            # We'll be setting values for the instance ourselves, so commit=False prevents Django from saving the instance automatically.
            profile = profile_form.save(commit=False)
            profile.user = user

            # Profile picture supplied? If so, we put it in the new UserProfile.
            if 'picture' in request.FILES:
                profile.picture = request.FILES['picture']

            # Now we save the model instance!
            profile.save()

            # We can say registration was successful.
            registered = True

        # Invalid form(s) - just print errors to the terminal.
        else:
            print user_form.errors, profile_form.errors

    # Not a HTTP POST, so we render the two ModelForms to allow a user to input their data.
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
	
	
	
	