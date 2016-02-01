# encoding: utf-8

from __future__ import unicode_literals

from threading import local
from inspect import getargspec
from functools import partial

from marrow.package.loader import load


log = __import__('logging').getLogger(__name__)


class ThreadLocalExtension(object):
	"""Provide the current context as a thread local global.
	
	This provides a convienent global variable where you can store per-thread data.
	
	While the context itself is cleaned up after each call, any data you add won't be.  These are not request-locals.
	"""
	
	first = True
	provides = ['threadlocal']
	
	def __init__(self, where='web.core:local'):
		super(ThreadLocalExtension, self).__init__()
		
		if __debug__:
			log.debug("Initalizing ThreadLocal extension.")
		
		self.where = where
		self.local = None
		self.preserve = False
	
	def _lookup(self):
		module, _, name = self.where.rpartition(':')
		module = load(module)
		
		return module, name
	
	def start(self, context):
		module, name = self._lookup()
		
		if __debug__:
			log.debug("Preparing thread local storage and assigning main thread application context.")
		
		if hasattr(module, name):
			self.local = getattr(module, name)
			self.preserve = True
		else:
			self.local = local()
			setattr(module, name, self.local)
		
		self.local.context = context  # Main thread application context.
	
	def stop(self, context):
		self.local = None
		
		if __debug__:
			log.debug("Cleaning up thread local storage.")
		
		if self.preserve:
			return
		
		module, name = self._lookup()
		delattr(module, name)
	
	def prepare(self, context):
		if __debug__:
			log.debug("Assigning thread local request context.")
		
		self.local.context = context
	
	def after(self, result, exc=None):
		if __debug__:
			log.debug("Cleaning up thread local request context.")
		
		del self.local.context
