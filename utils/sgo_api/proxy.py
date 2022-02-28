from typing import Union, Optional

from .exceptions import *


class Proxy:
    def __init__(self):
        self.scheme: Optional[None] = None
        self.ip: Optional[None] = None
        self.port: Optional[None] = None
        self.username: Optional[None] = None
        self.password: Optional[None] = None

    @property
    def valid(self):
        return bool(self.scheme and self.ip and self.port)

    @property
    def auth(self):
        return bool(self.username and self.password)

    @property
    def url(self, include_scheme=True):
        url = ''
        if include_scheme:
            url += f'{self.scheme}://'
        if self.auth:
            url += f'{self.username}:{self.password}@'
        url += f'{self.ip}:{self.port}'
        return url

    @property
    def proxy_auth(self):
        if self.auth:
            return self.username, self.password
        else:
            return None

    def parse(self, proxy: Union[str, list, dict], scheme: str = 'http'):
        scheme = scheme.lower()
        if scheme not in ['http', 'https', 'socks4', 'socks5']:
            raise IncorrectProxyScheme(f'Proxy.parse(self, {scheme}, {proxy}): {scheme} Excepted.')

        if isinstance(proxy, str):
            proxy_split = proxy.split(":")
            if len(proxy_split) < 2:  # if cannot split string
                raise ParseProxyError(f'Proxy.parse(self, {scheme}, {proxy}): (str) proxy_split={proxy_split}')
            self.scheme = scheme
            self.ip = proxy_split[0]
            self.port = int(proxy_split[1])
            if len(proxy_split) >= 4:
                self.username = proxy_split[2]
                self.password = proxy_split[3]
        elif isinstance(proxy, list):
            if len(proxy) < 2:
                raise ParseProxyError(f'Proxy.parse(self, {scheme}, {proxy}): (list)')
            self.scheme = scheme
            self.ip = proxy[0]
            self.port = int(proxy[1])
            if len(proxy) >= 4:
                self.username = proxy[2]
                self.password = proxy[3]
        elif isinstance(proxy, dict):
            self.scheme = proxy.get('type')
            self.ip = proxy['ip']
            self.port = int(proxy['port'])
            self.username = proxy.get('user') or proxy.get('username')
            self.password = proxy.get('pwd') or proxy.get('pass') or proxy.get('password')
        else:
            raise IncorrectProxyType(f'Proxy.parse(self, {scheme}, {proxy}): ({type(proxy)})')
        return
