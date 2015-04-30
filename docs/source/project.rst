####################
Developing a project
####################
 
Since Autosubmit 2.2 the user can select the desired source GIT repository for the model, the templates and the ocean diagnostics and using a given concrete branch is possible.
This introduce a better version control system for the templates and model sources and more options to create new experiments based on different developments by the user

Templates has a set of subfolders for the different models (ecearth -version 2-, ecearth3, nemo, ifs -version 2-, ifs3) and one common subfolder.
The different subfolders contain the body files, i.e. the shell script to run, for each job type (setup, init, sim, post, clean and trans) that are platform independent.
Additionally the user can modify the sources under proj folder.
A first setup job will take care of transferring the modified sources at HPC, re-compiling the model and preparing new set of executables.
On the other hand, a second setup job will prepare the executables which already exist at HPC.
The executable scripts are created at runtime so the modifications on the sources can be done on the fly.

For developing under GIT, please have a look at these presentations:


	http://ic3.cat/wikicfu/images/ASandGIT.pdf

	http://ic3.cat/wikicfu/images/AS23andGIT.pdf
