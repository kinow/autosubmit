try:
    # noinspection PyCompatibility
    from configparser import SafeConfigParser
except ImportError:
    # noinspection PyCompatibility
    from ConfigParser import SafeConfigParser


class ConfigParserFactory:

    def __init__(self):
        pass

    def create_parser(self):
        return SafeConfigParser()
