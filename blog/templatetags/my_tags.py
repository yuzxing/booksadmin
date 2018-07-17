from django import template
from django.db.models import Count, Avg, Max, Min, Sum
from blog.models import Category,Blog ,Tag, Comment, Article, ArticleUpDown, Article2Tag, UserInfo

register = template.Library()


@register.simple_tag
def mul_tag(x, y):

    return x*y


@register.inclusion_tag("left_region.html")
def get_query_data(username):

    user = UserInfo.objects.filter(username=username).first()
    blog = user.blog
    print(blog)
    # blog_id = Blog.objects.filter(site_name=user).values('nid')
    # blog = blog_id.get('nid')

    cate_list = Category.objects.filter(blog=blog).annotate(c=Count("article__title")).values_list("title", "c")
    print(cate_list)
    tag_list = Tag.objects.filter(blog=blog).annotate(c=Count("article__title")).values_list("title", "c")

    date_list = Article.objects.filter(user=user).extra(select={"y_m_date": "strftime('%%Y/%%m', create_time)"}).\
        values("y_m_date").annotate(c=Count("title")).values_list("y_m_date", "c")
    print(date_list)
    return {"username": username, "cate_list": cate_list, "tag_list": tag_list, "date_list": date_list}


