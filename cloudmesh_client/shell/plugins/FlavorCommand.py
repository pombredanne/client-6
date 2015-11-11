from __future__ import print_function
from cloudmesh_client.cloud.flavor import Flavor
from cloudmesh_client.shell.command import command, PluginCommand, CloudCommand
from cloudmesh_client.shell.console import Console
from cloudmesh_client.cloud.default import Default


class FlavorCommand(PluginCommand, CloudCommand):
    topics = {"flavor": "cloud"}

    def __init__(self, context):
        self.context = context
        if self.context.debug:
            print("init command flavor")

    @command
    def do_flavor(self, args, arguments):
        """
        ::

            Usage:
                flavor refresh [--cloud=CLOUD]
                flavor list [ID] [--cloud=CLOUD] [--format=FORMAT] [--refresh]

                This lists out the flavors present for a cloud

            Options:
               --format=FORMAT  the output format [default: table]
               --cloud=CLOUD    the cloud name
               --refresh        refreshes the data before displaying it
                                from the cloud

            Examples:
                cm flavor refresh
                cm flavor list
                cm flavor list --format=csv
                cm flavor show 58c9552c-8d93-42c0-9dea-5f48d90a3188 --refresh

        """

        cloud = arguments["--cloud"] or Default.get_cloud()
        if cloud is None:
            Console.error("Default cloud doesn't exist")
            return

        if arguments["refresh"]:
            msg = "Refresh flavor for cloud {:}.".format(cloud)
            if Flavor.refresh(cloud):
                Console.ok("{:} ok".format(msg))
            else:
                Console.error("{:} failed".format(msg))
            return ""

        if arguments["list"]:
            id = arguments['ID']
            refresh = arguments['--refresh']
            output_format = arguments["--format"]

            if id is None:
                result = Flavor.list(cloud, output_format)
            else:
                result = Flavor.details(cloud, id, refresh, output_format)

            if result is None:
                #
                # outo refresh
                #
                Console.error("No flavor(s) found. Failed")
                # Flavor.refresh(cloud)
                # Console.ok("Refreshing flavor(s). ok.")

            else:

                print(result)
            return ""
