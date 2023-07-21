from django.shortcuts import render
from django.views import generic
from pitch.models import Pitch


def index(request):
    context = {"var": "hello"}

    return render(request, "index.html", context=context)

class PitchListView(generic.ListView):
    model = Pitch
    paginate_by = 10

    def get_queryset(self):
        return Pitch.objects.filter(image__isnull=False)
    def get_context_data(self, **kwargs):
        context = super(PitchListView, self).get_context_data(**kwargs)
        pitches = Pitch.objects.all()
        for pitch in pitches:
            if pitch.image.all().exists():
                pitch.banner = pitch.image.all()[0].image.url
            else: 
                pitch.banner = "/uploads/uploads/default-image.jpg"
            pitch.surface = pitch.get_label_grass()
            pitch.size = pitch.get_label_size()
        context['pitch_list'] = pitches
        return context
