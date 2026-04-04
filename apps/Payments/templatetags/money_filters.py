from django import template

register = template.Library()

@register.filter
def cents_to_dollars(value):
    try:
        return "{:.2f}".format(value / 100)
    except:
        return value
