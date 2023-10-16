import vga1_8x8 as small
import tft_config
import s3lcd

import network
import socket
import ure
import time

import urequests
import json
import random

tft = tft_config.config(tft_config.WIDE)
tft.init()
messages = []

#############################################################################
# The following section allows you to set up a WiFi connection for the device
#############################################################################

def print_scr(text, fg, bg):
    tft.fill(bg)
    messages.append(text)
    a = len(messages) - 12
    b = len(messages)
    if (len(messages) < 12):
        a = 0
        b = len(messages)
    for i in range(a, b):
            tft.text(
                small,
                messages[i],
                8,
                14*(i - a),
                fg,
                bg
            )        
    tft.show()

print_scr("Welcome to DeadFellaz ESP32", s3lcd.WHITE, s3lcd.BLACK)




print_scr("Checking WiFi connectivity...", s3lcd.WHITE, s3lcd.BLACK)

ap_ssid = "DeadFellaz"
ap_password = "undeadhorde"
ap_authmode = 3  # WPA2-PSK

NETWORK_PROFILES = 'wifi.dat'

wlan_ap = network.WLAN(network.AP_IF)
wlan_sta = network.WLAN(network.STA_IF)

server_socket = None

def get_connection():
    """return a working WLAN(STA_IF) instance or None"""
    # First check if there already is any connection:
    if wlan_sta.isconnected():
        print_scr("WiFi connection already established", s3lcd.WHITE, s3lcd.BLACK)
        return wlan_sta
    connected = False
    try:
        # ESP connecting to WiFi takes time, wait a bit and try again:
        time.sleep(3)
        if wlan_sta.isconnected():
            print_scr("WiFi connection found after 3 seconds", s3lcd.WHITE, s3lcd.BLACK)     
            return wlan_sta
        # Read known network profiles from file
        profiles = read_profiles()
        # Search WiFis in range
        wlan_sta.active(True)
        networks = wlan_sta.scan()
        AUTHMODE = {0: "open", 1: "WEP", 2: "WPA-PSK", 3: "WPA2-PSK", 4: "WPA/WPA2-PSK"}
        for ssid, bssid, channel, rssi, authmode, hidden in sorted(networks, key=lambda x: x[3], reverse=True):
            ssid = ssid.decode('utf-8')
            encrypted = authmode > 0
            if encrypted:
                if ssid in profiles:
                    password = profiles[ssid]
                    connected = do_connect(ssid, password)
                else:
                    print_scr("Skip unknown network " + ssid, s3lcd.WHITE, s3lcd.BLACK)
            else:  # open
                connected = do_connect(ssid, None)
            if connected:   
                break
    except OSError as e:
        if (str(e) == "[Errno 2] ENOENT"):
            print_scr("First time configuration", s3lcd.WHITE, s3lcd.BLUE)
        else:
            print_scr("Something went wrong", s3lcd.WHITE, s3lcd.RED) 
            print_scr(str(e), s3lcd.WHITE, s3lcd.RED)
    # start web server for connection manager:
    if not connected:
        connected = start()
    return wlan_sta if connected else None
    
def read_profiles():
    with open(NETWORK_PROFILES) as f:
        lines = f.readlines()
    profiles = {}
    for line in lines:
        ssid, password = line.strip("\n").split(";")
        profiles[ssid] = password
    return profiles

def write_profiles(profiles):
    lines = []
    for ssid, password in profiles.items():
        lines.append("%s;%s\n" % (ssid, password))
    with open(NETWORK_PROFILES, "w") as f:
        f.write(''.join(lines))
        
def do_connect(ssid, password):
    wlan_sta.active(True)
    if wlan_sta.isconnected():
        print_scr("No network found.", s3lcd.WHITE, s3lcd.BLACK)
        return None
    print_scr("Trying to connect to " + str(ssid), s3lcd.WHITE, s3lcd.BLACK)
    wlan_sta.connect(ssid, password)
    for retry in range(200):
        connected = wlan_sta.isconnected()
        if connected:
            break
        time.sleep(0.1)
        print('.', end='')
    if connected:
        print_scr("Connected to " + str(ssid), s3lcd.WHITE, s3lcd.BLACK)
        
    else:
        print_scr("Failed to connect to " + str(ssid), s3lcd.WHITE, s3lcd.BLACK)
    return connected  

def send_header(client, status_code=200, content_length=None ):
    client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))
    client.sendall("Content-Type: text/html\r\n")
    if content_length is not None:
      client.sendall("Content-Length: {}\r\n".format(content_length))
    client.sendall("\r\n")

def send_response(client, payload, status_code=200):
    content_length = len(payload)
    send_header(client, status_code, content_length)
    if content_length > 0:
        client.sendall(payload)
    client.close()
    
