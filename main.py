from socket import *
import os

# Set the port number for the server to listen on
server_port = 5698

server_socket = socket(AF_INET, SOCK_STREAM)  # Create a TCP socket
server_socket.bind(('', server_port))  # Bind the server
server_socket.listen(1)  # Listen for incoming connections
print('The server is ready to listen for requests.')

# Define a function to read files with debugging statements
def read_file(file_path):
    full_path = os.path.abspath(file_path)
    print(f"Attempting to read file: {full_path}")
    try:
        with open(file_path, 'rb') as file:
            return file.read()
    except FileNotFoundError:
        print(f"File not found: {full_path}")
        return None

# Define a function for error 404
def error_404_response(client_ip, client_port):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <title>Error 404</title>
    </head>
    <body>
        <h1>Error 404</h1>
        <p style="color:red;">The file is not found.</p>
        <p>Your IP Address: {client_ip}</p>
        <p>Your Port Number: {client_port}</p>
    </body>
    </html>
    """
    response_headers = "HTTP/1.1 404 Not Found\r\n"
    response_headers += "Content-Type: text/html\r\n"
    response_headers += f"Content-Length: {len(html_content.encode('utf-8'))}\r\n"
    response_headers += "\r\n"
    response = response_headers + html_content
    return response.encode('utf-8')

# Function to parse the query string
def parse_query_string(path):
    if '?' in path:
        path, query = path.split('?', 1)
        query_params = {}
        for param in query.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                query_params[key] = value
        return path, query_params
    else:
        return path, {}

# Main server loop
while True:
    connection_socket, client_addr = server_socket.accept()  # Accept the connection
    client_ip, client_port = client_addr  # Get the client's IP and port
    request = connection_socket.recv(1024).decode('utf-8')  # Receive the request
    print("Request:")
    print(request)  # Print the request to the terminal

    try:
        # Parse the HTTP request
        request_lines = request.splitlines()
        if not request_lines:
            connection_socket.close()
            continue  # Skip to the next loop iteration

        request_line = request_lines[0]  # Get the first line of the request
        method, path, _ = request_line.split()  # Extract method and path
        file_name = path[1:]  # Remove leading '/'

        # Parse query parameters
        file_name, query_params = parse_query_string(file_name)

        # Initialize variables
        response_headers = ""
        response_body = b""

        # Serve main_en.html for specific paths
        if file_name in ["", "en", "index.html", "main_en.html"]:
            content = read_file("main_en.html")
            if content:
                content_type = 'text/html'
                response_headers = "HTTP/1.1 200 OK\r\n"
                response_headers += f"Content-Type: {content_type}\r\n"
                response_headers += f"Content-Length: {len(content)}\r\n"
                response_headers += "\r\n"
                response_body = content
            else:
                response = error_404_response(client_ip, client_port)
        # Serve main_ar.html for Arabic requests
        elif file_name in ["ar", "main_ar.html"]:
            content = read_file("main_ar.html")
            if content:
                content_type = 'text/html; charset=utf-8'
                response_headers = "HTTP/1.1 200 OK\r\n"
                response_headers += f"Content-Type: {content_type}\r\n"
                response_headers += f"Content-Length: {len(content)}\r\n"
                response_headers += "\r\n"
                response_body = content
            else:
                response = error_404_response(client_ip, client_port)
        # Handle supporting_material_en.html with search functionality
        elif file_name == "supporting_material_en.html":
            if 'query' in query_params:
                search_term = query_params['query']
                # Check if the search term is an image or video
                if search_term.lower().endswith(('.png', '.jpg', '.jpeg', '.mp4', '.mov', '.avi')):
                    # Build the path to the file in the 'images' directory
                    file_path = os.path.join('images', search_term)
                    if os.path.exists(file_path):
                        # Read the supporting_material_en.html content
                        html_content = read_file('supporting_material_en.html').decode('utf-8')
                        # Determine the HTML to embed based on file type
                        if search_term.lower().endswith(('.png', '.jpg', '.jpeg')):
                            media_html = f'<div class="result"><img src="/{file_path}" alt="{search_term}"></div>'
                        elif search_term.lower().endswith(('.mp4', '.mov', '.avi')):
                            media_html = f'''
                            <div class="result">
                                <video controls>
                                    <source src="/{file_path}" type="video/mp4">
                                    Your browser does not support the video.
                                </video>
                            </div>
                            '''
                        else:
                            media_html = ''
                        # Inject the media_html into the placeholder
                        modified_html = html_content.replace('<!-- Placeholder for the result -->', media_html)
                        response_body = modified_html.encode('utf-8')
                        content_type = 'text/html'
                        response_headers = "HTTP/1.1 200 OK\r\n"
                        response_headers += f"Content-Type: {content_type}\r\n"
                        response_headers += f"Content-Length: {len(response_body)}\r\n"
                        response_headers += "\r\n"
                    else:
                        print(f"File not found for search term: {file_path}")
                        # Redirect to external search if file not found locally
                        if search_term.lower().endswith(('.png', '.jpg', '.jpeg')):
                            redirect_url = f"https://www.google.com/search?tbm=isch&q={search_term}"
                        else:
                            redirect_url = f"https://www.youtube.com/results?search_query={search_term}"
                        response_headers = "HTTP/1.1 307 Temporary Redirect\r\n"
                        response_headers += f"Location: {redirect_url}\r\n"
                        response_headers += "\r\n"
                        response_body = b""
                else:
                    print(f"Unsupported file type or no file extension for search term: {search_term}")
                    # Unsupported file type or no file extension
                    response = error_404_response(client_ip, client_port)
            else:
                # Serve supporting_material_en.html
                content = read_file(file_name)
                if content:
                    content_type = 'text/html'
                    response_headers = "HTTP/1.1 200 OK\r\n"
                    response_headers += f"Content-Type: {content_type}\r\n"
                    response_headers += f"Content-Length: {len(content)}\r\n"
                    response_headers += "\r\n"
                    response_body = content
                else:
                    response = error_404_response(client_ip, client_port)
        # Handle supporting_material_ar.html with search functionality
        elif file_name == "supporting_material_ar.html":
            if 'query' in query_params:
                search_term = query_params['query']
                # Check if the search term is an image or video
                if search_term.lower().endswith(('.png', '.jpg', '.jpeg', '.mp4', '.mov', '.avi')):
                    # Build the path to the file in the 'images' directory
                    file_path = os.path.join('images', search_term)
                    if os.path.exists(file_path):
                        # Read the supporting_material_ar.html content
                        html_content = read_file('supporting_material_ar.html').decode('utf-8')
                        # Determine the HTML to embed based on file type
                        if search_term.lower().endswith(('.png', '.jpg', '.jpeg')):
                            media_html = f'<div class="result"><img src="/{file_path}" alt="{search_term}"></div>'
                        elif search_term.lower().endswith(('.mp4', '.mov', '.avi')):
                            media_html = f'''
                            <div class="result">
                                <video controls>
                                    <source src="/{file_path}" type="video/mp4">
                                    متصفحك لا يدعم عنصر الفيديو.
                                </video>
                            </div>
                            '''
                        else:
                            media_html = ''
                        # Inject the media_html into the placeholder
                        modified_html = html_content.replace('<!-- Placeholder for the result -->', media_html)
                        response_body = modified_html.encode('utf-8')
                        content_type = 'text/html; charset=utf-8'
                        response_headers = "HTTP/1.1 200 OK\r\n"
                        response_headers += f"Content-Type: {content_type}\r\n"
                        response_headers += f"Content-Length: {len(response_body)}\r\n"
                        response_headers += "\r\n"
                    else:
                        print(f"File not found for search term: {file_path}")
                        # Redirect to external search if file not found locally
                        if search_term.lower().endswith(('.png', '.jpg', '.jpeg')):
                            redirect_url = f"https://www.google.com/search?tbm=isch&q={search_term}"
                        else:
                            redirect_url = f"https://www.youtube.com/results?search_query={search_term}"
                        response_headers = "HTTP/1.1 307 Temporary Redirect\r\n"
                        response_headers += f"Location: {redirect_url}\r\n"
                        response_headers += "\r\n"
                        response_body = b""
                else:
                    print(f"Unsupported file type or no file extension for search term: {search_term}")
                    # Unsupported file type or no file extension
                    response = error_404_response(client_ip, client_port)
            else:
                # Serve supporting_material_ar.html
                content = read_file(file_name)
                if content:
                    content_type = 'text/html; charset=utf-8'
                    response_headers = "HTTP/1.1 200 OK\r\n"
                    response_headers += f"Content-Type: {content_type}\r\n"
                    response_headers += f"Content-Length: {len(content)}\r\n"
                    response_headers += "\r\n"
                    response_body = content
                else:
                    response = error_404_response(client_ip, client_port)
        # Serve other files based on their content type
        else:
            if os.path.exists(file_name):
                content = read_file(file_name)
                if content:
                    # Determine the content type
                    if file_name.lower().endswith('.html'):
                        content_type = 'text/html'
                    elif file_name.lower().endswith('.css'):
                        content_type = 'text/css'
                    elif file_name.lower().endswith('.png'):
                        content_type = 'image/png'
                    elif file_name.lower().endswith(('.jpg', '.jpeg')):
                        content_type = 'image/jpeg'
                    elif file_name.lower().endswith('.mp4'):
                        content_type = 'video/mp4'
                    elif file_name.lower().endswith('.mov'):
                        content_type = 'video/quicktime'
                    elif file_name.lower().endswith('.avi'):
                        content_type = 'video/x-msvideo'
                    else:
                        content_type = 'application/octet-stream'
                    response_headers = "HTTP/1.1 200 OK\r\n"
                    response_headers += f"Content-Type: {content_type}\r\n"
                    response_headers += f"Content-Length: {len(content)}\r\n"
                    response_headers += "\r\n"
                    response_body = content
                else:
                    print(f"File not found or cannot read: {file_name}")
                    response = error_404_response(client_ip, client_port)
            else:
                print(f"File does not exist: {file_name}")
                response = error_404_response(client_ip, client_port)

        # Send the response
        if 'response' in locals():
            # If 'response' variable is defined (e.g., error response)
            print("Response:")
            # Decode response and print headers only
            decoded_response = response.decode('utf-8', errors='replace')
            headers, _, _ = decoded_response.partition('\r\n\r\n')
            print(headers)
            connection_socket.sendall(response)
            del response  # Remove 'response' from locals
        else:
            # Build the full response
            full_response = response_headers.encode('utf-8') + response_body
            print("Response:")
            print(response_headers)
            connection_socket.sendall(full_response)
    except Exception as e:
        print(f"Error: {e}")
        # Send a 404 error response if an exception occurs
        response = error_404_response(client_ip, client_port)
        print("Response:")
        # Decode response and print headers only
        decoded_response = response.decode('utf-8', errors='replace')
        headers, _, _ = decoded_response.partition('\r\n\r\n')
        print(headers)
        connection_socket.sendall(response)

    # Close the connection
    connection_socket.close()