import os
import random
import socket
import time
import subprocess
import sys

import pytest

import scheduler
from server import SERVER_PORT_ASYNC


def start_server_process() -> subprocess.Popen:
    script_path = os.path.join(os.path.dirname(__file__), "server.py")
    proc = subprocess.Popen(
        [sys.executable, script_path],
    )
    return proc


def _terminate_proc(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=2.0)
    except subprocess.TimeoutExpired:
        proc.kill()


def _wait_for_port(port: int, timeout: float = 5.0) -> None:
    start = time.time()
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect(("127.0.0.1", port))
            return
        except OSError:
            if time.time() - start > timeout:
                raise RuntimeError(f"Server on port {port} did not start in time")
            time.sleep(0.1)


def _recv_until_zero(sock: socket.socket, bufsize: int = 4096) -> bytes:
    chunks = []
    while True:
        chunk = sock.recv(bufsize)
        if not chunk:
            break
        chunks.append(chunk)
        if chunk[-1] == 0:
            break
    return b"".join(chunks)


def _recv_until_zero_and_decode(sock: socket.socket, encoding: str = "utf-8") -> str:
    data = _recv_until_zero(sock)
    return data.decode(encoding)


@pytest.fixture(scope="session")
def async_server():
    proc = start_server_process()
    _wait_for_port(SERVER_PORT_ASYNC)
    try:
        yield proc
    finally:
        _terminate_proc(proc)


def test_scheduler_call_soon():
    sched = scheduler.Scheduler()
    result = []

    sched.call_soon(lambda: result.append("called"))
    sched.run()
    assert result == ["called"]


def test_scheduler_call_later():
    sched = scheduler.Scheduler()
    result = []
    start_time = time.time()

    sched.call_later(0.1, lambda: result.append("called"))
    sched.run()

    end_time = time.time()
    assert result == ["called"]
    assert end_time - start_time >= 0.09


def test_scheduler_call_a_lot():
    sched = scheduler.Scheduler()
    result = []
    start_time = time.time()

    k = 100
    nums = [i for i in range(k)]
    random.shuffle(nums)

    for i in nums:
        sched.call_later(i * 0.05, lambda i=i: result.append(f"called {i}"))
    sched.run()

    end_time = time.time()
    assert result == [f"called {i}" for i in range(k)]
    assert end_time - start_time >= 4.5


def test_scheduler_stability_k_tasks():
    sched = scheduler.Scheduler()
    execution_order = []

    k = 20
    for i in range(k):
        sched.call_later(0.1, lambda i=i: execution_order.append(f"called {i}"))

    sched.run()
    expected_order = [f"called {i}" for i in range(k)]
    assert execution_order == expected_order


def test_basic_echo(async_server):
    message = "Hello, echo server!\0"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("127.0.0.1", SERVER_PORT_ASYNC))
        sock.sendall(message.encode("utf-8"))

        response = _recv_until_zero_and_decode(sock)
        print(f"test_basic_echo: {response!r}")

    assert response[::-1] == message


def test_large_message(async_server):
    large_message = "abcdefghijklmnopqrstvwxyz" * 100
    full_message = large_message + "\0"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as father, \
         socket.socket(socket.AF_INET, socket.SOCK_STREAM) as child:

        father.settimeout(2.0)
        child.settimeout(2.0)

        father.connect(("127.0.0.1", SERVER_PORT_ASYNC))
        child.connect(("127.0.0.1", SERVER_PORT_ASYNC))

        half = len(full_message) // 2

        first_half = full_message[:half]
        father.sendall(first_half.encode("utf-8"))

        time.sleep(0.05)

        child.sendall(full_message.encode("utf-8"))
        child_response = _recv_until_zero_and_decode(child)
        print(f"child_response len = {len(child_response)}")
        assert child_response[::-1] == full_message

        second_half = full_message[half:]
        father.sendall(second_half.encode("utf-8"))

        father_response = _recv_until_zero_and_decode(father)
        print(f"father_response len = {len(father_response)}")
        assert father_response[::-1] == full_message


def test_client_disconnects_early(async_server):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("127.0.0.1", SERVER_PORT_ASYNC))
    time.sleep(0.1)
    assert True


def test_empty_message(async_server):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("127.0.0.1", SERVER_PORT_ASYNC))
        sock.sendall(b"")
        sock.settimeout(1.0)
        with pytest.raises(socket.timeout):
            _ = sock.recv(1024)


def test_unicode_message(async_server):
    unicode_message = "абоба/" * 14
    full_message = unicode_message + "\0"

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(("127.0.0.1", SERVER_PORT_ASYNC))
        sock.sendall(full_message.encode("utf-8"))

        response = _recv_until_zero_and_decode(sock)
        print(f"test_unicode_message: {response!r}")

    assert response[::-1] == full_message
