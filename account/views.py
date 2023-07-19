from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render
from .forms import RegisterForm
from django.urls import reverse_lazy, reverse
from django.shortcuts import render
from django.views import generic
from django.contrib.auth.models import User
from django.core.mail import BadHeaderError, send_mail
from django.http import HttpResponse, HttpResponseRedirect
import uuid
from .models import EmailVerify


def sign_up(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        print("Register")
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            email = form.cleaned_data["email"]
            token = uuid.uuid4()

            link = reverse("verify-email", kwargs={"token": token})
            try:
                send_mail(
                    "Subject",
                    '<a href="%s">Click here</a>' % link,
                    "chungtrinh2k2@gmail.com",
                    [email],
                )
            except BadHeaderError:
                return HttpResponse("Invalid header found.")

            user = User.objects.create_user(username, email, password)
            user.is_active = False
            user.save()

            EmailVerify.objects.create(user=user, token=token)

            return HttpResponseRedirect(reverse("index"))

    else:
        form = RegisterForm()
    return render(request, "registration/signup.html", {"form": form})


def verify_email(request, token):
    if EmailVerify.objects.filter(token=token).exists():
        userVerify = EmailVerify.objects.get(token=token)
        user = userVerify.user
        print(user.email)
        print(user.username)
        user.is_active = True
        user.save()
    else:
        return HttpResponse("Token da duoc su dung hoac khong ton tai")

    context = {"var": "hello"}
    return render(request, "registration/verify-email.html", context=context)
