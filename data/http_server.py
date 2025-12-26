"""
Simple HTTP Server để ESP32 fetch CSV
Chạy: python http_server.py
"""
import http.server
import socketserver
import socket

PORT = 8000

def get_local_ip():
    """Lấy IP của laptop trong mạng LAN"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[{self.address_string()}] {format % args}")

if __name__ == "__main__":
    local_ip = get_local_ip()
    
    print("=" * 50)
    print(f"🌐 HTTP Server đang chạy tại:")
    print(f"   http://{local_ip}:{PORT}")
    print(f"   http://localhost:{PORT}")
    print("=" * 50)
    print(f"\n📁 Serving files từ: {__file__.replace('http_server.py', '')}")
    print(f"📄 ESP32 sẽ fetch: http://{local_ip}:{PORT}/test.csv")
    print(f"\n⚠️  Cập nhật IP trong esp32_mqtt_sim.ino thành: {local_ip}")
    print("=" * 50)
    print("\nNhấn Ctrl+C để dừng server\n")
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n🛑 Server stopped")
