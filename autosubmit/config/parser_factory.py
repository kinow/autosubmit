try:
    # noinspection PyCompatibility
    from configparser import SafeConfigParser
except ImportError:
    # noinspection PyCompatibility
    from ConfigParser import SafeConfigParser


class ConfigParserFactory:

    def create_parser(self):
        return SafeConfigParser()