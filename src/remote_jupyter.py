"""
rjy: remote jupyter session management
"""
import re
import os
from os.path import expanduser, join, exists, isdir
from pathlib import Path
import json
import shlex
from subprocess import Popen, PIPE
import logging
import defopt
from tabulate import tabulate

logger = logging.getLogger("rjy")

EX = "http://localhost:8904/lab?token=b1fc61e2[...]7b7a40"


TUNNEL_RE = re.compile(r"ssh -Y -N -L (?P<lhost>\w+):(?P<port1>\d+):"
                       r"(?P<lhost2>\w+):(?P<port2>\d+) (?P<rhost>\w+)")

LINK_RE = re.compile(r"http://(?P<lhost>localhost|127\\.0\\.0\\.1):"
                     r"(?P<port>\d+)/lab\?token=(?P<key>[0-9a-fA-F]+)")

LINK_STR = "http://{lhost}:{port}?token={token}"
FOOTER = """\
status types:

  - connected: a registered session is currently connected
  - disconnected: a session is registered, but currently connected
  - unregistered: a session is connected, but not registered with rjy
"""


def make_key(remote, port):
    return f"{remote}:{port}"


def parse_ps_cmd(x):
    out = []
    for line in x:
        line = line.strip()
        if not len(line):
            continue
        pid, command = re.split(' +', line, maxsplit=1)
        out.append((pid, command))
    return out


def parse_juypter_link(link):
    mtch = LINK_RE.match(link)
    assert mtch is not None, "invalid link format"
    lhost, port, token = mtch.groups()
    assert lhost in ('localhost', '127.0.0.1'), "invalid localhost"
    return port, token


def run_ps():
    p = Popen(["ps -x -o pid,command"], stdout=PIPE, shell=True)
    out, err = p.communicate()
    p.kill()
    return out.decode().split('\n')


def find_open_tunnels():
    """
    Returns a list of tuple values, (localhost, port, remote).
    """
    ps_rows = parse_ps_cmd(run_ps())
    header = ps_rows.pop(0)  # drop the header
    assert header[0].startswith('PID'), "top header does no match expected"
    matches = {}
    for pid, cmd in ps_rows:
        mtch = TUNNEL_RE.match(cmd)
        if mtch is not None:
            lhost1, port1, lhost2, port2, remote = mtch.groups()
            msg = "tunnel {thing} do not match ({a}≠{b})!"
            assert lhost1 == lhost2, msg.format(thing='localhosts',
                                                a=lhost1, b=lhost2)
            assert port1 == port2,  msg.format(thing='ports', a=port1, b=port2)
            matches[pid] = (remote, int(port1))
    return matches


class SSHTunnel(object):
    def __init__(self, host, port, token=None):
        self.port = port
        self.host = host
        self.token = token
        self.pid = None

    @property
    def name(self):
        return f"{self.host}:{self.port}"

    def __repr__(self):
        return f"SSHTunnel({self.name})"

    def start(self):
        if self.is_alive():
            msg = f"session is currently alive for {self}, cannot start"
            logger.info(msg)
            return True
        host, port = self.host, self.port
        cmd = f"ssh -Y -N -L localhost:{port}:localhost:{port} {host} &"
        cmds = shlex.split(cmd)

        p = Popen(cmds, start_new_session=True)
        self.pid = p.pid
        return p.pid

    def dump(self):
        return (self.host, self.port, self.token, self.pid)

    def is_alive(self):
        alive = find_open_tunnels()
        remote, port = self.host, self.port
        alive_keys = [x for x in alive.values()]
        if (remote, port) in alive_keys:
            return True
        return False


