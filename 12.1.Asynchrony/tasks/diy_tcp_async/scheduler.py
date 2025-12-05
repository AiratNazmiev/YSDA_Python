import time
from collections import deque
import heapq
from select import select


class Scheduler:
    def __init__(self):
        """
        Initialize the event loop / scheduler state.

        Expected fields:
            deque of callbacks or Task objects that are ready to run immediately.
            min-heap of (deadline, sequence, callback) for time-based scheduling.
            monotonically increasing integer to break ties in the heap.
            dict mapping fileno -> callback waiting for socket to become readable.
            dict mapping fileno -> callback waiting for socket to become writable.
            currently running Task (or None when no task is running).
        """
        pass

    def call_soon(self, func):
        """
        Schedule a callback to be run as soon as possible.
        """
        pass

    def call_later(self, delay, func):
        """
        Schedule a callback to be run after 'delay' seconds.
        """
        pass

    def read_wait(self, fileno, func):
        """
        Register a callback to be resumed when the file descriptor 'fileno'
        becomes readable.
        """
        pass

    def write_wait(self, fileno, func):
        """
        Register a callback to be resumed when the file descriptor 'fileno'
        becomes writable.
        """
        pass

    def run(self):
        """
        Main event loop.

        Expected behaviour:
            Searching and using pending callback in 'ready', a sleeping
            timer in 'sleeping', or some I/O waiters in read_waiting/write_waiting
        """
        pass

    def new_task(self, coro):
        """
        Wrap a coroutine object 'coro' into a Task and schedule it to run.
        """
        pass

    async def sleep(self, delay):
        """
        Coroutine-friendly sleep.
        """
        pass

    async def recv(self, sock, maxbytes):
        """
        Asynchronous version of socket.recv.

        Expected behaviour:
            register the current Task via read_wait(sock.fileno(), self.current);
            set self.current to None;
            yield control back to the scheduler using 'await switch()';
            when the Task is resumed, actually perform sock.recv(maxbytes)
            and return the received bytes.
        """
        pass

    async def send(self, sock, data):
        """
        Asynchronous version of socket.send.

        Expected behaviour:
            register the current Task via write_wait(sock.fileno(), self.current);
            set self.current to None;
            yield control with 'await switch()';
            when resumed, call sock.send(data) and return the number of bytes sent.
        """
        pass

    async def accept(self, sock):
        """
        Asynchronous version of socket.accept.

        Expected behaviour:
            register the current Task via read_wait(sock.fileno(), self.current);
            set self.current to None;
            yield control with await switch();
            when resumed, call sock.accept() and return (client_sock, address).
        """
        pass


class Awaitable:
    """
    Minimal awaitable used to yield control back to the scheduler.

    await switch() should:
        call Awaitable.__await__();
        produce a generator that yields exactly once;
        let the scheduler run other ready tasks until this Task is scheduled again.
    """
    def __await__(self):
        """
        Should yield control exactly once.
        No return value is needed.
        """
        yield


def switch():
    """
    Used inside async functions to yield control to the scheduler.
    """
    pass


class Task:
    """
    Small wrapper around a coroutine object.

    The scheduler keeps Task instances in the 'ready' deque and
    drives them by calling task().
    """
    def __init__(self, coro):
        """
        Store the wrapped coroutine.
        """
        pass

    def __call__(self):
        """
        Advance the coroutine by one step.

        Expected behaviour:
            set current to this Task;
            if the coroutine has not finished (no StopIteration) and
            current is still this Task, append this Task back to
            ready tasks so it will continue later;
            if StopIteration is raised, the coroutine is done and the Task
            mustn't be re-scheduled.
        """
        pass


# Global scheduler instance used by the server code
sched = Scheduler()
