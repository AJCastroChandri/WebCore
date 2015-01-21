# encoding: utf-8
from __future__ import unicode_literals, division, print_function, absolute_import

from marrow.util.compat import basestring

try:
    from redis import StrictRedis
except ImportError:
    raise ImportError('You need to install redis to use this extension')


class RedisExtension(object):
    provides = ['redis', 'database']

    def __init__(self, context, contextvar='redis', connection=None, **conn_params):
        super(RedisExtension, self).__init__()

        if not isinstance(contextvar, basestring):
            raise TypeError('The "contextvar" option needs to be a string')
        if connection is not None and not isinstance(connection, StrictRedis):
            raise TypeError('The "connection" option needs to be a StrictRedis instance')

        self._contextvar = contextvar
        self._conn_params = conn_params
        self._connection = connection

    def start(self, context):
        # Create a new connection if none was supplied (this does not yet actually connect to the server)
        if self._connection is not None:
            self._connection = StrictRedis(**self._conn_params)

        # Check that the connection is valid
        self._connection.ping()

        # Add the connection to the context
        if hasattr(context, self._contextvar):
            raise Exception('The context already has a variable named "%s"' % self._contextvar)
        setattr(context, self._contextvar, self._connection)