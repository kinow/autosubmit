try:
    from ruamel.yaml import CLoader as Loader, CDumper as Dumper
except ImportError:
    from ruamel.yaml import Loader, Dumper
from ruamel.yaml import YAML
class YAMLParserFactory:
    def __init__(self):
        pass

    def create_parser(self):
        return YAMLParser()

class YAMLParser(YAML):

    def __init__(self):
        self.data = []
        super(YAMLParser, self).__init__(typ="safe")
    # def get_section(self, section, d_value=None, must_exists = False ):
    #     """
    #     Gets any section if it exists within the dictionary, else returns None or error if must exists.
    #     :param section:
    #     :type list
    #     :param must_exists:
    #     :type bool
    #     :param d_value:
    #     :type str
    #     :return:
    #     """
    #     section = [s.upper() for s in section]
    #     # For text redeability
    #     section_str = str(section[0])
    #     for sect in section[1:]:
    #         section_str += "." + str(sect)
    #     current_level=self.experiment_data.get(section[0],None)
    #     for param in section[1:]:
    #         if current_level:
    #             if type(current_level) is dict:
    #                 current_level = current_level.get(param,d_value)
    #             else:
    #                 return None
    #     if not current_level and must_exists:
    #         return None
    #     if not current_level or current_level == "":
    #         return d_value
    #     else:
    #         return current_level
    # def check_exists(self,section="",option= "",conf_file="",typ=""):
    #     """
    #     Checks if an option exists, and returns value it if exists. Otherwise it returns false
    #
    #     :param conf_file: file that contains the option
    #     :type section: str
    #     :param section: section that contains the option
    #     :type section: str
    #     :param option: option to check
    #     :type option: str
    #     :return: True if option exists, False otherwise
    #     :rtype: value or False and type
    #     """
    #     if conf_file == "":
    #         if section in self.data:
    #             if option == "":
    #                 return self.data[section],type(self.data[section])
    #             elif option in self.data[section]:
    #                 return self.data[section][option],type(self.data[section][option])
    #             else:
    #                 return False,None
    #         else:
    #             return False,None
    #     else:
    #         if section in self.data[conf_file]:
    #             if option == "":
    #                 return self.data[conf_file][section]
    #             elif option in self.data[conf_file][section]:
    #                 return self.data[conf_file][section][option],type(self.data[conf_file][section][option])
    #             else:
    #                 return False,None
    #         else:
    #             return False,None
    # def check_is_choice(self, section="", option="", must_exist=True, choices=[],conf_file= ""):
    #     """
    #     Checks if an option has the expected value and returns it. Otherwise returns False
    #
    #     :param conf_file: file that contains the option
    #     :type section: str
    #     :param section: section that contains the option
    #     :type section: str
    #     :param option: option to check
    #     :type option: str
    #     :return: True if option exists, False otherwise
    #     :rtype: value,type or False,type
    #     """
    #     if conf_file == "":
    #         if section in self.data:
    #             if option == "":
    #                 if self.data[section] in choices:
    #                     return self.data[section]
    #                 else:
    #                     if must_exist:
    #                         return False
    #                     else:
    #                         return True
    #             elif option in self.data[section]:
    #                 if self.data[section][option] in choices:
    #                     return self.data[section][option]
    #                 else:
    #                     if must_exist:
    #                         return False
    #                     else:
    #                         return True
    #             else:
    #                 return False
    #         else:
    #             return False
    #     else:
    #         if section in self.data[conf_file]:
    #             if option == "":
    #                 return self.data[conf_file][section]
    #             elif option in self.data[conf_file][section]:
    #                 return self.data[conf_file][section][option]
    #             else:
    #                 return False
    #         else:
    #             return False
# class job(YAML.YAMLObject):
#
#     yaml_tag = u'!job'
#     def __init__(self, name, hp, ac, attacks):
#         self.name = name
#
#     self.delay_end = datetime.datetime.now()
#     self.delay_retrials = 0
#     self.wrapper_type = "none"
#     self._wrapper_queue = None
#     self._platform = None
#     self._queue = None
#     self.retry_delay = 0
#     self.platform_name = None  # type: str
#     self.section = None  # type: str
#     self.wallclock = None  # type: str
#     self.wchunkinc = None
#     self.tasks = '0'
#     self.threads = '1'
#     self.processors = '1'
#     self.memory = ''
#     self.memory_per_task = ''
#     self.chunk = None
#     self.member = None
#     self.date = None
#     self.name = name
#     self.split = None
#     self.delay = None
#     self.frequency = None
#     self.synchronize = None
#     self.skippable = False
#     self.repacked = 0
#     self._long_name = None
#     self.long_name = name
#     self.date_format = ''
#     self.type = Type.BASH
#     self.scratch_free_space = None
#     self.custom_directives = []
#     self.undefined_variables = None
#     self.log_retries = 5
#     self.id = job_id
#     self.file = None
#     self.executable = None
#     self.x11 = False
#     self._local_logs = ('', '')
#     self._remote_logs = ('', '')
#     self.script_name = self.name + ".cmd"
#     self.status = status
#     self.prev_status = status
#     self.old_status = self.status
#     self.new_status = status
#     self.priority = priority
#     self._parents = set()
#     self._children = set()
#     self.fail_count = 0
#     self.expid = name.split('_')[0]  # type: str
#     self.parameters = dict()
#     self._tmp_path = os.path.join(
#         BasicConfig.LOCAL_ROOT_DIR, self.expid, BasicConfig.LOCAL_TMP_DIR)
#     self.write_start = False
#     self._platform = None
#     self.check = 'true'
#     self.check_warnings = False
#     self.packed = False
#     self.hold = False  # type: bool
#     self.distance_weight = 0
#     self.level = 0
#     self.export = "none"
#     self.dependencies = []
#
#     def __repr__(self):
#         return "%s(name=%r, hp=%r, ac=%r, attacks=%r)" % (
#             self.__class__.__name__, self.name, self.hp, self.ac, self.attacks)