class Sessions(object):
    """
    A collection of sessions.
    """

    def __init__(self):
        self.sessions = {}  # what to write to the cache
        self.cached_sessions = {}  # from the file
        self.alive = {}  # what's running
        self.check_valid()
        self.load_cached_sessions()
        self.load_alive()

    def _make_homedir(self):
        os.mkdir(self.home_dir)

    @property
    def home_dir(self):
        home_dir = join(expanduser("~"), ".remote_jupyter")
        return home_dir

    def check_valid(self):
        home_exists = exists(self.home_dir) and isdir(self.home_dir)
        if not home_exists:
            assert not exists(self.home_dir)  # something else is wrong
            logger.info("creating ~/.remote_jupyter")
            self._make_homedir()
        if not exists(self.sessions_file):
            Path(self.sessions_file).touch()

    def load_cached_sessions(self):
        """
        Load the expected sessions.
        """
        self.check_valid()
        empty_sessions = os.path.getsize(self.sessions_file) == 0
        if not exists(self.sessions_file) or empty_sessions:
            self.cached_sessions = {}
            return {}

        with open(self.sessions_file) as f:
            cached = json.load(f)
            # make a key
            self.cached_sessions = cached

        self.sessions = {**self.sessions, **self.cached_sessions}
        return self.cached_sessions

    def load_alive(self):
        alive = find_open_tunnels()
        self.alive = {make_key(*x): x for x in alive.values()}
        return self.alive

    def compare_sessions(self):
        """
        Compare what's alive and what's cached, output a table.
        """
        self.check_valid()
        alive = self.load_alive()
        cached = self.load_cached_sessions()

        all_keys = set(alive).union(set(cached))

        connected_rows = []
        for key in all_keys:
            pid = None
            if key in alive and key in cached:
                status = 'conected'
            elif key in alive and key not in cached:
                status = 'unregistered'
            elif key not in alive and key in cached:
                status = 'disconnected'
            else:
                raise ValueError("invalid state")

            remote, port = alive.get(key, (None, None))
            remote_cached, port_cached, token = None, None, None
            if key in cached:
                remote_cached, port_cached, token, pid = cached[key]

            # validate state
            if port is not None and port_cached is not None:
                assert port == int(port_cached)
            if remote is not None and remote_cached is not None:
                assert remote == remote_cached

            # if status is disconnected, the pid is no longer accurate
            pid = None if status == 'disconnected' else pid

            # make the link if possible
            link = None
            if token is not None:
                link = LINK_STR.format(lhost='localhost',
                                       port=port, token=token)
            connected_rows.append((key, pid, remote, port, status, link))

        header = ['key', 'pid', 'remote', 'port', 'status', 'link']
        tab = tabulate(connected_rows, headers=header)
        print("\n" + tab)
        print("\n" + FOOTER)

    @property
    def sessions_file(self):
        return join(self.home_dir, "sessions.json")

    def reconnect(self, key=None, verbose=False):
        """
        Reconnect all sessions.
        """
        self.check_valid()
        alive = self.load_alive()
        if key is not None:
            assert key in self.cached_sessions
            if key in alive:
                msg = f"the key {key} was found to already by connected!"
                logger.info(msg)
                return

        # reconnect everything in cached
        for cached_key, values in self.cached_sessions.items():
            if key is not None and cached_key != key:
                # only handle they specified key if set
                continue
            if cached_key in alive:
                # already running...
                if verbose:
                    msg = (f"cached session {cached_key} is "
                           "already connected...")
                    logger.info(msg)
                continue
            host, port, token, pid = values
            tunnel = SSHTunnel(host, port, token)
            tunnel.start()
            logger.info(f"reconnected session {host}:{port}")

            # register it
            self.sessions[cached_key] = tunnel
            self.save()

    def drop(self, key):
        """
        Drop a session (from the cache).
        """
        self.check_valid()
        self.load_cached_sessions()
        self.sessions = {}
        for cache_key, session in self.cached_sessions.items():
            if key != cache_key:
                self.sessions[cache_key] = session
            else:
                logger.info(f"dropping session {key} from registration")
        self.save()

    def save(self):
        """
        """
        with open(self.sessions_file, 'w') as f:
            dumped = {k: v.dump() for k, v in self.sessions.items()}
            json.dump(dumped, f)

    def disconnect(self, key=None, pid=None):
        alive = find_open_tunnels()
        for pid, session in alive.items():
            remote, port = session
            if pid == pid or key == make_key(remote, port):
                logger.info(f"disconnecting {pid} for {remote}:{port}")
                os.kill(int(pid), 2)

    def killall(self):
        "Kill all found funnels."
        alive = find_open_tunnels()
        for pid, session in alive.items():
            remote, port = session
            logger.info(f"killing {pid} for {remote}:{port}")
            os.kill(int(pid), 2)

    def new(self, link, remote):
        """
        Create a new tunnel for a session, given the session link.
        """
        self.check_valid()
        port, token = parse_juypter_link(link)
        new_key = make_key(remote, port)
        if new_key in self.alive:
            logger.warning(f"tunnel {remote}:{port} already exists!")
            return

        if new_key in self.cached_sessions:
            msg = (f"tunnel {remote}:{port} is cached, but not "
                   "alive... reconnecting.")
            logger.info(msg)

        # create new tunnel
        tunnel = SSHTunnel(remote, port, token)
        tunnel.start()
        logger.info(f"connected new session {remote}:{port}")

        # register it
        self.sessions[new_key] = tunnel
        self.save()


def reconnect(key: str = None, *, verbose: bool = True):
    """
    Reconnect the given key or all if key not specified.

    key: the key to reconnect (if not set, reconnects all cached).
    verbose: be verbose
    """
    s = Sessions()
    s.reconnect(key)


def drop(key: str):
    """
    Drop a session that's tracked in the cache.

    key: the key to drop
    """
    s = Sessions()
    s.drop(key=key)


def disconnect(key: str = None, *, pid: int = None):
    """
    disconnect specified process ID or key (specify either).

    key: the key to disconnect.
    pid: the PIDt to disconnect.

    """
    s = Sessions()
    s.disconnect(key=key, pid=pid)


def killall():
    """
    Kill all found running tunnels.
    """
    s = Sessions()
    s.killall()


def new(link: str, remote: str):
    f"""
    Initiate a new session from a remote link.

    link: the link from the Jupyter session, e.g. {EX}
    remote: the hostname or IP of the remote server
    """
    s = Sessions()
    s.new(link, remote)


def list_sessions():
    """
    Check and list all tunnel sessions, both found and cached.
    """
    s = Sessions()
    s.compare_sessions()


def main():
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    defopt.run({'list': list_sessions, 'new': new,
                'killall': killall,
                'dc': disconnect,
                'drop': drop, 'rc': reconnect})
