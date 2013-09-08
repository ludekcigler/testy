from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()

@register.filter
def czech_declination(value, aDeclinations):
    dec = [arg.strip() for arg in aDeclinations.split(",")]
    if (int(value) == 1):
        return u'%s %s' % (value, dec[0])
    elif (int(value) > 1 and int(value) <= 4):
        return u'%s %s' % (value, dec[1])
    else:
        return u'%s %s' % (value, dec[2])

class RangeNode(template.Node):
    def __init__(self, start, stop, step, context_name):
        if not self._isint(start):
            self.start = template.Variable(start)
        else:
            self.start = start

        if not self._isint(stop):
            self.stop = template.Variable(stop)
        else:
            self.stop = stop

        if not self._isint(step):
            self.step = template.Variable(step)
        else:
            self.step = step

        self.context_name = context_name

    def _isint(self, value):
        return isinstance(value, int)

    def _resolveint(self, value, context):
        if self._isint(value):
            return value
        return int(value.resolve(context))

    def render(self, context):
        start = self._resolveint(self.start, context)
        stop = self._resolveint(self.stop, context)
        step = self._resolveint(self.step, context)
    
        context[self.context_name] = range(start, stop, step)
        return ""

@register.tag
def num_range(parser, token):
    """
    Create a list containing an arithmetic progression that can be 
    iterated through in templates.

    If the start argument is omitted, it defaults to 0. 
    If step is positive, the last element is the largest start + i * step less than stop; if step is negative, the last element is the smallest start + i * step greater than stop. 
    step must not be zero (or else ValueError is raised).
    
    see http://docs.python.org/library/functions.html#range for more details.

    Syntax:
    {% num_range [start] stop [step] as some_range %}
    
    {% for i in some_range %}
      ... do something
    {% endfor %}
    """
    bits = token.contents.split()
    len_bits = len(bits)

    if len_bits not in range(4, 7):
        raise template.TemplateSyntaxError(_('%s tag requires between three and fifth arguments') % bits[0])
    if bits[-2] != 'as':
        raise template.TemplateSyntaxError(_("last but one argument to %s tag must be 'as'") % bits[0])

    #DEFAULTS
    start, step = 0, 1

    as_index = bits.index('as')

    if as_index == 2:
        stop = bits[1]
    else:
        start, stop = bits[1], bits[2]
        
        if as_index == 4:
            step = bits[3]

    context_name = bits[-1]

    return RangeNode(start, stop, step, context_name)

@register.filter_function
def order_by(queryset, args):
    args = [x.strip() for x in args.split(',')]
    return queryset.order_by(*args)
