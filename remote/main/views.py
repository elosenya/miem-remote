import re

from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from .forms import LoginForm
from django.contrib.auth import authenticate, login, logout
from .telnet_sessions import start_session, get_session, devices, devs_update_events
import json
import time
import threading
import os
import requests
from django.contrib.auth.models import User


def index(request):
    login_var = request.user.is_authenticated
    if login_var is False:
        return HttpResponseRedirect('/login')
    username = request.user.first_name + ' ' + request.user.last_name
    return render(request, 'main/index.html', {"login": login_var, "username": username})


def pnet(request):
    login_var = request.user.is_authenticated
    if login_var is False:
        return HttpResponseRedirect('/login')
    stage = request.GET.get('stage')
    if stage == "2":
        user = User.objects.get(pk=request.user.id)
        login = user.__str__()
        passwd = user.pnetmodel.password
        print(type(request.META.get('HTTP_COOKIE')))
        r = requests.post('https://kyky.6u6u.ru:8081/store/public/auth/login/login',
                          data=json.dumps({'username': f"{login}",
                                           'password': f"{passwd}",
                                           'html': '1',
                                           'captcha': {'login_captcha': 'AA'}
                                           }, separators=(',', ':')),
                          headers={'Content-Type': 'application/json',
                                   'Accept': '*/*',
                                   'Accept-Encoding': 'gzip, deflate',
                                   'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                                   'Cache-Control': 'no-cache',
                                   'Connection': 'keep-alive',
                                   'Cookie': request.META.get('HTTP_COOKIE').replace("%3D", "="),
                                   'Host': 'kyky.6u6u.ru:8081',
                                   'Origin': 'https://kyky.6u6u.ru:8081',
                                   'Pragma': 'no-cache',
                                   'Referer': 'https://kyky.6u6u.ru:8081/enter.php',
                                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                                   'X-Xsrf-Token': request.COOKIES['XSRF-TOKEN'].replace('%3D', '=')
                                   },
                          verify=False
                          )
        print(r.status_code, r.reason, r.text[0:200], r.cookies.keys())
        if r.status_code == 202:
            response = HttpResponseRedirect('https://kyky.6u6u.ru:8081/store/public/admin/main/view')
            for cookie in r.cookies.keys():
                if cookie == 'XSRF-TOKEN':
                    response.set_cookie(cookie, r.cookies[cookie], max_age=7200)
                    continue
                if cookie == 'token':
                    response.set_cookie(cookie, r.cookies[cookie], max_age=3600, domain='kyky.6u6u.ru', httponly=True)
                    continue
                response.set_cookie(cookie, r.cookies[cookie], max_age=7200, httponly=True)
            return response
        return HttpResponseRedirect('?')
    return render(request, 'main/pnet.html')


def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            user = authenticate(username=cd['email'], password=cd['password'])

            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponseRedirect('/')
                else:
                    return HttpResponse("Что-то пошло не так, попробуйте снова")
            else:
                return HttpResponse("Учётные данные неверны, попробуйте снова")

    else:
        form = LoginForm()
    return render(request, 'main/login.html', {"form": form})


def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/login')


def telnet(request):
    login_var = request.user.is_authenticated
    if login_var is False:
        return HttpResponseRedirect('/login')
    dev_id = ""
    if 'id' in request.GET:
        dev_id = request.GET.get('id')
    if (not dev_id.isdigit() or int(dev_id) < 0 or int(dev_id) >= len(devices) or
            (devices[int(dev_id)].busy is True and devices[int(dev_id)].session != request.COOKIES['sessionid'])):
        return HttpResponseRedirect('/devices_page')

    dev_id = int(dev_id)
    username = request.user.first_name + ' ' + request.user.last_name
    session = request.COOKIES.get('sessionid')
    tn = get_session(session)
    if tn is None:
        tn = start_session(session, dev_id)
        if tn is None:
            return HttpResponseRedirect('/devices_page')
    else:
        if tn.dev_id != dev_id:
            tn.destroy_session(session)
            tn = start_session(session, dev_id)
    tn.tn.get_socket().send(b'\r\n')
    history = tn.history()
    return render(request, 'main/telnet.html', {"login": login_var, "username": username,
                                                'history': history.decode('ascii'),
                                                "quit_str": tn.quit_str.decode('ascii'),
                                                "start_time": tn.get_start_time(),
                                                "session_time": tn.session_time})


def telnet_cmd_hist(request):
    session = request.COOKIES.get('sessionid')
    tn = get_session(session)
    return HttpResponse(json.dumps(tn.cmd_hist))


def devices_page(request):
    login_var = request.user.is_authenticated
    if login_var is False:
        return HttpResponseRedirect('/login')
    session = request.COOKIES.get('sessionid')
    username = request.user.first_name + ' ' + request.user.last_name
    session = request.COOKIES.get('sessionid')

    return render(request, 'main/devs.html', {"login": login_var, "username": username,
                                              "devices": devices, "session": session})


def telnet_read_new(request):
    session = request.COOKIES.get('sessionid')
    tn = get_session(session)
    if tn is None:
        return HttpResponse(json.dumps(["Соединение разорвано", -1]))
    add_str, n = tn.read()
    return HttpResponse(json.dumps([add_str, n]))


def telnet_write_new(request):
    session = request.COOKIES.get('sessionid')
    tn = get_session(session)
    cmd = str(request.GET.get('cmd')).encode('ascii', errors='ignore')
    if tn is None:
        return HttpResponse("Соединение разорвано\n")
    tn.write(cmd)
    return HttpResponse()


def knowledge_base(request):
    login_var = request.user.is_authenticated
    if login_var is False:
        return HttpResponseRedirect('/login')
    username = request.user.first_name + ' ' + request.user.last_name

    chapters = ['chapter_0', 'chapter_1', 'chapter_2', 'chapter_3', 'chapter_4', 'chapter_5', 'chapter_6', 'chapter_7',
                'chapter_8', 'chapter_9', 'chapter_10', 'chapter_11', 'chapter_12',
                'chapter_13', 'chapter_14', 'chapter_15']
    id = request.GET.get('id')
    if id is None or not id.isdigit() or int(id) < 0 or int(id) >= len(chapters):
        return render(request, 'main/knowledge_base/contents.html',
                      {"login": login_var, "username": username})
    else:
        chapter_id = int(id)
    return render(request, f'main/knowledge_base/{chapters[chapter_id]}.html',
                  {"login": login_var, "username": username, "chapter_id": chapter_id})


def devs_update(request):
    if request.GET.get('wait') == "1":
        event = threading.Event()
        devs_update_events.append(event)
        print(devs_update_events)
        event.wait(timeout=15)
        event.clear()
        devs_update_events.remove(event)
    devs = []
    names = []
    for dev in devices:
        devs.append(dev.busy)
        names.append(dev.name)
    print(devs)
    return HttpResponse(json.dumps([devs, names]))
