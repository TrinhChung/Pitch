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
from account.mail import send_mail_custom
from project1.settings import HOST


def sign_up(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            email = form.cleaned_data["email"]
            token = uuid.uuid4()

            link = HOST + reverse("verify-email", kwargs={"token": token})

            send_mail_custom(
                "Verify your email from Pitch App",
                email,
                None,
                "email/verify_email_signup.html",
                link=link,
                username=username,
            )

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
        user.is_active = True
        user.save()
    else:
        return HttpResponse("Token da duoc su dung hoac khong ton tai")

    context = {"var": "hello"}
    return render(request, "registration/verify-email.html", context=context)
