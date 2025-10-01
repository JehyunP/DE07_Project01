from django.http import HttpResponse, HttpResponseRedirect
from .models import *
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.db.models import F
from django.views import generic
from django.urls import reverse_lazy
from django.contrib.auth.forms import UserCreationForm

# Create your views here.
def index(request):
    program_lists = Program.objects.all()[:5]
    context = {'Program' : program_lists}

    return render(request, 'backends/index.html', context)