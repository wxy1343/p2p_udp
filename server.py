import socket
from threading import Thread, Lock

lock = Lock()
client_list = []
p2p_addr_dict = {}


def listening():
    def get_udp_addr(addr):
        for addr_client_tcp, addr_client_udp in p2p_addr_dict.items():
            if addr == addr_client_tcp:
                return addr_client_udp

    def client_handle(c):
        addr_client_tcp = c.getpeername()
        src_client_tcp, port_client_tcp = addr_client_tcp
        while True:
            try:
                data = c.recv(1024).decode()
            except:
                client_list.remove(c)
                c.close()
                print(f'{src_client_tcp}:{port_client_tcp} 已关闭')
                return
            if data != '':
                l = []
                try:
                    t = type(eval(data))
                except:
                    t = None
                if data == 'get_p2p_addr':
                    with lock:
                        for client in client_list:
                            if c != client:
                                try:
                                    addr_client_udp = get_udp_addr(client.getpeername())
                                except:
                                    client_list.remove(c)
                                    c.close()
                                    print(f'{src_client_tcp}:{port_client_tcp} 已关闭')
                                    return
                                if addr_client_udp and addr_client_udp not in l:
                                    l.append(addr_client_udp)
                    try:
                        c.send(str([addr_client_tcp, l]).encode())
                    except:
                        client_list.remove(c)
                        c.close()
                        print(f'{src_client_tcp}:{port_client_tcp} 已关闭')
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
                                    client_list.remove(c)
                                    c.close()
                                    print(f'{src_client_tcp}:{port_client_tcp} 已关闭')
                                    return

    s = socket.socket()
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
    s_p2p.bind(('', 4321))
    while True:
        data, addr_client_udp = s_p2p.recvfrom(1024)
        src, port = addr_client_udp
        print(f'收到 {src}:{port} 的udp连接 -> {data}')
        data = data.decode()
        try:
            t = type(eval(data))
        except:
            t = None
        if t is tuple:
            addr_client_tcp = eval(data)
        with lock:
            p2p_addr_dict[addr_client_tcp] = addr_client_udp


Thread(target=listening).start()
Thread(target=p2p).start()
while True:
    text = input()
    if text == '':
        for client in client_list:
            client.close()
