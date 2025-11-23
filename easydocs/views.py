# D:\Gabriel\Programs\EasyDocs\easydocs\views.py

from django.shortcuts import render, redirect
from users.forms import EmailLoginForm, RegisterForm
from django.contrib.auth import login, logout

def home(request):
    if request.user.is_authenticated:
        return render(request, 'home.html')

    show_register = request.GET.get('register') == '1'
    login_form = EmailLoginForm()
    register_form = RegisterForm()

    if request.method == 'POST':
        if 'login_submit' in request.POST:
            login_form = EmailLoginForm(request.POST)
            if login_form.is_valid():
                login(request, login_form.user)
                return redirect('/')
            show_register = False
        elif 'register_submit' in request.POST:
            register_form = RegisterForm(request.POST)
            show_register = True
            if register_form.is_valid():
                register_form.save()
                return redirect('/')

    context = {
        'login_form': login_form,
        'register_form': register_form,
        'show_register': show_register
    }
    return render(request, 'auth.html', context)

def logout_view(request):
    logout(request)
    return redirect('/')
