try:
    # noinspection PyCompatibility
    from configparser import ConfigParser as ConfPar
except ImportError:
    # noinspection PyCompatibility
    from ConfigParser import ConfigParser as ConfPar
import bscearth.utils.path
import re
from pyparsing import nestedExpr


class ConfigParserFactory:

    def __init__(self):
        pass

    def create_parser(self):
        return ConfigParser()


class ConfigParser(ConfPar, object):

    def __init__(self):
        super(ConfigParser, self).__init__()

    def get_option(self, section, option, default=None):
        """
        Gets an option from given parser

        :param self: parser to use
        :type self: SafeConfigParser
        :param section: section that contains the option
        :type section: str
        :param option: option to get
        :type option: str
        :param default: value to be returned if option is not present
        :type default: object
        :return: option value
        :rtype: str
        """
        if self.has_option(section, option):
            return self.get(section, option)
        else:
            return default

    def get_path_option(self, section, option, default=None):
        """
        Gets an option from given parser

        :param self: parser to use
        :type self: SafeConfigParser
        :param section: section that contains the option
        :type section: str
        :param option: option to get
        :type option: str
        :param default: value to be returned if option is not present
        :type default: object
        :return: option value
        :rtype: str
        """
        return bscearth.utils.path.expand_path(self.get_option(section, option, default))

    def get_bool_option(self, section, option, default):
        """
        Gets a boolean option from given parser

        :param self: parser to use
        :type self: SafeConfigParser
        :param section: section that contains the option
        :type section: str
        :param option: option to get
        :type option: str
        :param default: value to be returned if option is not present
        :type default: bool
        :return: option value
        :rtype: bool
        """
        if self.has_option(section, option):
            return self.get(section, option).lower().strip() == 'true'
        else:
            return default

    def get_int_option(self, section, option, default=0):
        """
        Gets an integer option

        :param section: section that contains the option
        :type section: str
        :param option: option to get
        :type option: str
        :param default: value to be returned if option is not present
        :type default: int
        :return: option value
        :rtype: int
        """
        return int(self.get_option(section, option, default))

    def get_float_option(self, section, option, default=0.0):
        """
        Gets a float option

        :param section: section that contains the option
        :type section: str
        :param option: option to get
        :type option: str
        :param default: value to be returned if option is not present
        :type default: float
        :return: option value
        :rtype: float
        """
        return float(self.get_option(section, option, default))

    def get_choice_option(self, section, option, choices, default=None, ignore_case=False):
        """
        Gets a boolean option

        :param ignore_case: if True,
        :param choices: available choices
        :type choices: [str]
        :param section: section that contains the option
        :type section: str
        :param option: option to get
        :type option: str
        :param default: value to be returned if option is not present
        :type default: str
        :return: option value
        :rtype: str
        """

        if self.has_option(section, option):
            value = self.get_option(section, option, choices[0])
            if ignore_case:
                value = value.lower()
                for choice in choices:
                    if value == choice.lower():
                        return choice
            else:
                if value in choices:
                    return value
            raise ConfigError('Value {2} in option {0} in section {1} is not a valid choice'.format(option, section,
                                                                                                    value))
        else:
            if default:
                return default
        raise ConfigError('Option {0} in section {1} is not present and there is not a default value'.format(option,
                                                                                                             section))

    def get_list_option(self, section, option, default=list(), separator=' '):
        """
        Gets a list option

        :param section: section that contains the option
        :type section: str
        :param option: option to get
        :type option: str
        :param default: value to be returned if option is not present
        :type default: object
        :param separator: separator used to split the list
        :type separator: str
        :return: option value
        :rtype: list
        """
        if self.has_option(section, option):
            return self.get(section, option).split(separator)
        else:
            return default

    def get_int_list_option(self, section, option, default=list(), separator=' '):
        """
        Gets a list option

        :param section: section that contains the option
        :type section: str
        :param option: option to get
        :type option: str
        :param default: value to be returned if option is not present
        :type default: object
        :param separator: separator used to split the list
        :type separator: str
        :return: option value
        :rtype: list
        """
        if self.has_option(section, option):
            return [int(i) for i in self.get_list_option(section, option, separator=separator)]
        else:
            return default

    def check_exists(self, section, option):
        """
        Checks if an option exists in given parser

        :param section: section that contains the option
        :type section: str
        :param option: option to check
        :type option: str
        :return: True if option exists, False otherwise
        :rtype: bool
        """
        if self.has_option(section, option):
            return True
        else:
            return False

    def check_is_boolean(self, section, option, must_exist):
        """
        Checks if an option is a boolean value in given parser

        :param section: section that contains the option
        :type section: str
        :param option: option to check
        :type option: str
        :param must_exist: if True, option must exist
        :type must_exist: bool
        :return: True if option value is boolean, False otherwise
        :rtype: bool
        """
        if must_exist and not self.check_exists(section, option):
            return False
        if self.get_option(section, option, 'false').lower() not in ['false', 'true']:
            return False
        return True

    def check_is_choice(self, section, option, must_exist, choices):
        """
        Checks if an option is a valid choice in given parser

        :param self: parser to use
        :type self: SafeConfigParser
        :param section: section that contains the option
        :type section: str
        :param option: option to check
        :type option: str
        :param must_exist: if True, option must exist
        :type must_exist: bool
        :param choices: valid choices
        :type choices: list
        :return: True if option value is a valid choice, False otherwise
        :rtype: bool
        """
        if must_exist and not self.check_exists(section, option):
            return False
        value = self.get_option(section, option, choices[0])
        if value not in choices:
            return False
        return True

    def check_is_int(self, section, option, must_exist):
        """
        Checks if an option is an integer value in given parser

        :param self: parser to use
        :type self: SafeConfigParser
        :param section: section that contains the option
        :type section: str
        :param option: option to check
        :type option: str
        :param must_exist: if True, option must exist
        :type must_exist: bool
        :return: True if option value is integer, False otherwise
        :rtype: bool
        """
        if must_exist and not self.check_exists(section, option):
            return False
        value = self.get_option(section, option, '1')
        try:
            int(value)
        except ValueError:
            return False
        return True

    def check_regex(self, section, option, must_exist, regex):
        """
        Checks if an option complies with a regular expression in given parser

        :param self: parser to use
        :type self: SafeConfigParser
        :param section: section that contains the option
        :type section: str
        :param option: option to check
        :type option: str
        :param must_exist: if True, option must exist
        :type must_exist: bool
        :param regex: regular expression to check
        :type regex: str
        :return: True if option complies with regex, False otherwise
        :rtype: bool
        """
        if must_exist and not self.check_exists(section, option):
            return False
        prog = re.compile(regex)
        value = self.get_option(section, option, '1')
        if not prog.match(value):
            return False
        return True

    @staticmethod
    def check_json(key, value):
        """
        Checks if value is a valid json

        :param key: key to check
        :type key: str
        :param value: value
        :type value: str
        :return: True if value is a valid json, False otherwise
        :rtype: bool
        """
        # noinspection PyBroadException
        try:
            nestedExpr('[', ']').parseString(value).asList()
            return True
        except:
            return False


class ConfigError(Exception):

    def __init__(self, msg, *args):
        super(ConfigError, self).__init__(msg.format(*args))
