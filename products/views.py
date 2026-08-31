from django.shortcuts import render

def test_view(request):
    return render(request, 'test.html')

def home_view(request):
    return render(request, 'home.html')

def ombor_view(request):
    return render(request, 'ombor.html')

def filal_view(request):
    return render(request, 'filallar.html')

def sozlamalar(request):
    return render(request, 'sozlamalar.html')
