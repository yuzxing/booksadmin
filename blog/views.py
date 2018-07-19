from django.shortcuts import render, redirect, reverse, HttpResponse
from django.contrib import auth
from utils.code import check_code
from blog.models import Article, Article2Tag, Tag, Category, Comment, ArticleUpDown, Blog, UserInfo
from django.db.models import F#导入F方法进行数据运算
#把需要数据同步的放在事物里
from django.db import transaction
from my_blog import settings
from bs4 import BeautifulSoup
import uuid
import json
import os

# 封装json序列化模块方法
from django.http import JsonResponse


USER_LIST = []


def index(request):
    article_list = Article.objects.all()

    return render(request, "index.html", {"article_list": article_list, 'user_list': USER_LIST})


def code(request):
    """
    生成图片验证码
    :param request:
    :return:
    """
    img,random_code = check_code()
    request.session['random_code'] = random_code
    from io import BytesIO
    stream = BytesIO()
    img.save(stream, 'png')
    return HttpResponse(stream.getvalue())


def login(request):
    """
    用户登陆
    :param request:
    :return:
    """
    if request.method == 'GET':
        return render(request, 'login.html')
    user = request.POST.get('user')
    pwd = request.POST.get('pwd')
    code = request.POST.get('code')
    user = auth.authenticate(username=user, password=pwd)
    if code.upper() != request.session['random_code'].upper():
        return render(request, 'login.html', {'msg': '验证码错误'})

    elif user:
        auth.login(request, user)
        return redirect("/index/")

    return render(request, 'login.html', {'msg': '用户名或密码错误'})


def form_data_upload(request):
    """
    ajax上传文件
    :param request:
    :return:
    """
    img_upload = request.FILES.get('img_upload')

    file_name = str(uuid.uuid4()) + "." + img_upload.name.rsplit('.', maxsplit=1)[1]
    img_file_path = os.path.join('static', 'imgs', file_name)
    with open(img_file_path, 'wb') as f:
        for line in img_upload.chunks():
            f.write(line)

    return HttpResponse(img_file_path)


def iframe_upload_img(request):
    if request.method == "GET":
        return render(request, 'register.html')
    user = request.POST.get('user')
    pwd = request.POST.get('pwd')
    avatar = request.POST.get('avatar')
    USER_LIST.append(
        {
            'user': user,
            'pwd': pwd,
            'avatar': avatar
        }
    )
    return redirect('/index/')


def upload_iframe(request):
    ret = {'status': True, 'data': None}
    try:
        avatar = request.FILES.get('avatar')
        file_name = str(uuid.uuid4()) + "." + avatar.name.rsplit('.', maxsplit=1)[1]
        img_file_path = os.path.join('static', 'imgs', file_name)
        with open(img_file_path, 'wb') as f:
            for line in avatar.chunks():
                f.write(line)
        ret['data'] = os.path.join("/", img_file_path)
    except Exception as e:
        ret['status'] = False
        ret['error'] = '上传失败'
    return HttpResponse(json.dumps(ret))


def logout(request):
    auth.logout(request)
    return redirect("/index/")


def home_site(request, username, **kwargs):#个人左侧标签,分类,日期归档

    user = UserInfo.objects.filter(username=username).first()#从UserInfo表中取用户
    if not user:
        return render(request, "not_found.html")#没有用户返回404页面
    blog = user.blog#用户的个人站点
    if not kwargs:
        article_list = Article.objects.filter(user__username=username)
    else:
        condition = kwargs.get("condition")
        params = kwargs.get("params")
        if condition == "category":
            article_list = Article.objects.filter(user__username=username).filter(category__title=params)
        elif condition == "tag":
            article_list = Article.objects.filter(user__username=username).filter(tags__title=params)
        else:
            year, month = params.split("/")
            article_list = Article.objects.filter(user__username=username)\
                .filter(create_time__year=year, create_time__month=month)
    if not article_list:
        return render(request, "not_found.html")
    # tag_list = Tag.objects.filter(blog=blog).annotate(c=Count('article')).values_list('title', 'c')#统计标签文章的数量
    # category_list = Category.objects.filter(blog=blog).annotate(c=Count('article')).values_list('title', 'c')#统计分类文章的数量
    # article_list = Article.objects.filter(user_id=user.pk)#个人站点的文章
    return render(request, "home_site.html", locals())


