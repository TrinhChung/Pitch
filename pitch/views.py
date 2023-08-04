import re
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import gettext
from django.views import generic
from account.mail import send_mail_custom
from pitch.models import Pitch, Order, Comment
from django.db.models import Count
from django.http import Http404, HttpResponseRedirect
from pitch.forms import RentalPitchModelForm, CancelOrderModelForm
import datetime
from django.urls import reverse_lazy, reverse
from django.contrib.auth.decorators import login_required
from pitch.custom_fnc import convert_timedelta
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from account.mail import send_mail_custom
from django.utils.translation import gettext_lazy as _
from project1.settings import HOST
from django.db.models import Q, Avg
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from .forms import SearchForm, CommentForm
from django.shortcuts import redirect, get_object_or_404
from django.db import DatabaseError, transaction


# Create your views here.
def index(request):
    pitches = (
        Pitch.objects.all()
        .annotate(num_orders=Count("order", filter=Q(order__status="c")))
        .order_by("-num_orders")[:3]
        .prefetch_related("image")
    )
    for pitch in pitches:
        if pitch.image.all().exists():
            pitch.banner = pitch.image.all()[0].image.url
        else:
            pitch.banner = "/media/uploads/default-image.jpg"
        pitch.surface = pitch.get_label_grass()
        pitch.size = pitch.get_label_size()
    context = {"pitch_list": pitches}
    return render(request, "index.html", context=context)


@transaction.atomic
@login_required
def pitch_detail(request, pk):
    context = {}
    try:
        pitch = Pitch.objects.get(pk=pk)
    except Pitch.DoesNotExist:
        raise Http404("Pitch does not exist")
    context["pitch"] = pitch
    start_rental_date = datetime.datetime.now() + datetime.timedelta(days=1)
    context["images"] = context["pitch"].image.all()

    comments = Comment.objects.filter(pitch=pitch)
    context["comments"] = comments

    if request.method == "POST":
        form = RentalPitchModelForm(request.POST, pitch=pitch)
        if "submit_comment" in request.POST:
            comment_form = CommentForm(request.POST)
            print(comment_form.is_valid())
            if comment_form.is_valid():
                comment = comment_form.cleaned_data["comment"]
                rating = comment_form.cleaned_data["rating"]
                Comment.objects.create(
                    renter=request.user,
                    pitch=pitch,
                    comment=comment,
                    rating=rating,
                )
                # Redirect to refresh the page after successful comment creation
                return HttpResponseRedirect(request.path_info)
            else:
                # If form is not valid, set the form in context to display the errors
                context["comment_form"] = comment_form
        elif "update_comment" in request.POST:
            comment_pk = request.POST.get("comment_pk")
            comment = get_object_or_404(Comment, pk=comment_pk)
            comment_form = CommentForm(request.POST, instance=comment)
            if comment_form.is_valid():
                comment_form.save()
                # Redirect to refresh the page after successful comment update
                return HttpResponseRedirect(request.path_info)
            else:
                # If form is not valid, set the form in context to display the errors
                context["comment_form"] = comment_form
        else:
            if form.is_valid():
                time_start = form.cleaned_data["time_start"]
                time_end = form.cleaned_data["time_end"]
                voucher = form.cleaned_data["voucher"]
                email = request.user.email
                username = request.user.username

                cost = convert_timedelta(time_end - time_start) * (pitch.price)
                if voucher:
                    cost -= voucher.discount
                order = Order.objects.create(
                    pitch=pitch,
                    time_start=time_start,
                    time_end=time_end,
                    renter=request.user,
                    price=pitch.price,
                    cost=cost,
                    voucher=voucher,
                )

                link = HOST + reverse_lazy("order-detail", kwargs={"pk": order.id})

                send_mail_custom(
                    gettext("Notice to order a pitch from Pitch App"),
                    email,
                    None,
                    "email/notify_order_pitch.html",
                    link=link,
                    username=username,
                    time_start=time_start,
                    time_end=time_end,
                    pitch_title=pitch.title,
                    price=pitch.price,
                    cost=cost,
                )

                return HttpResponseRedirect(
                    reverse_lazy("order-detail", kwargs={"pk": order.id})
                )
            else:
                context["form"] = form

    else:
        context["form"] = RentalPitchModelForm(
            initial={
                "time_start": start_rental_date,
                "time_end": start_rental_date + datetime.timedelta(hours=1),
            },
            pitch=pitch,
        )
        context["update_comment_form"] = CommentForm()
        context["comment_form"] = CommentForm()

    paginator = Paginator(comments, 3)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context["page_obj"] = page_obj
    context["is_paginated"] = True

    return render(request, "pitch/pitch_detail.html", context=context)


