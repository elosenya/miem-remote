from django import forms


class LoginForm(forms.Form):
    email = forms.CharField(
        widget=forms.TextInput(attrs={
            'type': 'email',
            'id': 'inputEmail',
            'class': 'form-control',
            'placeholder': 'Email',
            'required': '',
            'autofocus': ''
        }))
    password = forms.CharField(
        widget=forms.TextInput(attrs={
            'type': 'password',
            'id': 'inputPassword',
            'class': 'form-control',
            'placeholder': 'Пароль',
            'required': ''
        }))
    remember = forms.CharField(
        widget=forms.CheckboxInput(attrs={
            'value': 'remember-me'
        }))
    remember.required = False


#       <input type="email" id="inputEmail" class="form-control" placeholder="Email" required="" autofocus="">
#       <input type="password" id="inputPassword" class="form-control" placeholder="Пароль" required="">
