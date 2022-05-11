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