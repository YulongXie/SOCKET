#!/usr/bin/python
# coding: utf-8
import socket,sys,time,random,datetime,os
import struct



def _deal_send_data(socCli,file_path):
    # 定义定义文件信息。128s表示文件名为128bytes长，l表示一个int或log文件类型，在此为文件大小
    fileinfo_size = struct.calcsize('128sq')
    # 定义文件头信息，包含文件名和文件大小
    fhead = struct.pack('128sq', bytes(os.path.basename(file_path).encode('utf-8')), os.stat(file_path).st_size)
    socCli.send(fhead)
    print('client filepath: {0}'.format(file_path))
    with open(file_path, 'rb') as fp:
        while True:
            file_data = fp.read(1024)
            if not file_data:
                print('{0} file send over...'.format(file_path))
                break
            socCli.send(file_data)       

def send_data(socCli,data):
    print("Got you")
    print('{} --> send from message: {}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],data))
    socCli.send(data.encode('utf-8'))
    reply = socCli.recv(1024) #接收回传信息
    print("i am here")
    if reply:
        print("{} <-- reply from server: {}\n".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],reply.decode("utf-8")))
        start_send_flag = True
        if start_send_flag == True:
            # time.sleep(2)     
            file_path = data.split(' ')[1]
            print("will send file {}".format(file_path))
            # socCli.send("data coming !!!!".encode('utf-8'))
            if os.path.exists(file_path) == True and os.path.isfile(file_path) == True:
                _deal_send_data(socCli,file_path)

def socket_client():
    socCli = socket.socket() #实例化Socket
    try:
        # socCli.connect(('192.168.169.131', 9999)) #连接指定服务器 (需更改IP和port)
        socCli.connect(('127.0.0.1', 9999)) #连接指定服务器 (需更改IP和port)
        while True:
            # time.sleep(0.1)
            # data = random.randint(1,10000)
            # data = str(data)
            # print(data)
            start_send_flag = False
            data = input("# 输入内容:") #正常输入
            if data == 'quit':
                socCli.close()
                sys.exit(0)
            elif data == '':
                data = input("# 输入内容:")
            elif data.split(' ')[0] == 'put':
                send_data(socCli,data)
            else:

                print('{} --> send from message: {}'.format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],data))
                socCli.send(data.encode("utf-8")) #向服务器发送转码后的信息
                reply = socCli.recv(1024) #接收回传信息
                if reply:
                    print("{} <-- reply from server: {}\n".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],reply.decode("utf-8")))
                    # print() #解码后输出
                if data == 'shutdown':
                    socCli.close()
                    sys.exit(0)
    except Exception as e:
        print(e)
    finally:
        socCli.close() #关闭Socket连接



if __name__ == '__main__':
    socket_client()

