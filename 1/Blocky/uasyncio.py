import uerrno
import uselect as select
import usocket as _socket


DEBUG = 0
log = None

def set_debug(val):
    global DEBUG, log
    DEBUG = val
    if val:
        import logging
        log = logging.getLogger("uasyncio")

class EventLoop:

    def __init__(self, runq_len=100, waitq_len=16):
        self.runq = deque()
        self.waitq = utimeq.utimeq(waitq_len)
        # Current task being run. Task is a top-level coroutine scheduled
        # in the event loop (sub-coroutines executed transparently by
        # yield from/await, event loop "doesn't see" them).
        self.cur_task = None
        self.tasks = []

    def time(self):
        return time.ticks_ms()

    def create_task(self, coro):
        # CPython 3.4.2
        self.call_later_ms(0, coro)
        # CPython asyncio incompatibility: we don't return Task object

    def call_soon(self, callback, *args):
        if __debug__ and DEBUG:
            log.debug("Scheduling in runq: %s", (callback, args))
        self.runq.append(callback)
        if not isinstance(callback, type_gen):
            self.runq.append(args)

    def call_later(self, delay, callback, *args):
        self.call_at_(time.ticks_add(self.time(), int(delay * 1000)), callback, args)

    def call_later_ms(self, delay, callback, *args):
        if not delay:
            return self.call_soon(callback, *args)
        self.call_at_(time.ticks_add(self.time(), delay), callback, args)

    def call_at_(self, time, callback, args=()):
        if __debug__ and DEBUG:
            log.debug("Scheduling in waitq: %s", (time, callback, args))
        self.waitq.push(time, callback, args)
        self.tasks.append(str(callback).split("'")[1])

    def wait(self, delay):
        # Default wait implementation, to be overriden in subclasses
        # with IO scheduling
        if __debug__ and DEBUG:
            log.debug("Sleeping for: %s", delay)
        time.sleep_ms(delay)

    def run_forever(self):
        cur_task = [0, 0, 0]
        while True:
            # Expire entries in waitq and move them to runq
            tnow = self.time()
            while self.waitq:
                t = self.waitq.peektime()
                delay = time.ticks_diff(t, tnow)
                if delay > 0:
                    break
                self.waitq.pop(cur_task)
                self.tasks.remove(str(cur_task[1]).split("'")[1])
                if __debug__ and DEBUG:
                    log.debug("Moving from waitq to runq: %s", cur_task[1])
                self.call_soon(cur_task[1], *cur_task[2])

            # Process runq
            l = len(self.runq)
            if __debug__ and DEBUG:
                log.debug("Entries in runq: %d", l)
            while l:
                cb = self.runq.popleft()
                l -= 1
                args = ()
                if not isinstance(cb, type_gen):
                    args = self.runq.popleft()
                    l -= 1
                    if __debug__ and DEBUG:
                        log.info("Next callback to run: %s", (cb, args))
                    cb(*args)
                    continue

                if __debug__ and DEBUG:
                    log.info("Next coroutine to run: %s", (cb, args))
                self.cur_task = cb
                delay = 0
                try:
                    if args is ():
                        ret = next(cb)
                    else:
                        ret = cb.send(*args)
                    if __debug__ and DEBUG:
                        log.info("Coroutine %s yield result: %s", cb, ret)
                    if isinstance(ret, SysCall1):
                        arg = ret.arg
                        if isinstance(ret, SleepMs):
                            delay = arg
                        elif isinstance(ret, IORead):
                            cb.pend_throw(False)
                            self.add_reader(arg, cb)
                            continue
                        elif isinstance(ret, IOWrite):
                            cb.pend_throw(False)
                            self.add_writer(arg, cb)
                            continue
                        elif isinstance(ret, IOReadDone):
                            self.remove_reader(arg)
                        elif isinstance(ret, IOWriteDone):
                            self.remove_writer(arg)
                        elif isinstance(ret, StopLoop):
                            return arg
                        else:
                            assert False, "Unknown syscall yielded: %r (of type %r)" % (ret, type(ret))
                    elif isinstance(ret, type_gen):
                        self.call_soon(ret)
                    elif isinstance(ret, int):
                        # Delay
                        delay = ret
                    elif ret is None:
                        # Just reschedule
                        pass
                    elif ret is False:
                        # Don't reschedule
                        continue
                    else:
                        assert False, "Unsupported coroutine yield value: %r (of type %r)" % (ret, type(ret))
                except StopIteration as e:
                    if __debug__ and DEBUG:
                        log.debug("Coroutine finished: %s", cb)
                    continue
                except CancelledError as e:
                    if __debug__ and DEBUG:
                        log.debug("Coroutine cancelled: %s", cb)
                    continue
                # Currently all syscalls don't return anything, so we don't
                # need to feed anything to the next invocation of coroutine.
                # If that changes, need to pass that value below.
                if delay:
                    self.call_later_ms(delay, cb)
                else:
                    self.call_soon(cb)

            # Wait until next waitq task or I/O availability
            delay = 0
            if not self.runq:
                delay = -1
                if self.waitq:
                    tnow = self.time()
                    t = self.waitq.peektime()
                    delay = time.ticks_diff(t, tnow)
                    if delay < 0:
                        delay = 0
            self.wait(delay)

    def run_until_complete(self, coro):
        def _run_and_stop():
            yield from coro
            yield StopLoop(0)
        self.call_soon(_run_and_stop())
        self.run_forever()

    def stop(self):
        self.call_soon((lambda: (yield StopLoop(0)))())

    def close(self):
        pass


		
