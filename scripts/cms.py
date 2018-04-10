#!/usr/bin/env python3 

import os
import sys
from cmd import Cmd
from datetime import datetime
import getdata
import save_stats
import session_stats
import subprocess

class MyCmd(Cmd):

    def __init__(self, working_dir, outxls, prompt='> '):
        # initialize the base class
        Cmd.__init__(self)

        # set class vars
        self.working_dir = working_dir
        self.outxls = os.path.join(self.working_dir, outxls)
        self.pickles = {}
        self.prompt = '(CMS) '
        self.intro = '%s\n\tCUAHSI Metrics Shell\n%s' + \
                     '\nEnter a command or "help" to list options' + \
                     (40*'-')

    def do_collect_hs_data(self, args):
        """
        Collect metrics data for HydroShare
        usage: collect_hs_data
        - no args
        """

        res = getdata.get_stats_data(dirname=self.working_dir)
        self.pickles = res

#    def do_set_output_xls(self, args):
#        path = os.path.join(self.working_dir, args.strip())
#        if path == '':
#            print('invalid input arguments.')
#            print('see \'help save_to_xls\' for more info')
#            return
#
#        # check that outpath is in the correct format
#        if path[-3:] != 'xlsx':
#            print('Argument must have the \'xlsx\' extension, e.g. mydata.xlsx')
#            print('see \'help save_to_xls\' for more info')
#            return
#
#        print('\n\tcurrent output xls path is %s' % (self.outxls))

#    def do_save_to_xls(self, args):
#        """
#        Save summarized metrics data to excel file. The output will be saved
#        in the working directory.
#
#        usage: save_to_xls
#        - no args
#        """
#
#        # save user data, check that pickle files exist before saving
#        if not os.path.exists(os.path.join(self.working_dir, 'users.pkl')):
#            print('\n\tcould not find \'users.pkl\', skipping.'
#                  '\n\trun \'collect_hs_data\' to retrieve these missing data')
#        else:
#            # call the save function
#            save_stats.save_anon_users(self.working_dir, self.outxls)
#
#        # save resource data, check that pickle files exist before saving
#        if not os.path.exists(os.path.join(self.working_dir, 'resources.pkl')):
#            print('\n\tcould not find \'resources.pkl\', skipping.'
#                  '\n\trun \'collect_hs_data\' to retrieve these missing data')
#        else:
#            # call the save function
#            save_stats.save_anon_resources(self.working_dir, self.outxls)

    def do_calculate_session_stats(self, args):
        """
        Calculate session statistics from activity logs.

        usage: calculate_session_stats [a] [b]
        - a: start date, MM-DD-YYYY
        - b: end date, MM-DD-YYYY
        """

        # parse the start and end dates
        dates = args.split()
        if len(dates) < 2:
            print('\n\tnot enough arguments')
            return

        # check date formats
        try:
            st = datetime.strptime(dates[0].strip(), '%m-%d-%Y')
            et = datetime.strptime(dates[1].strip(), '%m-%d-%Y')
        except ValueError:
            print('\tincorrect date format')
            return

        # save user data, check that pickle files exist before saving
        if not os.path.exists(os.path.join(self.working_dir, 'activity.pkl')):
            print('\n\tcould not find \'activity.pkl\', skipping.'
                  '\n\trun \'collect_hs_data\' to retrieve these missing data')
            return

        # generate statistics
        session_stats.sessions_by_month(self.working_dir, self.outxls, st, et)
        session_stats.fig_session_by_month(self.working_dir, st, et)
        session_stats.fig_actions_by_university(self.working_dir, st, et)


    def do_cwd(self, workingdir):
        """
        Change working directory to another existing path

        usage: cwd [path]
        - path: an valid filepath

        """

        if not os.path.exists(workingdir):
            print('\n\tpath does not exist: %s' % (workingdir))
        else:
            self.working_dir = workingdir

        print('\n\tcurrent working directory is %s' % (self.working_dir))


#    def do_del(self, name):
#        print('Deleted {}'.format(name))

    def do_ll(self, args):
        """
        List files in your working directory
        """
        result = subprocess.run(['ls', '-l', self.working_dir],
                                stdout=subprocess.PIPE).stdout.decode('utf-8')
        print(result)

    def do_rm(self, args):
        """
        Remove files within the working directory
        """
        fmt_args = []
        for a in args.split(' '):
            # turn all non flags into paths relative to the working dir
            if a[0] != '-':
                a = os.path.join(self.working_dir, a)
            fmt_args.append(a)
            cmd = 'rm ' + ' '.join(fmt_args)
        result = subprocess.Popen(cmd,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE,
                                  shell=True)
        out, err = result.communicate()
        if out != '': print(out.decode('utf-8'))
        if err != '': print(err.decode('utf-8'))

    def do_q(self, args):
        """
        Exits the shell
        """
        raise SystemExit()


if __name__ == "__main__":
    dirname = None
    if len(sys.argv[1:]) > 0:
        if os.path.exists(sys.argv[1]):
            dirname = sys.argv[1]

    if dirname is None:

        # create a directory for these data
        dirname = datetime.now().strftime('%m.%d.%Y')

        i = 2
        while os.path.exists(dirname):
            dirname = dirname[:10] + '_%d' % i
            i += 1
        os.makedirs(dirname)

    app = MyCmd(dirname, 'stats.xlsx')
    app.cmdloop(40*'-' + '\n\tCUAHSI Metrics Shell\n' + 40*'-' +
                '\nEnter a command or "help" to list options' +
                '\n\nA directory for your session has been created at: %s'
                % dirname)
