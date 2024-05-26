import socket
import time
import uuid
from telnetlib import Telnet
from typing import Any, Tuple
import re
from datetime import datetime
import threading

telnet_d = {
    "IAC": bytes([255]),
    "DONT": bytes([254]),
    "DO": bytes([253]),
    "WONT": bytes([252]),
    "WILL": bytes([251]),
    "theNULL": bytes([0]),

    "SE": bytes([240]),  # Subnegotiation End
    "NOP": bytes([241]),  # No Operation
    "DM": bytes([242]),  # Data Mark
    "BRK": bytes([243]),  # Break
    "IP": bytes([244]),  # Interrupt process
    "AO": bytes([245]),  # Abort output
    "AYT": bytes([246]),  # Are You There
    "EC": bytes([247]),  # Erase Character
    "EL": bytes([248]),  # Erase Line
    "GA": bytes([249]),  # Go Ahead
    "SB": bytes([250]),  # Subnegotiation Begin

    # Telnet protocol options code (don't change)
    # These ones all come from arpa/telnet.h
    "BINARY": bytes([0]),  # 8-bit data path
    "ECHO": bytes([1]),  # echo
    "RCP": bytes([2]),  # prepare to reconnect
    "SGA": bytes([3]),  # suppress go ahead
    "NAMS": bytes([4]),  # approximate message size
    "STATUS": bytes([5]),  # give status
    "TM": bytes([6]),  # timing mark
    "RCTE": bytes([7]),  # remote controlled transmission and echo
    "NAOL": bytes([8]),  # negotiate about output line width
    "NAOP": bytes([9]),  # negotiate about output page size
    "NAOCRD": bytes([10]),  # negotiate about CR disposition
    "NAOHTS": bytes([11]),  # negotiate about horizontal tabstops
    "NAOHTD": bytes([12]),  # negotiate about horizontal tab disposition
    "NAOFFD": bytes([13]),  # negotiate about formfeed disposition
    "NAOVTS": bytes([14]),  # negotiate about vertical tab stops
    "NAOVTD": bytes([15]),  # negotiate about vertical tab disposition
    "NAOLFD": bytes([16]),  # negotiate about output LF disposition
    "XASCII": bytes([17]),  # extended ascii character set
    "LOGOUT": bytes([18]),  # force logout
    "BM": bytes([19]),  # byte macro
    "DET": bytes([20]),  # data entry terminal
    "SUPDUP": bytes([21]),  # supdup protocol
    "SUPDUPOUTPUT": bytes([22]),  # supdup output
    "SNDLOC": bytes([23]),  # send location
    "TTYPE": bytes([24]),  # terminal type
    "EOR": bytes([25]),  # end or record
    "TUID": bytes([26]),  # TACACS user identification
    "OUTMRK": bytes([27]),  # output marking
    "TTYLOC": bytes([28]),  # terminal location number
    "VT3270REGIME": bytes([29]),  # 3270 regime
    "X3PAD": bytes([30]),  # X.3 PAD
    'NAWS': bytes([31]),  # window size
    "TSPEED": bytes([32]),  # terminal speed
    "LFLOW": bytes([33]),  # remote flow control
    "LINEMODE": bytes([34]),  # Linemode option
    "XDISPLOC": bytes([35]),  # X Display Location
    "OLD_ENVIRON": bytes([36]),  # Old - Environment variables
    "AUTHENTICATION": bytes([37]),  # Authenticate
    "ENCRYPT": bytes([38]),  # Encryption option
    "NEW_ENVIRON": bytes([39]),  # New - Environment variables
    # the following ones come from
    # http://www.iana.org/assignments/telnet-options
    # Unfortunately, that document does not assign identifiers
    # to all of them, so we are making them up
    "TN3270E": bytes([40]),  # TN3270E
    "XAUTH": bytes([41]),  # XAUTH
    "CHARSET": bytes([42]),  # CHARSET
    "RSP": bytes([43]),  # Telnet Remote Serial Port
    "COM_PORT_OPTION": bytes([44]),  # Com Port Control Option
    "SUPPRESS_LOCAL_ECHO": bytes([45]),  # Telnet Suppress Local Echo
    "TLS": bytes([46]),  # Telnet Start TLS
    "KERMIT": bytes([47]),  # KERMIT
    "SEND_URL": bytes([48]),  # SEND-URL
    "FORWARD_X": bytes([49]),  # FORWARD_X
    "PRAGMA_LOGON": bytes([138]),  # TELOPT PRAGMA LOGON
    "SSPI_LOGON": bytes([139]),  # TELOPT SSPI LOGON
    "PRAGMA_HEARTBEAT": bytes([140]),  # TELOPT PRAGMA HEARTBEAT
    "EXOPL": bytes([255]),  # Extended-Options-List
    "NOOPT": bytes([0])

}
telnet_dict = {v: k for k, v in telnet_d.items()}


class TelnetDevice:
    wait_user: bytes
    wait_password: bytes
    login: bytes
    password: bytes
    ipaddr: str
    port: int
    quit_str: bytes
    name: str

    busy: bool = False
    session: str

    def __init__(self, wait1, wait2, login, password, ipaddr, quit_str, name, port=23):
        self.wait_user = wait1
        self.wait_password = wait2
        self.login = login
        self.password = password
        self.ipaddr = ipaddr
        self.port = port
        self.quit_str = quit_str
        self.name = name


