from django import template
register = template.Library()

@register.filter
def split_bullets(value):
    return [b.strip() for b in value.split('•') if b.strip()]