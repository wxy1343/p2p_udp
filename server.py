import os
import socket
from threading import Thread, Lock

lock = Lock()
s = socket.socket()
client_list = []
p2p_addr_dict = {}
writable = False


def listening():
    def get_udp_addr(addr):
        for addr_client_tcp, addr_client_udp in p2p_addr_dict.items():
            if addr == addr_client_tcp:
                return addr_client_udp

    def close(c, src, port):
        try:
            c.close()
            client_list.remove(c)
            print(f'{src}:{port} 已关闭')
        except ValueError:
            pass

    def client_handle(c):
        addr_client_tcp = c.getpeername()
        src_client_tcp, port_client_tcp = addr_client_tcp
        while True:
            try:
                data = c.recv(1024).decode()
            except:
                close(c, src_client_tcp, port_client_tcp)
                return
            if data == 'exit':
                close(c, src_client_tcp, port_client_tcp)
            if data != '':
                l = []
                try:
                    t = type(eval(data))
                except (NameError, TypeError):
                    t = None
                if data == 'get_p2p_addr':
                    with lock:
                        for client in client_list:
                            if c != client:
                                try:
                                    addr_client_udp = get_udp_addr(client.getpeername())
                                except:
                                    close(c, src_client_tcp, port_client_tcp)
                                    return
                                if addr_client_udp and addr_client_udp not in l:
                                    l.append(addr_client_udp)
                    try:
                        c.send(str([addr_client_tcp, l]).encode())
                    except:
                        close(c, src_client_tcp, port_client_tcp)
                        return
                elif t is tuple:
                    data = eval(data)
                    if data in p2p_addr_dict.values():
                        addr_p2p_udp = data
                        src, port = addr_p2p_udp
                        addr_client_udp = get_udp_addr(addr_client_tcp)
                        src_client_udp, src_client_port = addr_client_udp
                        print(f'{src_client_udp}:{src_client_port} 请求连接 {src}:{port}')
                        for client in client_list:
                            if client != c:
                                try:
                                    if get_udp_addr(client.getpeername()) == addr_p2p_udp:
                                        client.send(str(addr_client_udp).encode())
                                except:
                                    close(c, src_client_tcp, port_client_tcp)
                                    return

    s.bind(('0.0.0.0', 1234))
    s.listen(5)
    while True:
        c, addr = s.accept()
        src, port = addr
        print(f'{src}:{port} 已连接')
        if c not in client_list:
            client_list.append(c)
            Thread(target=client_handle, args=(c,)).start()


def p2p():
    addr_client_tcp = ()
    s_p2p = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s_p2p.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s_p2p.bind(('', 4321))
    while True:
        data, addr_client_udp = s_p2p.recvfrom(1024)
        src, port = addr_client_udp
        if writable:
            print(f'收到 {src}:{port} 的udp连接 -> {data}')
        data = data.decode()
        try:
            t = type(eval(data))
        except (NameError, TypeError):
            t = None
        if t is tuple:
            addr_client_tcp = eval(data)
        with lock:
            p2p_addr_dict[addr_client_tcp] = addr_client_udp


def close():
    for client in client_list:
        client.close()


Thread(target=listening).start()
Thread(target=p2p).start()
while True:
    try:
        text = input()
    except KeyboardInterrupt:
        print('关闭连接')
        close()
        s.close()
        os._exit(2)
    if text == 'close':
        close()
    elif text == 'ls':
        for client in client_list:
            print(client.getpeername())
    elif text == 'info':
        writable = True
        while True:
            try:
                input()
            except:
                writable = False
                break
