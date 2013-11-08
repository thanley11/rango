from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from rango.models import Category
from rango.models import Page
from rango.forms import CategoryForm
from rango.forms import PageForm

def index(request):
    # Obtain the context from the HTTP request.
    context = RequestContext(request)

    # Query the database for a list of ALL categories currently stored.
    # Order the categories by no. likes in descending order.
    # Retrieve the top 5 only - or all if less than 5.
    # Place the list in our context_dict dictionary which will be passed to the template engine.
    category_list = Category.objects.order_by('-name')[:5]
    context_dict = {'categories': category_list}

    for category in category_list:
        category.url = category.name.replace(' ','_')
    # Render the response and send it back!
    return render_to_response('rango/index.html', context_dict, context)

def category(request, category_name_url):
    context = RequestContext(request)
    
    # Change underscores in the category name to spaces.
    # URLs don't handle spaces well, so we encode them as underscores.
    # We can then simply replace the underscores with spaces again to get the name.
    
    category_name = category_name_url.replace('_',' ')

    # Create a context dictionary which we can pass to the template rendering engine.
    # We start by containing the name of the category passed by the user.

    context_dict = {'category_name': category_name}
    
    try:
        # Can we find a category with the given name?
        # If we can't, the .get() method raises a DoesNotExist exception.
        # So the .get() method returns one model instance or raises an exception.
        category = Category.objects.get(name=category_name)
        
        # Retrieve all of the associated pages.
        # Note that filter returns >= 1 model instance.
        pages = Page.objects.filter(category=category)
        
        # Adds our results list to the template context under name pages.
        context_dict['pages'] = pages
        
        context_dict['category'] = category
    except Category.DoesNotExist:
        # We get here if we didn't find the specified category.
        # Don't do anything - the template displays the "no category" message for us.
        pass
    
    return render_to_response('rango/category.html', context_dict, context)

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

def add_page(request):
    context = RequestContext(request)
    
    if request.method == 'POST':
        form = PageForm(request.POST)
        
        if form.is_valid():
            page = form.save(commit=False)
            cat = Category.objects.get(name=category_name)
            page.category = cat
            
            page.views = 0
            
            page. save()
            
            return category(request, category_name_url)
        else:
            print form.errors
    else:
        form = PageForm()
        
    return render_to_response('/rango/add_page.html',
            {'category_name_url': category_name_url,
             'category_name': category_name, 'form': form},
            context)
            
            
            
           
            