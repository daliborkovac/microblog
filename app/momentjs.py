from jinja2 import Markup


class MomentJS(object):
    """ A wrapper for moment.js that we can invoke from the templates. This is going to save us time in
    the future if we need to change our timestamp rendering code, because we will have it just in one place.
    Usage example:
        ts = post.timestamp
        moment_ts = momentjs(ts)
        print(moment_ts.format('LLLL'))
        print(moment_ts.calendar())
        print(moment_ts.fromNow())
    """
    def __init__(self, timestamp):
        self.timestamp = timestamp

    def render(self, fmt):
        """ This method produces a piece of JavaScript for rendering timestamp information.
        :param fmt: a format string that needs to be applied to moment() method from moment.js
        :return: A piece of JavaScript code like in this example:
                    <script>
                    document.write(moment("2008-11-04T08:54:00 Z").format("LLLL")
                    </script>
                Instead of .format() method we can also use calendar() or fromNow() methods of moment.js.
        """
        return Markup('<script>\ndocument.write(moment(\"{}\").{});\n</script>'.format(self.timestamp.strftime("%Y-%m-%dT%H:%M:%S Z"), fmt))

    def format(self, fmt):
        """
        :param fmt: a moment.js format, like L, LL, LLL, LLLL, dddd, ...
        :return: calls the render method with a given format
        """
        return self.render("format(\"{}\")".format(fmt))

    def calendar(self):
        """
        :return: calls the render method with format calendar()
        """
        return self.render("calendar()")

    def fromNow(self):
        """
        :return: calls the render method with format fromNow()
        """
        return self.render("fromNow()")