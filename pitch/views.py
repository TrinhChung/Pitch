from django.shortcuts import render
from django.views import generic
from pitch.models import Pitch
# Create your views here.
def index(request):
    """View function for home page of site."""
    # Generate counts of some of the main objects

    context = {"var": "hello"}

    return render(request, "index.html", context=context)

class PitchListView(generic.ListView):
    model = Pitch
    # your own name for the list as a template variable
    paginate_by = 10

    def get_queryset(self):
        return Pitch.objects.all()

    def get_context_data(self, **kwargs):
        context = super(PitchListView, self).get_context_data(**kwargs)
        return context