class MyOrderedView(LoginRequiredMixin, generic.ListView):
    model = Order
    paginate_by = 10

    def get_queryset(self):
        return Order.objects.filter(renter=self.request.user).order_by("created_date")


@login_required
def order_cancel(request, pk):
    context = {}
    try:
        order = Order.objects.get(pk=pk)
    except Order.DoesNotExist:
        raise Http404("Order does not exist")
    context["order"] = order

    if request.method == "POST":
        form = CancelOrderModelForm(request.POST)
        if form.is_valid():
            email = request.user.email
            username = request.user.username
            link = HOST + reverse_lazy("order-detail", kwargs={"pk": pk})
            order.status = "d"
            order.save()
            send_mail_custom(
                _("Order cancellation notice from Pitch App"),
                email,
                None,
                "email/notify_cancel_order.html",
                link=link,
                username=username,
                time_start=order.time_start,
                time_end=order.time_end,
                pitch_title=order.pitch.title,
                cost=order.cost,
            )
        else:
            context["form"] = form
    else:
        if order.renter.id != request.user.id:
            return render(
                request,
                "error.html",
                {"text_content": _("You can not access this page.")},
                status=302,
            )
        if order.status == "o":
            context["form"] = CancelOrderModelForm(
                initial={
                    "status": "o",
                },
            )

    return render(request, "pitch/order_detail.html", context=context)


def search_view(request):
    form = SearchForm(request.GET)
    query = request.GET.get("q")
    address = request.GET.get("address")
    price = request.GET.get("price")
    size = request.GET.get("size")
    surface = request.GET.get("surface")
    results = []
    # results = Pitch.objects.all().prefetch_related("image")
    ask = [query, address, price, size, surface]
    queryFilter = ""
    if surface:
        queryFilter += "surface = '%s'" % surface
    if size:
        if queryFilter != "":
            queryFilter += " and "
        queryFilter += "size = '%s'" % size
    if price:
        if queryFilter != "":
            queryFilter += " and "
        queryFilter += " price <= %s" % price
    if address:
        if queryFilter != "":
            queryFilter += " and "
        queryFilter += "address = '%s'" % address
    if query:
        if queryFilter != "":
            queryFilter += " and "
        queryFilter += "MATCH(title,description) AGAINST('%s') > 0.01 " % query

    if len(queryFilter) > 0:
        queryFilter = "SELECT * FROM pitches WHERE " + queryFilter
    else:
        queryFilter = "SELECT * FROM pitches "

    results = Pitch.objects.raw(queryFilter).prefetch_related("image")

    for pitch in results:
        if pitch.image.all().exists():
            pitch.banner = pitch.image.all()[0].image.url
        else:
            pitch.banner = "/media/uploads/default-image.jpg"
        pitch.surface = pitch.get_label_grass()
        pitch.size = pitch.get_label_size()
    paginator = Paginator(results, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "query": ask,
        "form": form,
        "page_obj": page_obj,
        "is_paginated": True,
    }

    return render(request, "pitch/pitch_search.html", context)


def create_comment(request, pk):
    pitch = get_object_or_404(Pitch, pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.pitch = pitch
            comment.renter = request.user
            comment.save()
            return redirect("pitch-detail", pk=pk)
    else:
        form = CommentForm()
    return render(request, "pitch/create_comment.html", {"form": form})
