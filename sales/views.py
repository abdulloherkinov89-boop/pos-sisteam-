from django.shortcuts import render

def mijoz_html(request):
    return render(request, 'mijoz.html')

def hisobot(request):
    return render(request, 'hisobot.html')