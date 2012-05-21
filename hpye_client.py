import socket

# constants
HOST = 'localhost'
PORT = 4793

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
    s.sendall('hi')
    s.close()
    print 'done'

main()
