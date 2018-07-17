"""my_blog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path
from blog import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name="index"),#首页
    path('login/', views.login, name="login"),#登录
    path('code/', views.code, name="code"),#登录
    path('logout/', views.logout, name="logout"),#注销
    path('index/', views.index, name="index"),#首页
    path('digg/', views.digg),#点赞
    path('backend/', views.backend, name="backend"),#点赞
    path('backend/add_article/', views.add_article, name="add_article"),#点赞
    re_path('backend/edit_article/(?P<edit_id>(\d+))/', views.edit_article, name="edit_article"),#点赞
    path('comment/', views.comment),#评论
    re_path('(?P<username>\w+)/$', views.home_site, name="home_site"),#个人站点
    re_path('(?P<username>\w+)/(?P<condition>tag|category|archive)/(?P<params>.*)', views.home_site, name="home_site"),#个人站点详情页
    re_path('(?P<username>\w+)/articles/(?P<article_id>\d+)$', views.article_details, name="article_details"),#个人文章详情页


    # 个人文章详情页
]






