def article_details(request, username, article_id):#文章详情页
    user = UserInfo.objects.filter(username=username).first()
    blog = user.blog
    article_obj = Article.objects.filter(pk=article_id).first()
    comment_list = Comment.objects.filter(article_id=article_id)

    return render(request, "article_detail.html", locals())


def digg(request):
    print(request.POST)
    is_up = json.loads(request.POST.get("is_up"))
    article_id = request.POST.get("article_id")
    user_id = request.user.pk
    response = {"state": True, "msg": None}

    obj = ArticleUpDown.objects.filter(user_id=user_id, article_id=article_id).first()
    if obj:
        response["state"] = False
        response["handled"] = obj.is_up
    else:
        with transaction.atomic():
            new_obj = ArticleUpDown.objects.create(user_id=user_id, article_id=article_id, is_up=is_up)
            if is_up:
                Article.objects.filter(pk=article_id).update(up_count=F("up_count")+1)
            else:
                Article.objects.filter(pk=article_id).update(down_count=F("down_count")+1)

    return JsonResponse(response)


def comment(request):

    # 获取数据
    user_id = request.user.pk
    response = {"state": True, "msg": None}
    article_id = request.POST.get("article_id")
    pid = request.POST.get("pid")
    content = request.POST.get("content")
    if len(content) > 0:
        response["state"] = True
    # 生成评论对象
        with transaction.atomic():#把同步的数据放入事物里
            #把评论写入评论表里
            comment = Comment.objects.create(user_id=user_id, article_id=article_id, content=content, parent_comment_id=pid)
            #把当前文章里评论数更新加1
            Article.objects.filter(pk=article_id).update(comment_count=F("comment_count")+1)
        response["timer"] = comment.create_time.strftime("%Y-%m-%d %X")
        response["user"] = request.user.username
        response["content"] = comment.content
    else:
        response["state"] = False
    return JsonResponse(response)


def backend(request):
    user = request.user
    article_list = Article.objects.filter(user=user)
    return render(request, "backend/backend.html", locals())


def add_article(request):
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        user = request.user
        category = request.POST.get("cate")
        tags_pk_list = request.POST.getlist("tags")#取多个标签
        #引用BeautifulSoup过滤html标签html.parser
        soup = BeautifulSoup(content, "html.parser")
        for tag in soup.find_all():
            #判断如果有script标签
            if tag.name in ["script"]:
                tag.decompose()
        desc = soup.text[0:150]#取过滤后的标签
        article_obj = Article.objects.create(title=title, content=str(soup), user=user, category=category, desc=desc)
        for tag_pk in tags_pk_list:#循环标签列表
            Article2Tag.objects.create(article_id=article_obj.pk, tag_id=tag_pk)#添加多对多关系
        return redirect("/backend/")

    else:
        blog = request.user.blog
        cate_list = Category.objects.filter(blog=blog)
        tags = Tag.objects.filter(blog=blog)
        return render(request, "backend/add_article.html", locals())


def upload(request):#
    #FILES文件上传
    print(request.FILES)
    obj = request.FILES.get("upload_img")
    name = obj.name
#拼接路径
    path = os.path.join(settings.BASE_DIR, "static", "upload", name)
    with open(path, "wb") as f:
        for line in obj:
            f.write(line)
    res = {
        "error": 0,
        "url": "/static/upload/"+name
    }

    return JsonResponse(res)


def edit_article(request, edit_id):
    article_obj = Article.objects.filter(pk=edit_id).first()
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        user = request.user
        cate_pk = request.POST.get("cate")
        tags_pk_list = request.POST.getlist("tags")  # 取多个标签
        soup = BeautifulSoup(content, "html.parser")
        for tag in soup.find_all():
            # 判断如果有script标签
            if tag.name in ["script"]:
                tag.decompose()
        desc = soup.text[0:150]  # 取过滤后的标签
        article_obj_new = Article.objects.update(title=title, content=str(soup), user=user, category=cate_pk, desc=desc)
        for tag_pk in tags_pk_list:  # 循环标签列表
            Article2Tag.objects.update(article_id=article_obj_new.pk, tag_id=tag_pk)  # 添加多对多关系
        return redirect("/backend/")

    else:
        blog = request.user.blog
        cate_list = Category.objects.filter(blog=blog)
        tags = Tag.objects.filter(blog=blog)
        return render(request, "backend/edit_article.html", locals())
































































