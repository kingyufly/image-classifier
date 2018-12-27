import numpy as np
import socket, base64, json, queue, threading
from keras.applications.resnet50 import ResNet50, preprocess_input, decode_predictions
from keras.preprocessing import image

global q
model = None

def T():
    # load the model
    global model
    if model == None:
        model = ResNet50(weights="imagenet", input_shape=(224,224,3))
    while 1:  
        while not q.empty():
            client_socket = q.get()
            recv_data = bytes()

            # receive data
            while 1:
                tmp = client_socket.recv(1024)
                if len(tmp) != 1024:
                    recv_data += tmp
                    break
                else:
                    recv_data += tmp

            data = json.loads(recv_data.decode("utf-8"))
            encoded_image = bytes(data["image"], encoding = "utf-8")
            chat_id = data["chat_id"]
            image_data = base64.b64decode(encoded_image)
            with open('recv.png', 'wb') as outfile:
                outfile.write(image_data)

            # prepare the image
            img = image.load_img("recv.png", target_size=(224, 224))
            x = image.img_to_array(img)
            x = np.expand_dims(x, axis=0)
            x = preprocess_input(x)

            # make prediction
            preds = model.predict(x)

            # process the output
            P = decode_predictions(preds, top=5)[0]
            data = []
            for (i, (imagenetID, label, proba)) in enumerate(P):
                one = {"label":label,"proba":str(round(proba,4))}
                data.append(one)
            send_data = {"predictions":data, "chat_id":chat_id}

            # send back the data
            client_socket.sendall(json.dumps(send_data).encode("utf-8"))

            client_socket.close()

t = threading.Thread(target=T)

if __name__ == '__main__':
    
    # listen to port 50001
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("localhost", 50002))
    server_socket.listen(10)
    
    q = queue.Queue()
    # process client requests
    while 1:
        (client_socket, address) = server_socket.accept()
        q.put(client_socket)

        # check thread2 is run or not
        if not t.isAlive():
            t.setDaemon(True)
            t.start()

