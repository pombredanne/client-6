from __future__ import print_function

from cloudmesh_client.shell.console import Console
from cloudmesh_client.default import Default
from cloudmesh_client.common.Printer import dict_printer
from cloudmesh_client.cloud.iaas.CloudProvider import CloudProvider
from cloudmesh_client.shell.command import command, PluginCommand, CloudPluginCommand
from cloudmesh_client.common.ConfigDict import ConfigDict
from pprint import pprint
from cloudmesh_client.common.dotdict import dotdict
import os
import fnmatch
from cloudmesh_client.util import banner
from cloudmesh_client.util import HEADING

from cloudmesh_client.common.Shell import Shell
from cloudmesh_client.common.dotdict import dotdict
from cloudmesh_client.default import Default


class TestCommand(PluginCommand, CloudPluginCommand):
    topics = {"test": "cloud"}

    def __init__(self, context):
        self.context = context
        if self.context.debug:
            print("init command test")




    # noinspection PyUnusedLocal
    @command
    def do_test(self, args, arguments):
        """
        ::

          Usage:
             test list
             test [TEST] [NUMBER] [--test=TESTER]

          This is an internal command and is ment for developers. If executed, in the source directory,
          it will execute the specified series of tests in the tests directory.
          managing the admins test test test test

          Arguments:
            TEST     the name of the test directory
            NUMBER   the number of a specific test

          Options:
            --test=TESTER   nosetests or py.test. [default: nosetests -v --nocapture]

          Examples:
              cm test var
                  finds the first test that contains var and than executes all tests in it

              cm test var 4
                  finds the first test that contains var and than executes the test with number 004

        """
        pprint(arguments)

        data = dotdict({
            'test': arguments["TEST"],
            'number': arguments["NUMBER"],
            "tester": arguments["--test"]
        })


        def get_file():
            data.file = None
            for file in files:
                if data.test in file:
                    break
            data.file = file


        def run( command):
            command = command.format(**data)
            banner(command, c ="-")
            print (command)
            parameter = command.split(" ")
            shell_command = parameter[0]
            args = parameter[1:]
            result = Shell.execute(shell_command, args)
            print(result)
            return str(result)

        # command = "nosetests -v  --nocapture {0}:{1}.{2}".format(filename, classname, name)

        files = []
        for root, dirnames, filenames in os.walk('tests'):
            for filename in fnmatch.filter(filenames, '*.py'):
                if filename not in ["__init__.py"]:
                    files.append(os.path.join(root, filename))

        if arguments["list"]:
            print ('\n'.join(files))

            # find tests
            return ""


        if data.test is None:
            command = "{tester}"
        elif data.number is None:
            get_file()
            command = "{tester} {file}"
            # run all in that file
            print (data)
        else:
            # run specific test
            get_file()
            # python setup.py install; nosetests -v --nocapture  tests/cm_cloud/test_group.py:Test_group.test_001
            data.basename = os.path.basename(data.file).replace(".py","")
            data.basename = data.basename.replace("test_", "")
            data.number = data.number.zfill(3)
            print (data)

            command = "{tester} {file}:Test_{basename}.test_{number}"

        run(command)

        return ""