class TelnetSession:
    dev_id: int
    history_str = b""
    tn: Telnet | None
    session_id: str
    cmd_hist = []
    quit_str: bytes
    start_time: float

    timer: threading.Timer
    session_time = 60 * 15

    def start_session(self, key: str, dev_id):
        self.start_time = datetime.now().timestamp()
        self.timer = threading.Timer(self.session_time, self.destroy_session, [key])
        self.timer.start()
        devices[dev_id].busy = True
        devices[dev_id].session = key
        telnet_login = devices[dev_id].login
        telnet_password = devices[dev_id].password
        try:
            self.tn = Telnet(devices[dev_id].ipaddr, devices[dev_id].port, timeout=1)
        except Exception as e:
            self.tn = None
            return
        if devices[dev_id].wait_user != b'':
            self.tn.read_until(devices[dev_id].wait_user)
            self.tn.write(telnet_login)
        self.tn.read_until(devices[dev_id].wait_password)
        self.tn.write(telnet_password)
        self.quit_str = devices[dev_id].quit_str
        self.cmd_hist = []
        self.dev_id = dev_id
        self.session_id = key
        # self.tn.write(telnet_d['IAC'] + telnet_d['WONT'] + telnet_d['LINEMODE'] +
        #               telnet_d['IAC'] + telnet_d['WILL'] + telnet_d['ECHO'])
        sessions[key] = self
        set_devs_update_events()

    def read(self, timeout=15) -> tuple[str, int]:
        data = b''
        # Берем данные
        self.tn.get_socket().settimeout(timeout)
        try:
            while data.strip() == b'':
                data += self.tn.get_socket().recv(10000000).replace(bytes([7]), b'')
        except Exception as e:
            if e.__str__() == 'timed out':
                return "", 0
            else:
                self.destroy_session(self.session_id)
                return "Соединение прервано", -1

        # Берем данные еще раз на всякий пожарный
        self.tn.get_socket().settimeout(0.2)
        try:
            data += self.tn.get_socket().recv(10000000).replace(bytes([7]), b'')
        except Exception as e:
            if e.__str__() != 'timed out':
                self.destroy_session(self.session_id)
                return "Соединение прервано", -1
        # Подчищаем немного данные
        data = (data.decode("ascii", errors='ignore').
                replace("\x1b[K\x1b7\x1b[r\x1b8", "").
                replace("\x01\x03\x18\x1f", "").
                replace("\x1b[9999B", "").
                replace("\x00", "").
                replace("\x1b[K", "").
                replace("\x1b7\x1b[r\x1b8 \b \b", "").
                replace("\x1b7\x1b8", "")
                ).encode('ascii')

        # Заменяем \x1b[n* на '\b'*n
        while data.find(b"\x1b[") != -1:
            i = data.find(b"\x1b[")
            i += 2
            n = b""
            while chr(data[i]).isdigit():
                n += bytes([data[i]])
                i += 1
            num = 0
            if n.isdigit():
                num = int(n)

            n += bytes([data[i]])
            print(n)
            data = data.replace(b'\x1b[' + n, b'\b' * num)
        return data.decode('ascii'), 0

    def write(self, buffer: bytes):
        print(buffer)
        if buffer.startswith(b'^C'):
            self.tn.get_socket().send(b'\x03')
            return
        if buffer.strip().startswith(b'?'):
            self.tn.get_socket().send(b'?')
            return
        if buffer.startswith(b'\r\n'):
            print('here!')
            self.tn.get_socket().send(b'\r\n')
            return
        self.tn.get_socket().send(buffer + b' ' + b'\b' * 99)
        if buffer.replace(b'\r\n', b"").rstrip().lstrip().rstrip(b'\b').strip() == self.quit_str:
            self.destroy_session(self.session_id)

    def history(self) -> bytes:
        return self.history_str

    def destroy_session(self, session: str):
        self.timer.cancel()
        self.tn.close()
        self.cmd_hist = []
        if session in sessions:
            sessions.pop(session)
        devices[self.dev_id].busy = False
        devices[self.dev_id].session = ""
        set_devs_update_events()

    def get_start_time(self):
        return self.start_time


def start_session(session: str, dev_id) -> TelnetSession | None:
    telnet_session = TelnetSession()
    telnet_session.start_session(session, dev_id)
    if telnet_session.tn is None:
        devices[dev_id].busy = False
        return None
    return telnet_session


def get_session(session: str) -> TelnetSession | None:
    if session in sessions:
        return sessions[session]
    return None

def set_devs_update_events():
    for event in devs_update_events:
        event.set()


devs_update_events = []

sessions = {}
devices = [
    TelnetDevice(b'Login:', b'Password:',
                 b'admin+ct\r\n', b'\r\n', '192.168.1.126', b'quit', 'Mikrotik', 23),
    TelnetDevice(b'Username:', b'Password:',
                 b'admin\r\n', b'admin\r\n', '192.168.1.3', b'exit', "Tp-link", 23),
    TelnetDevice(b'Login:', b'Password:',
                 b'admin+ct\r\n', b'\r\n', '192.168.1.199', b'quit', 'Mikrotik virtual', 23),
    TelnetDevice(b'', b'Password:',
                 b'', b'cisco', '192.168.1.105', b'quit', 'Cisco virtual', 23),
]
