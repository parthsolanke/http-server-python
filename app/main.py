import sys
import gzip
import socket
import threading

MAX_REQUEST_SIZE = 1024
HTTP_STATUS_OK = "200 OK"
HTTP_STATUS_CREATED = "201 Created"
HTTP_STATUS_NOT_FOUND = "404 Not Found"

class HTTPServer:
    def __init__(self, host="localhost", port=4221):
        self.server_socket = socket.create_server((host, port), reuse_port=True)
        print("Server started")

    def handle_client(self, client, addr):
        print(f"Connection from {addr}")

        request_data = client.recv(MAX_REQUEST_SIZE).decode().split("\r\n")
        if not request_data:
            print("No data received")
            return

        request_line = request_data[0].split(" ")
        request_method = request_line[0]
        request_path = request_line[1]
        request_headers = request_data[1:-2]
        request_body = request_data[-1]

        headers_dict = self.parse_headers(request_headers)

        response = self.route_request(request_method, request_path, request_body, headers_dict)
        client.send(response)
        print("Response sent")
        client.close()

    def parse_headers(self, headers):
        headers_dict = {}
        for header in headers:
            if ": " in header:
                key, value = header.split(": ", 1)
                headers_dict[key] = value
        return headers_dict

    def route_request(self, method, path, body, headers):
        if path.startswith("/echo/"):
            if method == "GET":
                return self.handle_get_echo(path, headers.get("Accept-Encoding", None))
            return self.handle_echo(path)
        elif path == "/user-agent":
            return self.handle_user_agent(headers)
        elif path.startswith("/files/"):
            if method == "GET":
                return self.handle_get_file(path)
            elif method == "POST":
                return self.handle_post_file(path, body)
        elif path == "/":
            return self.handle_root()
        else:
            return self.handle_not_found()
    
    def handle_get_echo(self, path, accept_encoding):
        response_body = path.split("/echo/")[1].encode()
        if accept_encoding and "gzip" in accept_encoding.split(", "):
            body = gzip.compress(response_body)
            headers = [
                f"HTTP/1.1 {HTTP_STATUS_OK}",
                "Content-Type: text/plain",
                "Content-Encoding: gzip",
                f"Content-Length: {len(body)}",
                "",
                ""
            ]
            return "\r\n".join(headers).encode() + body
        return self.build_response(HTTP_STATUS_OK, "text/plain", response_body)
    
    def handle_echo(self, path):
        response_body = path.split("/echo/")[1].encode()
        return self.build_response(HTTP_STATUS_OK, "text/plain", response_body)

    def handle_user_agent(self, headers):
        response_body = headers.get("User-Agent", "").encode()
        return self.build_response(HTTP_STATUS_OK, "text/plain", response_body)

    def handle_get_file(self, path):
        file_name = path.split("/files/")[1]
        file_path = f"{sys.argv[2]}/{file_name}"
        try:
            with open(file_path, "rb") as file:
                response_body = file.read()
                return self.build_response(HTTP_STATUS_OK, "application/octet-stream", response_body)
        except FileNotFoundError:
            print(f"File not found: {file_path}")
            return self.build_response(HTTP_STATUS_NOT_FOUND)

    def handle_post_file(self, path, body):
        file_name = path.split("/files/")[1]
        file_path = f"{sys.argv[2]}/{file_name}"
        with open(file_path, "wb") as file:
            file.write(body.encode())
            return self.build_response(HTTP_STATUS_CREATED)

    def handle_root(self):
        return f"HTTP/1.1 {HTTP_STATUS_OK}\r\n\r\n".encode()

    def handle_not_found(self):
        return f"HTTP/1.1 {HTTP_STATUS_NOT_FOUND}\r\n\r\n".encode()

    def build_response(self, status, content_type="text/plain", body=b""):
        headers = [
            f"HTTP/1.1 {status}",
            f"Content-Type: {content_type}",
            f"Content-Length: {len(body)}",
            "",
            ""
        ]
        return "\r\n".join(headers).encode() + body

    def start(self):
        try:
            with self.server_socket:
                while True:
                    client, addr = self.server_socket.accept()
                    threading.Thread(target=self.handle_client, args=(client, addr)).start()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.server_socket.close()

if __name__ == "__main__":
    server = HTTPServer()
    server.start()
