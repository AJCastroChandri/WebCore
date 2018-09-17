# encoding: utf-8

#import time
#import pytest

from concurrent.futures import ThreadPoolExecutor
from webob import Request

from web.core import Application
#from web.core.context import Context
from web.ext.defer import DeferralExtension, DeferredExecutor


sentinel = object()


results = []


def deferred(a, b):
	global results
	results.append("called")
	return a * b


def resulting(receipt):
	global results
	results.append("returned")
	results.append(receipt.result())


class Root(object):
	def __init__(self, ctx):
		self.ctx = ctx
	
	def __call__(self):
		print("Submitting.")
		receipt = self.ctx.defer.submit(deferred, 2, 4)
		receipt.add_done_callback(resulting)
		return repr(receipt)

	def isa(self):
		return type(self.ctx.defer).__name__ + '\n' + type(self.ctx.executor).__name__




class TestDeferralExtension(object):
	app = Application(Root, extensions=[DeferralExtension()])
	
	def dtest_use(self):
		req = Request.blank('/')
		status, headers, body_iter = req.call_application(self.app)
	
	def test_preparation(self):
		app = Application(Root, extensions=[DeferralExtension()])
		ctx = app._Application__context  # "private" attribute
		
		assert 'executor' in ctx
		assert isinstance(ctx.executor, ThreadPoolExecutor)
		
		ctx = ctx._promote('RequestContext')
		
		assert 'defer' in ctx
		assert isinstance(ctx.defer, DeferredExecutor)
	
	def test_submission(self):
		req = Request.blank('/')
		status, headers, body_iter = req.call_application(self.app)
		body = b''.join(body_iter).decode('utf8')
		# DeferredFuture(<function deferred at 0x10aed5488>, *(2, 4), **{}, callbacks=1)
		assert body.startswith('DeferredFuture(')
		assert 'function deferred' in body
		assert '*(2, 4)' in body
		assert '**{}' in body
		assert body.endswith(', callbacks=1)')
		
		assert len(results) == 3
		assert results == ['called', 'returned', 8]
	
	def test_context(self):
		req = Request.blank('/isa')
		status, headers, body_iter = req.call_application(self.app)
		body = b''.join(body_iter).decode('utf8')
		defer, _, executor = body.partition('\n')
		
		assert defer == 'DeferredExecutor'
		assert executor == 'ThreadPoolExecutor'




'''


def test_deferred_future():
	"""
	test task.cancel()
	test task.cancelled()
	test task.running()
	test task.done()
	test task.result()
	test task.exception()
	test task.add_done_callback() with Executor
	test task.set_running_or_notify_cancel()
	test task.schedule() with Executor
	"""
	pass


def test_deferred_executor():
	executor = ThreadPoolExecutor()
	
	deferred_executor = DeferredExecutor(executor)
	
	future = deferred_executor.submit(sentinel)
	assert future is not None
	deferred_executor.shutdown()
	assert future.running() is True
	
	future = deferred_executor.submit(sentinel)
	deferred_executor.shutdown(wait=False)
	assert future.running() is False
	
	deferred_executor._schedule_one(future)
	assert future.running() is True


def test_defer_extension_executor():
	ctx = Context()
	ext = DeferralExtension(Executor=ThreadPoolExecutor)
	
	ext.start(ctx)
	assert hasattr(ctx, 'executor')
	assert isinstance(ctx.executor, ThreadPoolExecutor)
	ext.stop(ctx)


def test_defer_extension_deferred_executor():
	ctx = Context()
	ext = DeferralExtension(Executor=ThreadPoolExecutor)
	ext.start(ctx)
	
	assert hasattr(ctx, 'defer')
	#assert isinstance(ctx.deferred_executor, lazy)
	
	rctx = ctx._promote('RequestContext')
	assert 'defer' not in rctx.__dict__
	assert hasattr(rctx, 'executor')
	
	# done correctly executes deferred futures
	future = rctx.defer.submit(sentinel)
	assert 'defer' in rctx.__dict__ and isinstance(rctx.defer, DeferredExecutor)
	ext.done(rctx)
	assert future.running() is True
	
	# Test that deferred executor is never lazy loaded if not ccessed
	rctx = ctx._promote('RequestContext')
	ext.done(rctx)
	assert 'defer' not in rctx.__dict__
	
	ext.stop(ctx)
	assert ctx.executor._shutdown is True

'''

if __name__ == '__main__':
	TestDeferralExtension.app.serve('wsgiref')