class PollEventLoop(EventLoop):

    def __init__(self, runq_len=16, waitq_len=16):
        EventLoop.__init__(self, runq_len, waitq_len)
        self.poller = select.poll()
        self.objmap = {}

    def add_reader(self, sock, cb, *args):
        if DEBUG and __debug__:
            log.debug("add_reader%s", (sock, cb, args))
        if args:
            self.poller.register(sock, select.POLLIN)
            self.objmap[id(sock)] = (cb, args)
        else:
            self.poller.register(sock, select.POLLIN)
            self.objmap[id(sock)] = cb

    def remove_reader(self, sock):
        if DEBUG and __debug__:
            log.debug("remove_reader(%s)", sock)
        self.poller.unregister(sock)
        del self.objmap[id(sock)]

    def add_writer(self, sock, cb, *args):
        if DEBUG and __debug__:
            log.debug("add_writer%s", (sock, cb, args))
        if args:
            self.poller.register(sock, select.POLLOUT)
            self.objmap[id(sock)] = (cb, args)
        else:
            self.poller.register(sock, select.POLLOUT)
            self.objmap[id(sock)] = cb

    def remove_writer(self, sock):
        if DEBUG and __debug__:
            log.debug("remove_writer(%s)", sock)
        try:
            self.poller.unregister(sock)
            self.objmap.pop(id(sock), None)
        except OSError as e:
            # StreamWriter.awrite() first tries to write to a socket,
            # and if that succeeds, yield IOWrite may never be called
            # for that socket, and it will never be added to poller. So,
            # ignore such error.
            if e.args[0] != uerrno.ENOENT:
                raise

    def wait(self, delay):
        if DEBUG and __debug__:
            log.debug("poll.wait(%d)", delay)
        # We need one-shot behavior (second arg of 1 to .poll())
        res = self.poller.ipoll(delay, 1)
        #log.debug("poll result: %s", res)
        # Remove "if res" workaround after
        # https://github.com/micropython/micropython/issues/2716 fixed.
        if res:
            for sock, ev in res:
                cb = self.objmap[id(sock)]
                if ev & (select.POLLHUP | select.POLLERR):
                    # These events are returned even if not requested, and
                    # are sticky, i.e. will be returned again and again.
                    # If the caller doesn't do proper error handling and
                    # unregister this sock, we'll busy-loop on it, so we
                    # as well can unregister it now "just in case".
                    self.remove_reader(sock)
                if DEBUG and __debug__:
                    log.debug("Calling IO callback: %r", cb)
                if isinstance(cb, tuple):
                    cb[0](*cb[1])
                else:
                    cb.pend_throw(None)
                    self.call_soon(cb)


