from django.contrib.auth.models import User
from django.shortcuts import render
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
import random
from django.core.mail import send_mail
from PROJECTNAME.settings import EMAIL_HOST_USER
from cryptography.fernet import Fernet
from mechanize import Browser
import favicon
from .models import Password

br = Browser()  
br.set_handle_robots(False)
fernet = Fernet(settings.KEY)

def home(request):
    passwords = []
    if request.method == "POST":
        if "signup-form" in request.POST:
            username = request.POST.get("username")
            email = request.POST.get("email")
            password = request.POST.get("password")
            password2 = request.POST.get("password2")

            # Check if passwords match
            if password != password2:
                msg = "Please re-check you are using the same password!!"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)

            # Check if username already exists
            elif User.objects.filter(username=username).exists():
                msg = f"{username} already exists!!"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)

            # Check if email already exists
            elif User.objects.filter(email=email).exists():
                msg = f"{email} already exists!!"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)

            # Create new user and send OTP email
            else:
                new_user = User.objects.create_user(username, email, password)
                login(request, new_user)
                code = str(random.randint(100000, 999999))
                send_mail(
                    "OTP Verification",
                    f"Your OTP is {code}.",
                    EMAIL_HOST_USER,
                    [new_user.email],
                    fail_silently=False,
                )
                msg = f"{username}. Thanks for Subscribing..! An OTP has been sent to your email."
                messages.success(request, msg)
                return HttpResponseRedirect(request.path)

        elif "logout" in request.POST:
            msg = f"{request.user}. You logged Out..!"
            logout(request)
            messages.success(request, msg)
            return HttpResponseRedirect(request.path)

        elif 'login-form' in request.POST:
            username = request.POST.get("username")
            password = request.POST.get("password")
            new_login = authenticate(request, username=username, password=password)
            if new_login is None:
                msg = f"Login Failed!!! Try Again...."
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            else:
                code = str(random.randint(100000, 999999))
                global global_code
                global_code = code
                send_mail(
                    "OTP Verification",
                    f"Your OTP is {code}.",
                    EMAIL_HOST_USER,
                    [new_login.email],
                    fail_silently=False,
                )
                return render(request, "home.html" , {
                    "code":code,
                     "user":new_login,
                       })
                msg = f"{new_login.username}. An OTP has been sent to your email."
                messages.success(request, msg)
                return HttpResponseRedirect(request.path)

        elif "confirm" in request.POST:
            input_code = request.POST.get("code")
            username = request.POST.get("user")
            if input_code != global_code:
                msg = f"{input_code} is wrong!"
                messages.error(request, msg)
                return HttpResponseRedirect(request.path)
            else:
                try:
                    user = User.objects.get(username=username)
                    login(request, user)
                    msg = f"{request.user} Welcome Again!"
                    messages.success(request, msg)
                    return HttpResponseRedirect(request.path)
                except User.DoesNotExist:
                    msg = f"User {username} does not exist!"
                    messages.error(request, msg)
                    return HttpResponseRedirect(request.path)
        elif "add-password" in request.POST:
            url = request.POST.get("url")
            email = request.POST.get("email")
            password = request.POST.get("password")
            #ecrypt data
            encrypted_email = fernet.encrypt(email.encode())
            encrypted_password = fernet.encrypt(password.encode())
            #get title of the website
            try:
                br.open(url)
                title = br.title()
            except:
                title = url
            #get the logo's URL
            try:
                icon = favicon.get(url)[0].url
            except:
                icon = "https://cdn-icons-png.flaticon.com/128/1006/1006771.png"
            #Save data in database
            new_password = Password.objects.create(
                user=request.user,
                name=title,
                logo=icon,
                email=encrypted_email.decode(),
                password=encrypted_password.decode(),
            )
            msg = f"{title} added successfully."
            messages.success(request, msg)
            return HttpResponseRedirect(request.path)

        elif "delete" in request.POST:
            to_delete = request.POST.get("password-id")
            msg = f"{Password.objects.get(id=to_delete).name} deleted."
            Password.objects.get(id=to_delete).delete()
            messages.success(request, msg)
            return HttpResponseRedirect(request.path)
            
    context = {}
    if request.user.is_authenticated:
        passwords = Password.objects.all().filter(user=request.user)
        for password in passwords:
            password.email = fernet.decrypt(password.email.encode()).decode()
            password.password = fernet.decrypt(password.password.encode()).decode()
        context = {
            "passwords":passwords,
        }

    return render(request, "home.html", {
        "passwords":passwords,
    })
