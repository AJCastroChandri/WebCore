# encoding: utf-8

from inspect import isclass

from marrow.wsgi.exceptions import HTTPNotFound


def ipeek(d):
    """Iterate through a list, popping elements after they have been seen."""
    while d:
        yield d[0]
        d.pop(0)


class ObjectDispatchDialect(object):
    def __init__(self, config):
        self.trailing = config.get('slashes', True)
    
    def __call__(self, context, root):
        log = context.log
        path = str(context.request.remainder)
        trailing = path and path[-1] == '/'
        chunks = [i for i in path.strip('/').split('/') if i]
        
        last = ''
        parent = None
        current = root
        
        # Iterate through and consume the path element (chunk) list.
        for chunk in ipeek(chunks):
            log.debug(chunk=chunk, chunks=chunks)
            
            parent = current
            
            # Security: prevent access to real private attributes.
            # This is tricky as we need to avoid __getattr__ behaviour.
            if chunk[0] == '_' and (hasattr(current.__class__, chunk) or chunk in current.__dict__):
                raise HTTPNotFound()
            
            current = getattr(parent, chunk, None)
            log.data(attr=current).debug("Found attribute.")
            
            # If there is no attribute (real or via __getattr__) try the __lookup__ method to re-route.
            if not current:
                if not callable(parent):
                    try:
                        fallback = parent.__lookup__
                    except AttributeError:
                        raise HTTPNotFound()
                    else:
                        current, consumed = fallback(*chunks)
                        chunk = '/'.join(consumed)
                        del chunks[1:len(consumed)]
                else:
                    yield last.split('/'), parent, True
                    return
            
            if isclass(current):
                current = current(context)
            
            yield last.split('/'), parent, False
            
            last = chunk
        
        if isclass(current) and hasattr(current, '__call__'):
            current = current(context).__call__
        
        yield last.split('/'), current, True


def main():
    from marrow.util.bunch import Bunch
    from marrow.logging import Log, DEBUG
    
    request = Bunch(remainder='/')
    context = Bunch(log=Log(level=DEBUG).name(__file__), request=request)
    
    class Controller(object):
        def __init__(self, context):
            self._ctx = context
    
    class RootController(Controller):
        def __call__(self):
            return "Hello world!"
    
    router = ObjectDispatchDialect(dict())
    
    for i,j,k in router(context, RootController):
        context.log.info(path=i,obj=j,final=k)
    
    request.remainder = '/about/staff'
    
    class AboutController(Controller):
        def staff(self):
            return "Staff page."
    
    class RootController(Controller):
        about = AboutController
    
    print()
    for i,j,k in router(context, RootController):
        context.log.info(path=i,obj=j,final=k)
    
    def index(context):
        return "Foo!"
    
    print()
    for i,j,k in router(context, index):
        context.log.info(path=i,obj=j,final=k)

if __name__ == '__main__':
    main()