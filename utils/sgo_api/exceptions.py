class ProxyError(Exception):
    pass


class ParseProxyError(ProxyError):
    pass


class IncorrectProxyType(ProxyError):
    pass


class IncorrectProxyScheme(ProxyError):
    pass


class SgoRso23(Exception):
    pass


class LoginError(SgoRso23):
    pass
