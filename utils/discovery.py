import nmap
import socket

def get_local_ip():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 8000))
        return s.getsockname()[0]
    
def discover_ips_on_port(local_ip, port):
    network_prefix = '.'.join(local_ip.split('.')[:-1])
    target_ip = f"{network_prefix}.0/24"
    nm = nmap.PortScanner()
    nm.scan(hosts=target_ip, arguments=f'-p {port}')
    ips = [host for host in nm.all_hosts() if nm[host].has_tcp(port) and nm[host]['tcp'][port]['state'] == 'open' and host != local_ip]
    
    return ips
