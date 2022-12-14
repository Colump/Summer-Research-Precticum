#!/bin/bash
# jt_scheduler.sh; Wrapper script to start, stop and display the jt_scheduler.sh job
#
# The cron utility runs based on commands specified in a cron table (crontab).
# The crontab does not exist for a user by default.
# It can be created in the /var/spool/cron/crontabs directory using the
# 'crontab -e' command that's also used to edit a cron file.
#
# To check, start, stop Cron on Ubuntu you can use:
#    sudo service cron status
#    sudo service cron stop
#    sudo service cron start
#    sudo service cron restart

# Set up home directory and include shared resources
home_dir="/home/student"
# I popped the following into variables as it was handier for testing
cron_dir="/etc/cron.d"
#cron_dir="/etc/cron.d"
jt_gtfs_loader_module="jt_dl"
jt_model_update="curl -s https://api.journeyti.me/update_model_list.do"

# Helper function - save me keying command summary twice, ensures consistancy in
# user docs (such as they are)
function echoClientCommandDocs() {
    #cmdMsg="jt_scheduler.sh Commands Processed:\n"
    cmdMsg="  \e[3mhelp\e[0m - See this help text\n"
    cmdMsg+="  \e[3mshow\e[0m - Show the current state of the Cron table\n"
    cmdMsg+="  \e[3mschedule\e[0m - Schedule the JT_Scheduled_Tasks to run, using default timings\n"
    cmdMsg+="  \e[3mstop\e[0m - Remove the JT_Scheduled_Tasks from the Cron scheduler\n"
    echo -e "$cmdMsg"
}

# First - check our arguments:
function usage() {
    # Function 'usage()'' expects two arguments.
    #   -> $1 the error status we will exit with
    #   -> $2 the error message to display

    # Formatting from: https://misc.flogisoft.com/bash/tip_colors_and_formatting
    #   echo -e "\e[1mbold\e[0m"
    #   echo -e "\e[3mitalic\e[0m"
    #   echo -e "\e[3m\e[1mbold italic\e[0m"
    #   echo -e "\e[4munderline\e[0m"
    #   echo -e "\e[9mstrikethrough\e[0m"
    echo -e "$2\n\e[1mUsage\e[0m:"
    echoClientCommandDocs  # Not sure whether to include this here........
    #
    # For our mission-critical server process, we don't exit if there's a bad
    # request. We just log it and continue. Given the command-line nature of
    # this application, aborting seems overkill!
    exit "$1"  # exit with error status
}
if [ -z "$1" ]; then
    usage 1 "jt_scheduler.sh: ERROR You must supply an instruction.";
fi

#===============================================================================
#===============================================================================

# We clear the terminal, removes any clutter, hopefully helps the user
clear

# Check if the user supplied command is a valid command.
case "$1" in  # CASE_ClientOrServer?
help)
    # help: print a list of supported commands
    echo -e "jt_scheduler.sh: The JT_Scheduled_Tasks supports the following Commands:"
    echoClientCommandDocs
    ;;
show)
    # show: print out the current crontab table
    #crontab -l
    if [ -e "${cron_dir}/jt_scheduled_tasks" ]; then
        echo "jt_scheduler.sh: The current state of the Crontab is as follows:"
        cat "${cron_dir}/jt_scheduled_tasks"
    else
        echo "jt_scheduler.sh: ERROR schedule not found! Aborting..."
        exit 1
    fi
    ;;
schedule)
    # schedule
    
    # We're using a custom timer file in the cron.d directory rather than the
    # crontab as it's much easier to automate...
    echo "jt_scheduler.sh: Creating cron file..."
    touch "${cron_dir}/jt_scheduled_tasks"
    #
    # To define the time we have to provide concrete values for:
    #   minute (m)
    #   hour (h)
    #   day of month (dom)
    #   month (mon)
    #   day of week (dow)
    #   username (name of the user to run the command)
    # ... or use '*' in these fields (for 'any').
    echo "                     Generating default schedule entries..."
    #
    # NOTE: You'll notice we're just cron'ing the 'DWMB Scheduled Tasks'.  This assumes:
    #   -> That the DWMB Scheduled tasks are *installed* and configured as commands (enpoints in Setup.py)
    #   -> That the project conda virtual environment 'comp47360py39_jt' is configured
    #   -> That dudewmb.json (with our credentials) are available in the account login directory
    #   -> *** SUPER IMPORTANT *** That the ".bashrc_conda" script is available
    #      in the student home directory (the conda environments won't work without it)
    echo "SHELL=/bin/bash" >> "${cron_dir}/jt_scheduled_tasks"
    echo "BASH_ENV=~/.bashrc_conda" >> "${cron_dir}/jt_scheduled_tasks"
    echo "0 4 * * * student conda activate comp47360py39_jt && ${jt_gtfs_loader_module} >> ${home_dir}/jt_scheduled_tasks.log 2>&1 && conda deactivate" >> "${cron_dir}/jt_scheduled_tasks"
    # Should we be logging the following? Or should we dump to /dev/null...??
    echo "0 * * * * student conda activate comp47360py39_jt && ${jt_model_update} >> ${home_dir}/jt_scheduled_tasks.log 2>&1 && conda deactivate" >> "${cron_dir}/jt_scheduled_tasks"

    # Make sure there's a new line after the last command - cron seems to like it...
    echo "" >> "${cron_dir}/jt_scheduled_tasks"
    exit 0
    ;;
stop)
    # shutdown: exit with a return code of 0
    echo "jt_scheduler.sh: About to erase the current Crontab..."
    read -r -p "                     Are you sure? [Y/N] " response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]
    then
        #crontab -r
        if [ -e "${cron_dir}/jt_scheduled_tasks" ]; then
            rm "${cron_dir}/jt_scheduled_tasks"
            echo "jt_scheduler.sh: Crontab erased."
        else
            echo "jt_scheduler.sh: ERROR schedule not found! Aborting..."
            exit 1
        fi
    else
        echo "                     Coward! Perhaps you'll have the guts to delete it later..."
    fi
    exit 0
    ;;
*)
    # All other commands  - we just abort...
    errMsg="jt_scheduler.sh: ERROR Bad command. I don't understand \"$1\"\n";
    errMsg+="                     Bad Luck :-(.  You can always try again??";
    echo -e "$errMsg"
    ;;
esac