class StreamReader:

    def __init__(self, polls, ios=None):
        if ios is None:
            ios = polls
        self.polls = polls
        self.ios = ios

    def read(self, n=-1):
        while True:
            yield IORead(self.polls)
            res = self.ios.read(n)
            if res is not None:
                break
            # This should not happen for real sockets, but can easily
            # happen for stream wrappers (ssl, websockets, etc.)
            #log.warn("Empty read")
        if not res:
            yield IOReadDone(self.polls)
        return res

    def readexactly(self, n):
        buf = b""
        while n:
            yield IORead(self.polls)
            res = self.ios.read(n)
            assert res is not None
            if not res:
                yield IOReadDone(self.polls)
                break
            buf += res
            n -= len(res)
        return buf

    def readline(self):
        if DEBUG and __debug__:
            log.debug("StreamReader.readline()")
        buf = b""
        while True:
            yield IORead(self.polls)
            res = self.ios.readline()
            assert res is not None
            if not res:
                yield IOReadDone(self.polls)
                break
            buf += res
            if buf[-1] == 0x0a:
                break
        if DEBUG and __debug__:
            log.debug("StreamReader.readline(): %s", buf)
        return buf

    def aclose(self):
        yield IOReadDone(self.polls)
        self.ios.close()

    def __repr__(self):
        return "<StreamReader %r %r>" % (self.polls, self.ios)


class StreamWriter:

    def __init__(self, s, extra):
        self.s = s
        self.extra = extra

    def awrite(self, buf, off=0, sz=-1):
        # This method is called awrite (async write) to not proliferate
        # incompatibility with original asyncio. Unlike original asyncio
        # whose .write() method is both not a coroutine and guaranteed
        # to return immediately (which means it has to buffer all the
        # data), this method is a coroutine.
        if sz == -1:
            sz = len(buf) - off
        if DEBUG and __debug__:
            log.debug("StreamWriter.awrite(): spooling %d bytes", sz)
        while True:
            res = self.s.write(buf, off, sz)
            # If we spooled everything, return immediately
            if res == sz:
                if DEBUG and __debug__:
                    log.debug("StreamWriter.awrite(): completed spooling %d bytes", res)
                return
            if res is None:
                res = 0
            if DEBUG and __debug__:
                log.debug("StreamWriter.awrite(): spooled partial %d bytes", res)
            assert res < sz
            off += res
            sz -= res
            yield IOWrite(self.s)
            #assert s2.fileno() == self.s.fileno()
            if DEBUG and __debug__:
                log.debug("StreamWriter.awrite(): can write more")

    # Write piecewise content from iterable (usually, a generator)
    def awriteiter(self, iterable):
        for buf in iterable:
            yield from self.awrite(buf)

    def aclose(self):
        yield IOWriteDone(self.s)
        self.s.close()

    def get_extra_info(self, name, default=None):
        return self.extra.get(name, default)

    def __repr__(self):
        return "<StreamWriter %r>" % self.s


def open_connection(host, port, ssl=False):
    if DEBUG and __debug__:
        log.debug("open_connection(%s, %s)", host, port)
    ai = _socket.getaddrinfo(host, port, 0, _socket.SOCK_STREAM)
    ai = ai[0]
    s = _socket.socket(ai[0], ai[1], ai[2])
    s.setblocking(False)
    try:
        s.connect(ai[-1])
    except OSError as e:
        if e.args[0] != uerrno.EINPROGRESS:
            raise
    if DEBUG and __debug__:
        log.debug("open_connection: After connect")
    yield IOWrite(s)
#    if __debug__:
#        assert s2.fileno() == s.fileno()
    if DEBUG and __debug__:
        log.debug("open_connection: After iowait: %s", s)
    if ssl:
        print("Warning: uasyncio SSL support is alpha")
        import ussl
        s.setblocking(True)
        s2 = ussl.wrap_socket(s)
        s.setblocking(False)
        return StreamReader(s, s2), StreamWriter(s2, {})
    return StreamReader(s), StreamWriter(s, {})


