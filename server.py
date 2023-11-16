#!/usr/bin/python
# coding: utf-8


from __future__ import print_function, absolute_import
import socket
import queue
import logging
from select import select
import sys,datetime,struct,threading,os
 
SERVER_IP = ('', 9999 ) #设定监听的端口
 
# 保存客户端发送过来的消息,将消息放入队列中
message_queue = {}
input_list = []
output_list = []
output = sys.stdout

def deal_data(conn, addr):
    # while True:
    print('Accept new connection from {0}'.format(addr))
    current_time = datetime.datetime.now().strftime('%Y-%m-%d %H.%M.%S')
    while True:
        fileinfo_size = struct.calcsize('128sq')  # linux 和 windows 互传 128sl 改为 128sq  机器位数不一样，一个32位一个64位
        buf = conn.recv(fileinfo_size)
        # print('收到的字节流：', buf, type(buf))
        if buf:
            # print(buf, type(buf))
            filename, filesize = struct.unpack('128sq', buf)
            fn = filename.strip(str.encode('\00'))
            new_filename = os.path.join(str.encode('./'),  str.encode(current_time) + str.encode('_new_') + fn)
            print('file new name is {0}, filesize if {1}'.format(new_filename, filesize))
            recvd_size = 0  # 定义已接收文件的大小
            with open(new_filename, 'wb') as fp:
                print("start receiving...")
                while not recvd_size == filesize:
                    current_percent = (recvd_size/filesize)*100
                    # current_percent = round(current_percent,2)
                    output.write('\rcomplete percent ----->:%.2f%%' % current_percent) 
                    output.flush()
                    # print("current_percent is {}".format(current_percent))
                    if filesize - recvd_size > 1024:
                        data = conn.recv(1024)
                        recvd_size += len(data)
                    else:
                        data = conn.recv(filesize - recvd_size)
                        recvd_size = filesize
                    fp.write(data)
            print("\nend receive...")
        # conn.close()
        break

 
if __name__ == "__main__":
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(SERVER_IP)
    server.listen(10)
    # 设置为非阻塞
    # server.setblocking(False)
 
    # 初始化将服务端加入监听列表
    input_list.append(server)
    print("sys stdout:")
    print(sys.stdout.fileno())
    print(sys.stdout)
    will_recive_data_flag = False
    while True:
        # 开始 select 监听,对input_list中的服务端server进行监听
        stdinput, stdoutput, stderr = select(input_list, output_list,
                                             input_list)
        # print("input_list")
        # print(input_list)        
        # 循环判断是否有客户端连接进来,当有客户端连接进来时select将触发
        for obj in stdinput:
            # 判断当前触发的是不是服务端对象, 当触发的对象是服务端对象时,说明有新客户端连接进来了
            if obj == server:
                # 接收客户端的连接, 获取客户端对象和客户端地址信息
                conn, addr = server.accept()
                message = "Client {0} connected! ".format(addr)
                print(message)
                logging.info(message)
                # 将客户端对象也加入到监听的列表中, 当客户端发送消息时 select 将触发
                input_list.append(conn)
                # 为连接的客户端单独创建一个消息队列，用来保存客户端发送的消息
                message_queue[conn] = queue.Queue() 
            else:
                # 由于客户端连接进来时服务端接收客户端连接请求，将客户端加入到了监听列表中(input_list)，客户端发送消息将触发
                # 所以判断是否是客户端对象触发
                try:
                    # 客户端未断开
                    if will_recive_data_flag == False:
                        # print("00002")
                        recv_data = obj.recv(1024)
                        if recv_data:
                            message = "{0} <-- received {1} from client {2}".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                                recv_data.decode(), addr)
                            logging.info(message)
                            print(message)
                            # 将收到的消息放入到各客户端的消息队列中
                            message_queue[obj].put(recv_data)
                            # 将回复操作放到output列表中，让select监听
                            if obj not in output_list:
                                output_list.append(obj)
                            # obj.send("I'm already got your message :-)".encode('utf-8')) #往回发送字符串"I'm already"
                            if recv_data.decode('utf-8').split(' ')[0] == 'put':
                                print("00000001")
                                will_recive_data_flag = True
                                break
                                # obj.send()
                            if recv_data.decode('utf-8') == "shutdown":
                                sys.exit(1)
                    else:
                        print("Will receive data struct")
                        # while True:
                        # # while will_recive_data_flag == True:
                        # # conn, addr = server.accept()
                        #     t = threading.Thread(target=deal_data, args=(conn, addr))
                        #     t.start()
                        deal_data(conn,addr)
                        will_recive_data_flag = False

                except ConnectionResetError:
                    # 客户端断开连接了，将客户端的监听从input列表中移除
                    input_list.remove(obj)
                    # 移除客户端对象的消息队列
                    del message_queue[obj]
                    error_message = "\n[input] Client  {0} disconnected".format(addr)
                    logging.error(error_message)
                    print(error_message) 
                    # 如果现在没有客户端请求,也没有客户端发送消息时，开始对发送消息列表进行处理，是否需要发送消息
        for sendobj in output_list:
            try:
                # 如果消息队列中有消息,从消息队列中获取要发送的消息
                if not message_queue[sendobj].empty():
                    # 从该客户端对象的消息队列中获取要发送的消息
                    send_data = message_queue[sendobj].get()
                    sendobj.sendall(send_data)
                else:
                    # 将监听移除等待下一次客户端发送消息
                    output_list.remove(sendobj)
 
            except ConnectionResetError:
                # 客户端连接断开了
                del message_queue[sendobj]
                output_list.remove(sendobj)
                error_message = "\n[output] Client  {0} disconnected".format(addr)
                logging.warning(error_message)
                print(error_message)




