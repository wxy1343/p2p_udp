import ctypes
import inspect
import socket
import time
import os
from queue import Queue
from threading import Thread, Lock

q = Queue(maxsize=0)
q_p2p = Queue(maxsize=0)
lock = Lock()
p2p_addr_list = []
s = socket.socket()
s_p2p = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
p2p_dict = {}
my_tcp_addr = ()
server_ip = 'www.wxy1343.xyz'
# server_ip = '127.0.0.1'
tcp = 1234
udp = 4321


def client():
    global p2p_addr_list
    global p2p_connect
    global my_tcp_addr
    try:
        s.connect((server_ip, tcp))
    except:
        print('\n连接服务器失败')
        os._exit(0)
    while True:
        try:
            s.send(b'get_p2p_addr')
            data = s.recv(1024).decode()
        except:
            s.close()
            os._exit(0)
        try:
            t = type(eval(data))
        except:
            t = None
        if t is list:
            data = eval(data)
            my_tcp_addr = data[0]
            with lock:
                p2p_addr_list = data[1]
        elif t is tuple:
            data = eval(data)
            src, port = data
            print(f'\n收到来自 {src}:{port} 的p2p请求')
            print('输入 accept 接收请求\n-> ', end='')
            if data in p2p_addr_list:
                q.put(data)
        time.sleep(1)


def monitor_input():
    global t_p2p
    while True:
        text = input('-> ')
        if text == 'exit':
            s.close()
            os._exit(0)
        elif text == 'accept':
            if q.qsize() == 0:
                print('当前没有请求')
                continue
            data = q.get()
            if type(data) is tuple:
                addr_p2p_udp = data
                src, port = addr_p2p_udp
                print(f'收到来自 {src}:{port} 的请求连接')
                print(f'正在发送数据包至 -> {src}:{port}')
                t_p2p = Thread(target=p2p, args=(src, port))
                t_p2p.start()
                print('正在等待对方回应...')
                data, addr = s_p2p.recvfrom(1024)
                src, port = addr
                print(f'收到来自 {src}:{port} 的回应')
                print('p2p建立成功')
                with lock:
                    p2p_dict[s_p2p.getsockname()] = addr
            q.task_done()
        elif text == 'ls':
            for addr_p2p_udp in p2p_addr_list:
                src, port = addr_p2p_udp
                print(f'{src}:{port}')
        elif text == 'connect':
            if len(p2p_addr_list) != 0:
                for i, addr_p2p_udp in enumerate(p2p_addr_list):
                    src, port = addr_p2p_udp
                    print(f'{i} -> {src}:{port}')
                text = input('请输入序号：')
                try:
                    t = type(eval(text))
                except:
                    t = None
                if t is int:
                    n = int(text)
                    if n < len(p2p_addr_list):
                        with lock:
                            addr_p2p_udp = p2p_addr_list[n]
                        src, port = addr_p2p_udp
                        print(f'发送连接请求 -> {src}:{port}')
                        try:
                            s.send(str(addr_p2p_udp).encode())
                        except:
                            print('连接已关闭')
                            s.close()
                            os._exit(0)
                        print(f'正在发送数据包至 -> {src}:{port}')
                        t_p2p = Thread(target=p2p, args=(src, port))
                        t_p2p.start()
                        print('正在等待对方建立p2p...')
                        try:
                            data, addr = s_p2p.recvfrom(1024)
                        except:
                            print('连接已关闭')
                            return
                        src, port = addr
                        print(f'收到来自 {src}:{port} 的回应')
                        print('p2p建立成功')
                        t_p2p = Thread(target=p2p, args=addr)
                        t_p2p.start()
                        with lock:
                            p2p_dict[s_p2p.getsockname()] = addr
                    else:
                        print('发送连接请求失败')
            else:
                print('没有可连接设备')
        elif text == 'chat':
            for i, addr in enumerate(p2p_dict.items()):
                addr_client, addr_p2p_udp = addr
                src_client, port_client = addr_client
                src_p2p, port_p2p = addr_p2p_udp
                print(f'{i} -> {src_client}:{port_client} -> {src_p2p}:{port_p2p}')
            while True:
                text = input('请输入序号：')
                try:
                    n = int(text)
                    if n < len(p2p_dict):
                        addr = list(p2p_dict.items())[n]
                        break
                except:
                    pass
            t = Thread(target=chat, args=(s_p2p, addr[1]))
            t.start()
            t.join()


def chat(s_p2p, addr):
    print(s_p2p)

    def recv():
        while True:
            try:
                data, addr = s_p2p.recvfrom(1024)
            except:
                return
            data = data.decode()
            try:
                t = type(eval(data))
            except:
                t = None
            if not t is tuple:
                print(data)

    t = Thread(target=recv)
    t.setDaemon(True)
    t.start()
    while True:
        text = input()
        if text == 'exit':
            return
        s_p2p.sendto(text.encode(), addr)


def stop_thread(thread, timeout=0, exctype=SystemExit):
    time.sleep(timeout)
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(thread.ident)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def p2p(src, port):
    data = 'p2p'
    while True:
        if my_tcp_addr:
            data = str(my_tcp_addr)
        if my_tcp_addr != ():
            try:
                s_p2p.sendto(data.encode(), (src, port))
            except:
                pass
        time.sleep(1)


Thread(target=client).start()
Thread(target=monitor_input).start()
Thread(target=p2p, args=(server_ip, udp)).start()
