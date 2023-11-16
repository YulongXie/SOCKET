#!/usr/bin/python
# coding: utf-8
import datetime
import os
import socket
import struct
import sys
import json
import uuid
import hashlib

output = sys.stdout
parentpath = ''
current_os_platform = sys.platform
if current_os_platform == 'darwin':
    HomePath = os.environ["HOME"]
    parentpath = HomePath + '/Desktop/Report/Socket/'

if not os.path.exists(parentpath):
    os.makedirs(parentpath)
    print(parentpath)

if parentpath == '':
    sys.exit(1)


# from threading import Thread,current_thread

def get_uuid():
    get_timestamp_uuid = str(uuid.uuid4()).upper()  # 根据 时间戳生成 uuid , 保证全球唯一
    return get_timestamp_uuid


def get_file_md5(file_name):
    """
    计算文件的md5
    :param file_name:
    :return:
    """
    m = hashlib.md5()  # 创建md5对象
    with open(file_name, 'rb') as fobj:
        while True:
            data = fobj.read(4096)
            if not data:
                break
            m.update(data)  # 更新md5对象
    return m.hexdigest()  # 返回md5对象


def dealwith_client_headers(sk_client, headers_client):
    header_client_json = json.dumps(headers_client)  # 报头信息(json字符串)
    header_client_json_bytes = bytes(header_client_json, encoding="utf-8")  # 报头信息(bytes类型)
    print("客户端发送报头 {} 至服务端 ，长度为 {}".format(header_client_json, len(header_client_json_bytes)))
    # print(header_client_json_bytes)
    # print(len(header_client_json_bytes))
    sk_client.send(struct.pack('i', len(header_client_json_bytes)))  # 先发送报头的长度
    sk_client.send(header_client_json_bytes)  # 再发送报头的内容


def dealwith_server_headers(sk_client):
    from_server_head_msg_len = sk_client.recv(4)  # 先接收报头的长度(bytes类型)
    # print(from_server_head_msg_len)
    from_server_head_msg_len = struct.unpack('i', from_server_head_msg_len)  # 解包(tuple类型)
    # print(from_server_head_msg_len)
    # print("Step 1 : 开始接收报头长度:", from_server_head_msg_len[0])  # 元组的第一个元素为报头的长度
    from_server_head_msg = sk_client.recv(from_server_head_msg_len[0])  # 接收报头信息
    from_server_head_msg = from_server_head_msg.decode("utf-8")  # 报头信息解码
    from_server_head_msg = json.loads(from_server_head_msg)  # 报头信息转化为dict类型
    header_server = from_server_head_msg
    header_server_len = from_server_head_msg_len[0]
    # print("客户端收到服务端报头 {} , 长度 {}".format(header_server, header_server_len))
    return header_server, header_server_len


def socket_client_put(sk_client, cmd, headers_client):
    # result = False
    try:
        file_path = cmd.split(' ')[1]
        if os.path.isfile(file_path):
            filename = os.path.basename(file_path)
            filesize = os.stat(file_path).st_size
            filemd5 = get_file_md5(file_path)
            headers_client['file_size'] = filesize
            headers_client['file_name'] = filename
            headers_client['method'] = 'put'
            headers_client['md5'] = filemd5
            # print(headers_client)
            dealwith_client_headers(sk_client, headers_client)
            # header_client_json = json.dumps(headers_client)  # 报头信息(json字符串)
            # header_client_json_bytes = bytes(header_client_json, encoding="utf-8")  # 报头信息(bytes类型)
            # print(header_client_json)
            # # print(header_client_json_bytes)
            # print(len(header_client_json_bytes))
            # sk_client.send(struct.pack('i', len(header_client_json_bytes)))  # 先发送报头的长度
            # sk_client.send(header_client_json_bytes)  # 再发送报头的内容
            # sk_client.sendall(all_data)  # 最后发送数据 --需要改写
            with open(file_path, 'rb') as fp:
                while True:
                    file_data = fp.read(1024)
                    if not file_data:
                        print('{0} file send over...'.format(file_path))
                        break
                    sk_client.send(file_data)
            last_message_from_server = sk_client.recv(1024).decode('utf-8')
            print(last_message_from_server)
    except Exception as e:
        print(e)


