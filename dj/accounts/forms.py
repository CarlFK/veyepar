# forms.py

from django import forms
# from django.contrib.admin import widgets                                       
class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

