How to run only selected members
================================

To run only a subset of selected members you can execute the command:
::

    autosubmit run EXPID -rm MEMBERS
  
*EXPID* is the experiment identifier, the experiment you want to run.

*MEMBERS* is the selected subset of members. Format `"member1 member2 member2"`, example: `"fc0 fc1 fc2"`.

Then, your experiment will start running jobs belonging to those members only. If the experiment was previously running and autosubmit was stopped when some jobs belonging to other members (not the ones from your input) where running, those jobs will be tracked and finished in the new exclusive run.

Furthermore, if you wish to run a sequence of only members execution; then, instead of running `autosubmit run -rm "member_1"` ... `autosubmit run -rm "member_n"`, you can make a bash file with that sequence and run the bash file. Example:
::

    #!/bin/bash
    autosubmit run EXPID -rm MEMBER_1
    autosubmit run EXPID -rm MEMBER_2
    autosubmit run EXPID -rm MEMBER_3
    ...
    autosubmit run EXPID -rm MEMBER_N




