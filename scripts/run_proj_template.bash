#!/bin/bash -l


# ================== NOTHING TO CARE ABOUT ==================== #
#  -- Always change directory to the project's root dir         #
# where the script is located. This helps the orientation       #
# of the script relative to the project.                        #
                                                                #
# Get which file was called on the bash command                 #
# e.g.   symlink --or-- original                                #
SOURCE="${BASH_SOURCE[0]}"                                      #
                                                                #
# resolve $SOURCE until the file is no longer a symlink         #
while [ -h "$SOURCE" ];                                         #
do                                                              #
  DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"              #
  SOURCE="$(readlink "$SOURCE")"                                #
                                                                #
  # if $SOURCE was a relative symlink, we need to resolve it    #
  # relative to the path where the symlink file was located     #
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"                  #
done                                                            #
                                                                #
# Form the directory and move there                             #
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"                #
cd $DIR                                                         #
# ============================================================= #
