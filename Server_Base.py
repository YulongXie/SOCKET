#!/usr/bin/python
# coding: utf-8

# import gevent
# from gevent import monkey
# monkey.patch_all()
# from gevent import spawn
import sys
import datetime
import struct
import os
import socket
import subprocess
# import queue
# import logging
# import time


# import uuid
import hashlib
import json

from threading import Thread

CurDirPath = os.path.dirname(os.path.abspath(__file__))
print(CurDirPath)
output = sys.stdout
parentpath = ''
current_os_platform = sys.platform
print(current_os_platform)
if current_os_platform == 'darwin':
    HomePath = os.environ["HOME"]
    parentpath = HomePath + '/Desktop/Report/Socket/'

    print("OS Platform is darwin ,Server Run in MacOS")
if current_os_platform == 'linux':
    # parentpath = CurDirPath + '/Socket/'
    parentpath = '/sdcard/Documents/Socket/'
    print("OS Platform linux ,Server Run in Android(安卓)")

if not os.path.exists(parentpath):
    os.makedirs(parentpath)
    print(parentpath)

if parentpath == '':
    sys.exit(1)


def command(cmd):
    result = ''
    process = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, start_new_session=True)
    try:
        com_out, com_out_err = process.communicate(timeout=120)
        if com_out.decode('utf-8') == '' and com_out_err.decode('utf-8') == '':
            result = "Command {} Response is None , or {} no response during 30 seconds " \
                     "please check command is right or not".format(cmd, cmd)
        else:
            result = com_out.decode('utf-8') + com_out_err.decode('utf-8')
    except Exception as e:
        result = str(e)
    finally:
        process.kill()
        return result


# def get_uuid():
#     get_timestamp_uuid = str(uuid.uuid4()).upper()  # 根据 时间戳生成 uuid , 保证全球唯一
#     return get_timestamp_uuid


def get_file_md5(file_name):
    """
    计算文件的md5
    :param file_name:
    :return:
    """
    m = hashlib.md5()  # 创建md5对象
    with open(file_name, 'rb') as fn:
        while True:
            data = fn.read(4096)
            if not data:
                break
            m.update(data)  # 更新md5对象
    return m.hexdigest()  # 返回md5对象


def dealwith_server_headers(conn, headers_client):
    header_client_json = json.dumps(headers_client)  # 报头信息(json字符串)
    header_client_json_bytes = bytes(header_client_json, encoding="utf-8")  # 报头信息(bytes类型)
    print("服务端发送报头 {} 至客户端 ，长度为 {}".format(header_client_json, len(header_client_json_bytes)))
    # print(header_client_json_bytes)
    # print(len(header_client_json_bytes))
    conn.send(struct.pack('i', len(header_client_json_bytes)))  # 先发送报头的长度
    conn.send(header_client_json_bytes)  # 再发送报头的内容


def socket_server_send(conn, headers_server):
    headers_sendtoclient = {
        'file_size': 0,
        'file_name': None,
        'md5': 0}
    # filepath = headers_server[]
    print(headers_server)
    client_want_to_get_filepath = headers_server['file_path']
    print(client_want_to_get_filepath)
    if os.path.isfile(client_want_to_get_filepath):
        print("文件存在，开始发生报头信息")
        client_want_to_get_filename = os.path.basename(client_want_to_get_filepath)
        client_want_to_get_filesize = os.stat(client_want_to_get_filepath).st_size
        client_want_to_get_filemd5 = get_file_md5(client_want_to_get_filepath)
        headers_sendtoclient['file_name'] = client_want_to_get_filename
        headers_sendtoclient['file_size'] = client_want_to_get_filesize
        headers_sendtoclient['md5'] = client_want_to_get_filemd5
        dealwith_server_headers(conn, headers_sendtoclient)
        print("报头信息发送完成，开始发送数据")
        try:
            with open(client_want_to_get_filepath, 'rb') as fp:
                while True:
                    send_file_data = fp.read(1024)
                    # print(send_file_data)
                    if not send_file_data:
                        print('{0} file send over...'.format(client_want_to_get_filepath))
                        break
                    conn.send(send_file_data)
            last_message_from_client = conn.recv(1024).decode('utf-8')
            print(last_message_from_client)
        except Exception as e:
            print(e)
    else:
        print("文件不存在")
        message_info = "No Such File or Path -> {} ".format(client_want_to_get_filepath)
        conn.send(message_info.encode('utf-8'))

    # conn.close()


