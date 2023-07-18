from django.shortcuts import render


# Create your views here.
def index(request):
    """View function for home page of site."""
    # Generate counts of some of the main objects

    context = {"var": "hello"}

    return render(request, "index.html", context=context)
