import os
import pwd

from log.log import Log, AutosubmitCritical
from autosubmitconfigparser.config.basicconfig import BasicConfig
from typing import Tuple

def check_experiment_ownership(expid, basic_config, raise_error=False, logger=None):
  # [A-Za-z09]+ variable is not needed, LOG is global thus it will be read if available
  ## type: (str, BasicConfig, bool, Log) -> Tuple[bool, bool, str]
  my_user_ID = os.getuid()
  current_owner_ID = 0
  current_owner_name = "NA"
  try:
      current_owner_ID = os.stat(os.path.join(basic_config.LOCAL_ROOT_DIR, expid)).st_uid
      current_owner_name = pwd.getpwuid(os.stat(os.path.join(basic_config.LOCAL_ROOT_DIR, expid)).st_uid).pw_name
  except Exception as e:
      if logger:
        logger.info("Error while trying to get the experiment's owner information.")
  finally:
      if current_owner_ID <= 0 and logger:        
          logger.info("Current owner '{0}' of experiment {1} does not exist anymore.", current_owner_name, expid)
  is_owner = current_owner_ID == my_user_ID
  eadmin_user = os.popen('id -u eadmin').read().strip() # If eadmin no exists, it would be "" so INT() would fail.
  if eadmin_user != "":
      is_eadmin = my_user_ID == int(eadmin_user)
  else:
      is_eadmin = False
  if not is_owner and raise_error:
    raise AutosubmitCritical("You don't own the experiment {0}.".format(expid), 7012)     
  return is_owner, is_eadmin, current_owner_name