def socket_server_recv(conn, headers_server):
    print("开始接收数据，数据大小为:", headers_server['file_size'], ' Size')
    current_time = datetime.datetime.now().strftime('%Y-%m-%d')
    file_name_from_client = headers_server['file_name']
    file_size_from_client = headers_server['file_size']
    # new_file_name = str(current_time + '_NEW_' + file_name_from_client).encode('utf-8')
    new_file_name = '/' + file_name_from_client
    # print(new_file_name)
    # new_file_path = os.path.join(str.encode('./'), new_file_name)
    new_file_path = parentpath + str(current_time)
    if not os.path.exists(new_file_path):
        os.makedirs(new_file_path)
    # print(new_file_path.decode('utf-8'))
    full_file_path = new_file_path + new_file_name
    print(full_file_path)
    recvd_size = 0
    try:
        with open(full_file_path, 'wb') as fp:
            while not recvd_size == file_size_from_client:
                current_percent = (recvd_size / file_size_from_client) * 100
                current_percent = round(current_percent, 0)
                if current_percent % 2 ==0:
                    output.write('\rcomplete percent ----->:{} %'.format(current_percent))
                    output.flush()
                if file_size_from_client - recvd_size > 1024:
                    data = conn.recv(1024)
                    recvd_size += len(data)
                else:
                    data = conn.recv(file_size_from_client - recvd_size)
                    recvd_size = file_size_from_client
                # print(data)
                fp.write(data)
        fp.close()
        print("\nend receive...")
        message_server_recive_done = "File {} Upload to Server Successfully, " \
                                     "New File Name {}".format(file_name_from_client,
                                                               new_file_name)
        print(message_server_recive_done)
        conn.send(message_server_recive_done.encode('utf-8'))
    except OSError as e:
        conn.send(str(e).encode('utf-8'))


def socket_server_exec(conn, addr):
    """执行命令cmd，返回命令输出的内容。
    如果超时将会抛出TimeoutError异常。
    cmd - 要执行的命令
    timeout - 最长等待时间，单位：秒
    """
    # print("开始 exec")
    cmd = conn.recv(1024).decode('utf-8')
    print('cmd:', cmd)
    cmd_result = command(cmd)
    print('cmd_result : ', cmd_result)
    cmd_result_len = len(cmd_result)  # 数据的长度
    headers = {"data_size": cmd_result_len}  # 报头信息(dict类型)
    if cmd_result_len != 0:
        # print("将开始发送 {} size 数据到 客户端{}".format(cmd_result_len, addr))
        header_json = json.dumps(headers)  # 报头信息(json字符串)
        # print(header_json)
        header_json_bytes = bytes(header_json, encoding="utf-8")  # 报头信息(bytes类型)
        conn.send(struct.pack('i', len(header_json_bytes)))  # 先发送报头的长度
        conn.send(header_json_bytes)  # 再发送报头的内容
        print("{} 1.服务端发送报头 {} ,长度 {}至客户端 {}".format(
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], header_json, len(header_json_bytes), addr))
        print("{} 2.报头通讯完成，服务端发送大小为 {} Size 数据至客户端 {}".format(
                            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], cmd_result_len, addr))
        conn.sendall(cmd_result.encode('utf-8'))  # 最后发送数据
        conn.sendall()
        print("{} 3.服务端处理完成".format(
                            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]))


def comm(conn, addr):
    comm_first_message = 'Server CurDirPath is {}, File Storage Path is {} '.format(CurDirPath, parentpath)
    conn.send(comm_first_message.encode('utf-8'))
    # headers_server = {"file_size": 0, "file_name": None, "method": None, "md5": None}
    while True:
        try:
            # 客户端未断开连接了
            server_recv_head_msg_len = conn.recv(4)  # 先接收报头的长度(bytes类型)
            if not server_recv_head_msg_len:
                break
            print("Server Step 1 : 报头长度:", server_recv_head_msg_len[0])  # 元组的第一个元素为报头的长度
            server_recv_head_msg_len = struct.unpack('i', server_recv_head_msg_len)  # 解包(tuple类型)
            server_recv_head_msg = conn.recv(server_recv_head_msg_len[0])  # 接收报头信息
            server_recv_head_msg = server_recv_head_msg.decode("utf-8")  # 报头信息解码
            server_recv_head_msg = json.loads(server_recv_head_msg)  # 报头信息转化为dict类型
            # print("Server Step 2 : 报头内容:", server_recv_head_msg)  # 元组的第一个元素为报头的长度
            print("客户端上传报头 {}, 报头长度 {}".format(server_recv_head_msg, server_recv_head_msg_len[0]))
            if server_recv_head_msg['method'] == 'put':
                print("客户端将上传文件至服务端")

                socket_server_recv(conn, server_recv_head_msg)
            if server_recv_head_msg['method'] == 'get':
                print("客户端从服务端下载文件")
                socket_server_send(conn, server_recv_head_msg)
            if server_recv_head_msg['method'] == 'exec':
                print("客户端需要在服务端运行command")
                socket_server_exec(conn, addr)
        except ConnectionResetError:
            # 客户端断开连接了
            error_message = "\n[input] Client  {0} disconnected".format(addr)
            print(error_message)
        # except ConnectionAbortedError:
        #     # 客户端断开连接了
        #     error_message = "\n[input] Client  {0} Software Caused Connection abort".format(addr)
        #     print(error_message)
        except Exception as e:
            error_message = '\n[input] Client  {0} {1}'.format(addr, e)
            print(error_message)
    # conn.close()


def run(ip, port):
    server = socket.socket()
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((ip, port))
    server.listen(5)
    while True:
        conn, addr = server.accept()
        message = "Client {0} connected! ".format(addr)
        print(message)
        Thread(target=comm, args=(conn, addr,)).start()
        # spawn(comm,conn,addr)


if __name__ == '__main__':
    run('', 8080)
    # g = spawn(run,'', 9994)
    # g.join()