def socket_client_get(sk_client, cmd, headers_client):
    try:
        file_path = cmd.split(' ')[1]
        headers_client['file_path'] = file_path
        print(headers_client)
        header_client_json = json.dumps(headers_client)  # 报头信息(json字符串)
        header_client_json_bytes = bytes(header_client_json, encoding="utf-8")  # 报头信息(bytes类型)
        sk_client.send(struct.pack('i', len(header_client_json_bytes)))  # 先发送报头的长度
        sk_client.send(header_client_json_bytes)  # 再发送报头的内容
        # 开始接收数据
        # sk_client.sendall(all_data)  # 最后发送数据 --需要改写
        header_from_server, header_from_server_len = dealwith_server_headers(sk_client)
        print("客户端收到服务端报头 {} , 长度 {}".format(header_from_server, header_from_server_len))
        current_time = datetime.datetime.now().strftime('%Y-%m-%d_%H.%M.%S')
        file_name_from_server = header_from_server['file_name']
        # new_file_name = str(current_time + '_NEW_' + file_name_from_server).encode('utf-8')
        new_file_name = current_time + '_NEW_' + file_name_from_server
        print("new_file_name", new_file_name)
        # new_file_path = os.path.join(str.encode('./'), new_file_name)
        new_file_path = parentpath + '/' + new_file_name
        # print(header_from_server['file_size'])
        receive_filesize = header_from_server['file_size']
        recvd_size = 0
        with open(new_file_path, 'wb') as fp:
            while not recvd_size == receive_filesize:
                current_percent = (recvd_size / receive_filesize) * 100
                current_percent = round(current_percent, 0)
                if current_percent % 2 == 0:
                    output.write('\rcomplete percent ----->:{} %'.format(current_percent))
                    output.flush()
                if receive_filesize - recvd_size > 1024:
                    data = sk_client.recv(1024)
                    # print(data)
                    recvd_size += len(data)
                else:
                    data = sk_client.recv(receive_filesize - recvd_size)
                    recvd_size = receive_filesize
                # print(data)
                fp.write(data)
        fp.close()
        print("End receive From Server...\n")
        message_client_receive_done = "File {} Send to Client Successfully, " \
                                      "New File Name {}".format(file_name_from_server,
                                                                new_file_name)
        sk_client.send(message_client_receive_done.encode('utf-8'))
    except Exception as e:
        print(e)


def socket_client_exec(sk_client, cmd, headers_client):
    dealwith_client_headers(sk_client, headers_client)
    print('{} --> send from message: {}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], cmd))
    sk_client.send(cmd.encode("utf-8"))  # 向服务器发送转码后的信息
    print("Command {} 将执行 120s...".format(cmd))
    from_server_head_msg_len = sk_client.recv(4)  # 先接收报头的长度(bytes类型)
    # print(from_server_head_msg_len)
    from_server_head_msg_len = struct.unpack('i', from_server_head_msg_len)  # 解包(tuple类型)
    # print(from_server_head_msg_len)
    # print("Step 1 : 开始接收报头长度:", from_server_head_msg_len[0])  # 元组的第一个元素为报头的长度
    from_server_head_msg = sk_client.recv(from_server_head_msg_len[0])  # 接收报头信息
    from_server_head_msg = from_server_head_msg.decode("utf-8")  # 报头信息解码
    from_server_head_msg = json.loads(from_server_head_msg)  # 报头信息转化为dict类型
    print("客户端收到服务端报头 {} , 长度 {}".format(from_server_head_msg, from_server_head_msg_len[0]))
    # print("Step 2 : 开始接收报头", from_server_head_msg)
    if from_server_head_msg['data_size'] != 0:
        # print("服务端反馈内容 : ")
        print("V" * 50)
        from_server_real_msg = sk_client.recv(1024)  # 接收真正的数据
        from_server_real_len = len(from_server_real_msg)  # 获取一次接收数据的大小
        while from_server_head_msg['data_size'] > from_server_real_len:  # 判断数据是否接收完整
            from_server_real_msg += sk_client.recv(1024)  # 再次接收没接收完的数据
            from_server_real_len = len(from_server_real_msg)  # 再次统计已接收数据的大小
        print(from_server_real_msg.decode("utf-8"))
        print("^" * 50)
        print("服务端数据接收完成!!! :\n", )


def socket_client_main(sk_client, cmd):
    """
    method : put,get,exec
    """
    filesize, filename, filepath, cmd_method, filemd5, all_data = 0, None, None, 'exec', None, None
    headers_client = {
        "file_size": filesize,
        "file_name": filename,
        "fail_path": filepath,
        "method": cmd_method,
        "md5": filemd5}
    # print(headers_client)
    try:
        cmd_method = cmd.split(' ')[0]
        if cmd_method == "put":
            headers_client['method'] = 'put'
            socket_client_put(sk_client, cmd, headers_client)
        elif cmd_method == "get":
            headers_client['method'] = 'get'
            socket_client_get(sk_client, cmd, headers_client)
        else:
            socket_client_exec(sk_client, cmd, headers_client)
    except Exception as e:
        print(e)


def socket_client(serverip):
    # SERVER_IP = ('192.168.130.28', 9999)
    sk_client = socket.socket()  # 实例化Socket
    try:
        # sk_client.connect(('127.0.0.1', 9996)) #连接指定服务器 (需更改IP和port)
        sk_client.connect(serverip)  # 连接指定服务器 (需更改IP和port)
        server_cuurentpath = sk_client.recv(1024).decode('utf-8')
        print('server_cuurentPath : ', server_cuurentpath)
        current_uuid = get_uuid()
        while True:
            data = input(f"[{current_uuid}]:")  # 正常输入
            if data == 'quit':
                break
            if not data:
                continue
            socket_client_main(sk_client, data)
    except Exception as e:
        print(e)
    finally:
        sk_client.close()  # 关闭Socket连接
        sys.exit(0)


if __name__ == '__main__':
    # SERVER_IP = ('127.0.0.1', 8080)
    SERVER_IP = ('192.168.142.112', 8080)
    socket_client(SERVER_IP)
