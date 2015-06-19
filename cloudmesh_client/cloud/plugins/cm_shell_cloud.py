from __future__ import print_function
from cmd3.shell import command
from pprint import pprint
from cloudmesh_client.common import Config
import os
import os.path
from cloudmesh_client.cloud import command_cloud


class cm_shell_cloud:
    def activate_cm_shell_cloud(self):
        self.register_command_topic('cloud', 'register')

    @command
    def do_register(self, args, arguments):
        """
        ::

          Usage:
              register info
              register list [--yaml=FILENAME]
              register list ssh
              register cat [--yaml=FILENAME]
              register edit [--yaml=FILENAME]
              register form [--yaml=FILENAME]
              register check [--yaml=FILENAME]
              register test [--yaml=FILENAME]
              register rc HOST [OPENRC]
              register [--yaml=FILENAME]

          managing the registered clouds in the cloudmesh.yaml file.
          It looks for it in the current directory, and than in ~/.cloudmesh.
          If the file with the cloudmesh.yaml name is there it will use it.
          If neither location has one a new file will be created in
          ~/.cloudmesh/cloudmesh.yaml. Some defaults will be provided.
          However you will still need to fill it out with valid entries.

          Arguments:

            HOST   the host name
            USER   the user name
            OPENRC  the location of the openrc file

          Options:

             -v       verbose mode

          Description:

              register edit [--yaml=FILENAME]
                  edits the cloudmesh.yaml file

              register list [--yaml=FILENAME]
                  lists the registration yaml file

              register rc HOST [OPENRC]

                    reads the Openstack OPENRC file from a host that is described in ./ssh/config and adds it to the
                    configuration cloudmehs.yaml file. We assume that the file has already a template for this
                    host. If nt it can be created from other examples before you run this command.

                    The hostname can be specified as follows in the ./ssh/config file.

                    Host india
                        Hostname india.futuresystems.org
                        User yourusername

                    If the host is india and the OPENRC file is ommitted, it will automatically fill out the location
                    for the openrc file. To obtain the information from india simply type in

                        register rc india

              register [--yaml=FILENAME]
                  read the yaml file instead of ./cloudmesh.yaml or ~/.cloudmesh/cloudmesh.yaml which is used when the
                  yaml filename is ommitted.

              register edit [--yaml=FILENAME]
                  edits the cloudmesh yaml file

              register form [--yaml=FILENAME]
                  interactively fills out the form wherever we find TBD.

              register check [--yaml=FILENAME]
                  checks the yaml file for completness

              register test [--yaml=FILENAME]
                  checks the yaml file and executes tests to check if we
                  can use the cloud. TODO: maybe this should be in a test
                  command
        """
        pprint(arguments)

        def _get_file(arguments):
            if arguments["--yaml"]:
                filename = Config.find_file(arguments["--yaml"])
            else:
                filename = Config.find_file("cloudmesh.yaml")
            return filename

        if arguments["info"]:
            filename = _get_file(arguments)
            print("File", filename, end=' ')
            if os.path.isfile(filename):
                print("exists")
        elif arguments["cat"]:
            filename = _get_file(arguments)
            os.system("cat {:}".format(filename))
        elif arguments["edit"]:
            filename = _get_file(arguments)
            print("edit", filename)
            self.do_edit(filename)
        elif arguments['list'] and arguments['ssh']:
            print("list ssh")
            command_cloud.list_ssh()
        elif arguments['list']:
            filename = _get_file(arguments)
            print("list", filename)
            command_cloud.list(filename)
        elif arguments['check']:
            filename = _get_file(arguments)
            command_cloud.check_yaml_for_completeness(filename)
        elif arguments['--yaml']:
            filename = arguments['FILENAME']
            print("--yaml", filename)
            command_cloud.register(filename)
        elif arguments['test']:
            filename = _get_file(arguments)
            command_cloud.test(filename)
        elif arguments['form']:
            filename = _get_file(arguments)
            command_cloud.fill_out_form(filename)
        elif arguments['rc']:
            filename = arguments['OPENRC']
            host = arguments['HOST']
            command_cloud.read_rc_file(host, filename)
        pass


if __name__ == '__main__':
    command = cm_shell_register()
    command.do_register("list")