def start_server(client_coro, host, port, backlog=10):
    if DEBUG and __debug__:
        log.debug("start_server(%s, %s)", host, port)
    ai = _socket.getaddrinfo(host, port, 0, _socket.SOCK_STREAM)
    ai = ai[0]
    s = _socket.socket(ai[0], ai[1], ai[2])
    s.setblocking(False)

    s.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)
    s.bind(ai[-1])
    s.listen(backlog)
    while True:
        if DEBUG and __debug__:
            log.debug("start_server: Before accept")
        yield IORead(s)
        if DEBUG and __debug__:
            log.debug("start_server: After iowait")
        s2, client_addr = s.accept()
        s2.setblocking(False)
        if DEBUG and __debug__:
            log.debug("start_server: After accept: %s", s2)
        extra = {"peername": client_addr}
        yield client_coro(StreamReader(s2), StreamWriter(s2, extra))


_event_loop_class = PollEventLoop

import utime as time
import utimeq
from Blocky.deque import deque


type_gen = type((lambda: (yield))())

DEBUG = 0
log = None

def set_debug(val):
    global DEBUG, log
    DEBUG = val
    if val:
        import logging
        log = logging.getLogger("uasyncio.core")


class CancelledError(Exception):
    pass


class TimeoutError(CancelledError):
    pass



class SysCall:

    def __init__(self, *args):
        self.args = args

    def handle(self):
        raise NotImplementedError

# Optimized syscall with 1 arg
class SysCall1(SysCall):

    def __init__(self, arg):
        self.arg = arg

class StopLoop(SysCall1):
    pass

class IORead(SysCall1):
    pass

class IOWrite(SysCall1):
    pass

class IOReadDone(SysCall1):
    pass

class IOWriteDone(SysCall1):
    pass


_event_loop = None
_event_loop_class = EventLoop
def get_event_loop(runq_len=16, waitq_len=16):
    global _event_loop
    if _event_loop is None:
        _event_loop = _event_loop_class(runq_len, waitq_len)
    return _event_loop

def sleep(secs):
    yield int(secs * 1000)

# Implementation of sleep_ms awaitable with zero heap memory usage
class SleepMs(SysCall1):

    def __init__(self):
        self.v = None
        self.arg = None

    def __call__(self, arg):
        self.v = arg
        #print("__call__")
        return self

    def __iter__(self):
        #print("__iter__")
        return self

    def __next__(self):
        if self.v is not None:
            #print("__next__ syscall enter")
            self.arg = self.v
            self.v = None
            return self
        #print("__next__ syscall exit")
        _stop_iter.__traceback__ = None
        raise _stop_iter

_stop_iter = StopIteration()
sleep_ms = SleepMs()


def cancel(coro):
    prev = coro.pend_throw(CancelledError())
    if prev is False:
        _event_loop.call_soon(coro)


class TimeoutObj:
    def __init__(self, coro):
        self.coro = coro


def wait_for_ms(coro, timeout):

    def waiter(coro, timeout_obj):
        res = yield from coro
        if __debug__ and DEBUG:
            log.debug("waiter: cancelling %s", timeout_obj)
        timeout_obj.coro = None
        return res

    def timeout_func(timeout_obj):
        if timeout_obj.coro:
            if __debug__ and DEBUG:
                log.debug("timeout_func: cancelling %s", timeout_obj.coro)
            prev = timeout_obj.coro.pend_throw(TimeoutError())
            #print("prev pend", prev)
            if prev is False:
                _event_loop.call_soon(timeout_obj.coro)

    timeout_obj = TimeoutObj(_event_loop.cur_task)
    _event_loop.call_later_ms(timeout, timeout_func, timeout_obj)
    return (yield from waiter(coro, timeout_obj))


def wait_for(coro, timeout):
    return wait_for_ms(coro, int(timeout * 1000))


def coroutine(f):
    return f

#
# The functions below are deprecated in uasyncio, and provided only
# for compatibility with CPython asyncio
#

def ensure_future(coro, loop=_event_loop):
    _event_loop.call_soon(coro)
    # CPython asyncio incompatibility: we don't return Task object
    return coro


# CPython asyncio incompatibility: Task is a function, not a class (for efficiency)
def Task(coro, loop=_event_loop):
    # Same as async()
    _event_loop.call_soon(coro)





