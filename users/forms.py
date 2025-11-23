from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class RegisterForm(UserCreationForm):
    email = forms.EmailField(label='E-mail', required=True)

    class Meta:
        model = CustomUser
        fields = ("email", "password1", "password2")  

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class EmailLoginForm(forms.Form):
    email = forms.EmailField(label='E-mail')
    password = forms.CharField(label='Senha', widget=forms.PasswordInput)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        user = CustomUser.objects.filter(email=email).first()
        if user is None:
            raise forms.ValidationError("E-mail não cadastrado.")
        if not user.check_password(password):
            raise forms.ValidationError("Senha incorreta.")
        self.user = user
        return self.cleaned_data