def handle_root(client):
    wlan_sta.active(True)
    ssids = sorted(ssid.decode('utf-8') for ssid, *_ in wlan_sta.scan())
    send_header(client)
    client.sendall("""\
        <html>
            <h1 style="color: #5e9ca0;">
                <span style="color: #ff0000;">
                    Wi-Fi Client Setup
                </span>
            </h1>
            <form action="configure" method="post">
                <table style="margin-left: auto; margin-right: auto;">
                    <tbody>
    """)
    while len(ssids):
        ssid = ssids.pop(0)
        client.sendall("""\
                        <tr>
                            <td colspan="2">
                                <input type="radio" name="ssid" value="{0}" />{0}
                            </td>
                        </tr>
        """.format(ssid))
    client.sendall("""\
                        <tr>
                            <td>Password:</td>
                            <td><input name="password" type="password" /></td>
                        </tr>
                    </tbody>
                </table>
                <p style="text-align: center;">
                    <input type="submit" value="Submit" />
                </p>
            </form>
            <p>&nbsp;</p>
            <hr />
        </html>
    """)
    client.close()
    
def handle_configure(client, request):
    match = ure.search("ssid=([^&]*)&password=(.*)", request)

    if match is None:
        send_response(client, "Parameters not found", status_code=400)
        return False
    # version 1.9 compatibility
    try:
        ssid = match.group(1).decode("utf-8").replace("%3F", "?").replace("%21", "!")
        password = match.group(2).decode("utf-8").replace("%3F", "?").replace("%21", "!")
    except Exception:
        ssid = match.group(1).replace("%3F", "?").replace("%21", "!")
        password = match.group(2).replace("%3F", "?").replace("%21", "!")

    if len(ssid) == 0:
        send_response(client, "SSID must be provided", status_code=400)
        return False

    if do_connect(ssid, password):
        response = """\
            <html>
                    <br><br>
                    <h1 style="color: #5e9ca0; text-align: center;">
                        <span style="color: #ff0000;">
                            ESP successfully connected to WiFi network %(ssid)s.
                        </span>
                    </h1>
                    <br><br>
            </html>
        """ % dict(ssid=ssid)
        send_response(client, response)
        time.sleep(1)
        wlan_ap.active(False)
        try:
            profiles = read_profiles()
        except OSError:
            profiles = {}
        profiles[ssid] = password
        write_profiles(profiles)

        time.sleep(5)

        return True
    else:
        response = """\
            <html>
                    <h1 style="color: #5e9ca0; text-align: center;">
                        <span style="color: #ff0000;">
                            ESP could not connect to WiFi network %(ssid)s.
                        </span>
                    </h1>
                    <br><br>
                    <form>
                        <input type="button" value="Go back!" onclick="history.back()"></input>
                    </form>
            </html>
        """ % dict(ssid=ssid)
        send_response(client, response)
        return False

def handle_not_found(client, url):
    send_response(client, "Path not found: {}".format(url), status_code=404)
    
def stop():
    global server_socket

    if server_socket:
        server_socket.close()
        server_socket = None
        
def start(port=80):
    global server_socket

    addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]

    stop()

    wlan_sta.active(True)
    wlan_ap.active(True)

    wlan_ap.config(essid=ap_ssid, password=ap_password, authmode=ap_authmode)

    server_socket = socket.socket()
    server_socket.bind(addr)
    server_socket.listen(1)

    print_scr("", s3lcd.WHITE, s3lcd.BLACK)
    print_scr('Connect to WiFi ssid ' + ap_ssid, s3lcd.WHITE, s3lcd.BLACK)
    print_scr('with default password: ' + ap_password, s3lcd.WHITE, s3lcd.BLACK)
    print_scr('Access the ESP via your web browser.', s3lcd.WHITE, s3lcd.BLACK)
    print_scr('Listening on: 192.168.4.1', s3lcd.WHITE, s3lcd.BLACK)

    while True:
        if wlan_sta.isconnected():
            wlan_ap.active(False)
            return True

        print_scr("", s3lcd.WHITE, s3lcd.BLACK)
        print_scr("Waiting for connection...", s3lcd.WHITE, s3lcd.BLACK)
        client, addr = server_socket.accept()
        print_scr("", s3lcd.WHITE, s3lcd.BLACK)
        print_scr('Connection from ' + str(addr[0]), s3lcd.WHITE, s3lcd.BLACK)
        try:
            client.settimeout(5.0)

            request = b""
            try:
                while "\r\n\r\n" not in request:
                    request += client.recv(512)
            except OSError:
                pass

            # Handle form data from Safari on macOS and iOS; it sends \r\n\r\nssid=<ssid>&password=<password>
            try:
                request += client.recv(1024)
                print("Received form data after \\r\\n\\r\\n(i.e. from Safari on macOS or iOS)")
            except OSError:
                pass

            print("Request is: {}".format(request))
            if "HTTP" not in request:  # skip invalid requests
                continue

            # version 1.9 compatibility
            try:
                url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).decode("utf-8").rstrip("/")
            except Exception:
                url = ure.search("(?:GET|POST) /(.*?)(?:\\?.*?)? HTTP", request).group(1).rstrip("/")
            print("URL is {}".format(url))

            if url == "":
                handle_root(client)
            elif url == "configure":
                handle_configure(client, request)
            else:
                handle_not_found(client, url)

        finally:
            client.close()      

