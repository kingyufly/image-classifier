import threading, telepot, queue, socket, base64, json
from time import sleep
from telepot.loop import MessageLoop
from urllib import request
from PIL import Image
from io import BytesIO
import os, sys


global q1, q2

#thread1 process the data from telegram
def handle(msg):
    content_type, chat_type, chat_id = telepot.glance(msg)
    
    #remove the downloaded image if any
    filename = 'recv'
    pngname = 'recv.png'
    if(os.path.exists(pngname)):
        os.remove(pngname)
    if(os.path.exists(pngname)):
        os.remove(pngname)
        
    if content_type == 'photo':
        bot.download_file(msg['photo'][-1]['file_id'],filename)
    elif content_type == 'text':
        url = msg["text"]
        request.urlretrieve(url,filename)
    
    #tansfer the image from jpeg to png if received jpeg image
    image = Image.open(filename)
    image.save(pngname)
    image = Image.open(pngname)
    
    q1.put(image)
    q1.put(chat_id)

#thread2 process the image and send to the server, received the data and send to thread3
def T2():
    while 1:
        while not q1.empty():
            image = q1.get()
            chat_id = q1.get()
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            encoded_image = base64.b64encode(buffered.getvalue())
            soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            soc.connect(("localhost", 50002))

            data = {"image":str(encoded_image, encoding = "utf-8"), "chat_id":chat_id}
            soc.send(json.dumps(data).replace("\'", "\"").encode("utf-8"))
            recv_data = soc.recv(1024)
            soc.close()
            q2.put(recv_data)

#htread3 process the json and send to client
def T3():
    while 1:
        while not q2.empty():
            recv_data = q2.get()
            data = json.loads(recv_data.decode("utf-8"))
            predictions = data["predictions"]
            chat_id = data["chat_id"]
            
            reply = ""
            i = 1
            for prediction in predictions:
                reply += str(i) + ". " + prediction["label"] + " (" + prediction["proba"] + ")\n"
                i += 1
            bot.sendMessage(chat_id, reply)
            
threads = []
t2 = threading.Thread(target=T2)
threads.append(t2)
t3 = threading.Thread(target=T3)
threads.append(t3)

if __name__ == '__main__':
    q1 = queue.Queue()
    q2 = queue.Queue()
    bot = telepot.Bot("624297124:AAFwTUglItjHaVoqMkfj39sI5WhU66PxPMo")
    MessageLoop(bot, handle).run_as_thread()
    for t in threads:
        t.setDaemon(True)
        t.start()
        

