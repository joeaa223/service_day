from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render,get_object_or_404,redirect
from .models import NGO

def is_admin(user):
    return user.is_staff

@user_passes_test(is_admin)
def listing(request):
    ngos = NGO.objects.all().order_by("name")
    return render(request, "ngo/listing.html",{"ngos":ngos})

@user_passes_test(is_admin)
def register(request):
    if request.method == "POST":
        body = request.POST

        ngo = NGO.objects.create(
            name=body.get("ngo_name"),
            registration_number=body.get("reg_num"),
            contact_name=body.get("pic_name"),
            contact_email=body.get("pic_email"),
            contact_phone=body.get("pic_hp"),
            address=body.get("address"),
            postcode=body.get("postcode"),
            city=body.get("city"),
            state=body.get("state"),
            description=body.get("description")
        )
        return redirect("manage_ngo",ngo_id=ngo.id)  

    return render(request, "ngo/register.html")

@user_passes_test(is_admin)
def manage(request,ngo_id):
    ngo = get_object_or_404(NGO, id=ngo_id)

    if request.method == "POST":
        ngo.name = request.POST.get("name")
        ngo.registration_number = request.POST.get("registration_number")
        ngo.description = request.POST.get("description")
        ngo.contact_name = request.POST.get("contact_name")
        ngo.contact_email = request.POST.get("contact_email")
        ngo.contact_phone = request.POST.get("contact_phone")
        ngo.address = request.POST.get("address")
        ngo.postcode = request.POST.get("postcode")
        ngo.city = request.POST.get("city")
        ngo.state = request.POST.get("state")
        ngo.is_active = request.POST.get("is_active") == "True"
        ngo.save()

    return render(request, "ngo/manage.html", {"ngo": ngo})