import sys
import time

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent / "src"))

from exots import Server


def ping():
    return "pong"


def echo(params):
    return params["msg"]


def add(params):
    return params["a"] + params["b"]


def sum(a, b):
    return a + b


def error_method():
    raise RuntimeError("Something went wrong")


def slow_method():
    time.sleep(0.1)
    return "done"


server = Server(
    {
        "ping": ping,
        "echo": echo,
        "add": add,
        "sum": sum,
        "error_method": error_method,
        "slow_method": slow_method,
    }
)

server.run(sys.argv)
