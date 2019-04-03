import argparse
import socket

from time import sleep

import cv2
import numpy as np

import utils

parser = argparse.ArgumentParser()

parser.add_argument('--host', type=str, help='The IP of the echo server', required=True)
parser.add_argument('--port', type=int, help='The port on which the server is listening', required=True)
parser.add_argument('--jpeg_quality', type=int, help='The JPEG quality for compressing the reply', default=50)

args = parser.parse_args()

host         = args.host
port         = args.port
jpeg_quality = args.jpeg_quality

cv2.namedWindow("Image")

keep_running = True

# A lambda function to get a cv2 image
# encoded as a JPEG compressed byte sequence
get_buffer = lambda: utils.encode_image(cv2.imread("monarch.png",cv2.IMREAD_UNCHANGED), jpeg_quality)

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.connect((host, port))
    while keep_running:

        # Grab and encode the image
        img_buffer = get_buffer()
        if img_buffer is None:
            continue

        # Prepare the message with the number of bytes going to be sent
        msg = bytes("image{:010}".format(len(img_buffer)), "ascii")
        sock.sendall(msg)

        # Send the buffer
        sock.sendall(img_buffer)
        # And a known handshake to ensure the sockets are in sync
        sock.sendall('done!'.encode('ascii'))

        # Read the reply command
        cmd = sock.recv(5).decode('ascii')
        if cmd != 'image':
            raise RuntimeError("Unexpected server reply")
        # Read the image buffer size
        img_size = int(sock.recv(10).decode('ascii'))

        # Read the image buffer
        img_reply_bytes = sock.recv(img_size)

        # Read the final handshake
        cmd = sock.recv(5).decode('ascii')
        if cmd != 'enod!':
            raise RuntimeError("Unexpected server reply. Expected 'enod!', got '{}'".format(cmd))

        # Transaction is done, we now process/display the received image
        img = utils.decode_image_buffer(img_reply_bytes)
        cv2.imshow("Image", img)
        keep_running = not(cv2.waitKey(1) & 0xFF == ord('q'))
    print("Closing the socket")