wlan = get_connection()
if wlan is None:
    print_scr("Could not initialize the network.", s3lcd.WHITE, s3lcd.RED)
    while True:
        pass  # you shall not pass :D

# Main Code goes here, wlan is a working network.WLAN(STA_IF) instance.
print_scr("Connected succesfully.", s3lcd.WHITE, s3lcd.BLUE)
time.sleep(1)

###################################
# This is where the real fun begins
###################################

def center_scr(text, fg, bg, height):
    length = 1 if isinstance(text, int) else len(text)
    tft.text(
        small,
        text,
        170 + (150 // 2 - length // 2 * small.WIDTH),
        height,
        fg,
        bg
    )

def left_scr(text, fg, bg, height):
    length = 1 if isinstance(text, int) else len(text)
    tft.text(
        small,
        text,
        178,
        height,
        fg,
        bg
    )

try:
    while True:
        r = random.randint(1,10000)
        f = random.randint(1,10)

        metadata = urequests.get(
            url="https://blockchaingandalf.com/fellaz/" +
            str(r) + 
            ".json"
        ).text
        obj = json.loads(metadata)

        image = urequests.get(
            url="https://blockchaingandalf.com/fellaz/z" +
            str(r) + 
            ".png"
        ).content   

        front = urequests.get(
            url="https://blockchaingandalf.com/fellaz/f" +
            str(r) + 
            ".png"
        ).content         

        tft.fill(s3lcd.BLACK)
        tft.rect(0,0,170,170,0x1f06)
        tft.rect(1,1,168,168,0x4349)
        center_scr(obj["name"], 0x07e4, s3lcd.BLACK, 4)

        left_scr(obj["attributes"][1]["trait_type"] + ":", 0x76cf, s3lcd.BLACK, 22)
        left_scr(obj["attributes"][1]["value"], 0x4c6c, s3lcd.BLACK, 32)

        left_scr(obj["attributes"][3]["trait_type"] + ":", 0x76cf, s3lcd.BLACK, 46)
        left_scr(obj["attributes"][3]["value"], 0x4c6c, s3lcd.BLACK, 56)

        left_scr(obj["attributes"][5]["trait_type"] + ":", 0x76cf, s3lcd.BLACK, 70)
        left_scr(obj["attributes"][5]["value"], 0x4c6c, s3lcd.BLACK, 80)

        left_scr(obj["attributes"][7]["trait_type"] + ":", 0x76cf, s3lcd.BLACK, 94)
        left_scr(obj["attributes"][7]["value"], 0x4c6c, s3lcd.BLACK, 104)

        left_scr(obj["attributes"][9]["trait_type"] + ":", 0x76cf, s3lcd.BLACK, 118)
        left_scr(obj["attributes"][9]["value"], 0x4c6c, s3lcd.BLACK, 128)

        left_scr(obj["attributes"][12]["trait_type"] + ":", 0x76cf, s3lcd.BLACK, 142)
        left_scr(str(obj["attributes"][12]["value"]), 0x4c6c, s3lcd.BLACK, 152)

        tft.png(image, 2, 2)
        tft.show()
        time.sleep(3)

        if (f > 5): 
            tft.png(front, 2, 2)
            tft.show()

        time.sleep(1)
        tft.png(image, 2, 2)
        tft.show()
        time.sleep(2)


except Exception as ex:
    error = str(type(ex))
    # while (len(error) % 38 != 0):
    #    error = error + " "
    print_scr("Error on count" + str(r), s3lcd.BLACK, s3lcd.RED)
    #for i in range(0, len(error) // 38):
    #    print_scr(error[(i * 38):(i * 38) + 37], s3lcd.WHITE, s3lcd.RED)
    print_scr(error, s3lcd.WHITE, s3lcd.RED)
    tft.show()
    time.sleep(60)  

finally:
    tft.deinit()  # Deinitialize the display or it will cause a crash on the next run




