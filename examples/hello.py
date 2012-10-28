# encoding: utf-8

class Root(object):
    def __init__(self, context):
        self._ctx = context
    
    def __call__(self, name):
        """
        /hello -- 500
        /hello?name=Bob
        /hello POST name=bob
        /hello/Bob
        """
        return "Hello " + name


if __name__ == '__main__':
    from web.core.application import Application
    from wsgiref.simple_server import make_server
    make_server('127.0.0.1', 8080, Application(Root)).serve_forever()
