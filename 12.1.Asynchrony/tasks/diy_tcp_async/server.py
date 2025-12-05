import sys
from socket import *

from scheduler import sched


SERVER_PORT_ASYNC = 30000


async def tcp_server_async(addr):
    """
    Asynchronous DIY TCP echo server.

    Expected behaviour:
        * socket(AF_INET, SOCK_STREAM)
        * set appropriate socket options:
            SO_REUSEPORT - for fast testing
            SO_REUSEADDR - for fast testing
        * bind to 'addr' and call listen(backlog).
        and read some data in the infinite loop (break in some place).
    """
    pass


async def echo_handler(sock):
    """
    Handle a single client connection (echo logic).

    Expected protocol:
        Check tests :)
    """
    pass


if __name__ == '__main__':
    sched.new_task(tcp_server_async(("0.0.0.0", SERVER_PORT_ASYNC)))
    sched.run()