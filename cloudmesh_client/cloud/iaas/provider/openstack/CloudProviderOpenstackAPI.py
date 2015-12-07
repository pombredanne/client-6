import os
from pprint import pprint
from uuid import UUID

from cloudmesh_client.cloud.iaas.CloudProviderBase import CloudProviderBase
from cloudmesh_client.common.todo import TODO
from cloudmesh_client.common.ConfigDict import Config, ConfigDict
from cloudmesh_client.common.FlatDict import FlatDict
from keystoneclient.auth.identity import v3
from keystoneclient import session
from novaclient import client
import requests
import getpass

requests.packages.urllib3.disable_warnings()


# TODO: unset as not allowing to smoothly switch
def set_os_environ(cloudname):
    """Set os environment variables on a given cloudname"""
    # TODO: this has a severe bug as it is not unsetting variables
    # Also this coded duplicates in part from register
    try:
        d = ConfigDict("cloudmesh.yaml")
        credentials = d["cloudmesh"]["clouds"][cloudname]["credentials"]
        for key, value in credentials.iteritems():
            if key == "OS_CACERT":
                os.environ[key] = Config.path_expand(value)
            else:
                os.environ[key] = value
    except Exception, e:
        print(e)


#
# we already have a much better convert to dict function
#

class CloudProviderOpenstackAPI(CloudProviderBase):

    kind = "openstack"

    def __init__(self, cloud_name, cloud_details, user=None, flat=True):
        super(CloudProviderOpenstackAPI, self).__init__(cloud_name, user=user)
        self.initialize(cloud_name, cloud_details)
        self.flat = flat
        self.kind = "openstack"


    def _to_dict(self, openstack_result):
        d = {}
        for index, value in enumerate(openstack_result):
            # print "---"
            d[index] = dict(value.__dict__["_info"])
            if 'links' in d[index]:
                del d[index]['links']
            if 'server_links' in d[index]:
                del d[index]['server_links']

            # If flat dict flag set, convert to flatdict
            if self.flat is True:
                d[index] = dict(FlatDict(d[index]).dict)
            else:
                ValueError("TODO: we only support flat for now")
        return d

    def _ksv3_auth(self, credentials):
        # auth to identity v3
        ksauth = v3.Password(
            auth_url=credentials["OS_AUTH_URL"],
            username=credentials["OS_USERNAME"],
            password=credentials["OS_PASSWORD"],
            project_name=credentials["OS_PROJECT_NAME"],
            user_domain_name=credentials["OS_USER_DOMAIN_ID"],
            project_domain_name=credentials["OS_PROJECT_DOMAIN_ID"])

        return ksauth

    def initialize(self, cloudname, user=None):

        d = ConfigDict("cloudmesh.yaml")
        self.cloud_details = d["cloudmesh"]["clouds"][cloudname]

        # pprint(self.cloud_details)

        self.cloud = cloudname
        self.default_flavor = self.cloud_details["default"]["flavor"]
        self.default_image = self.cloud_details["default"]["image"]
        version = 2
        credentials = self.cloud_details["credentials"]
        cert = False
        if "OS_CACERT" in credentials:
            if credentials["OS_CACERT"] is not False:
                cert = Config.path_expand(credentials["OS_CACERT"])
        auth_url = credentials["OS_AUTH_URL"]
        ksversion = auth_url.split("/")[-1]

        """
        # GitHub issue 101
        # mechanism to interactively ask for password
        # when OS_PASSWORD set as "readline",
        # or read os.environ if set as "env".
        """
        os_password = credentials["OS_PASSWORD"]
        if os_password.lower() == "readline":
            os_password = getpass.getpass()
        elif os_password.lower() == "env":
                os_password = os.environ.get("OS_PASSWORD", getpass.getpass())

        if "v2.0" == ksversion:
            self.provider = client.Client(
                version,
                credentials["OS_USERNAME"],
                os_password,
                credentials["OS_TENANT_NAME"],
                credentials["OS_AUTH_URL"],
                cert)
        elif "v3" == ksversion:
            sess = session.Session(auth=self._ksv3_auth(credentials),
                                   verify=cert)
            self.provider = client.Client(2, session=sess)

    def mode(self, source):
        """
        Sets the source for the information to be returned. "db" and "cloud"
        :param source: the database can be queried in mode "db",
        the database can be bypassed in mode "cloud"
        """
        TODO.implement()

    def list_flavor(self, cloudname, **kwargs):
        return self._to_dict(self.provider.flavors.list())

    def list_image(self, cloudname, **kwargs):
        return self._to_dict(self.provider.images.list())

    def list_vm(self, cloudname, **kwargs):
        vm_dict = self._to_dict(self.provider.servers.list())

        # Extracting and modifying dict with IP details as per the model requirement.
        ip_detail_dict = dict()
        secgroup_list_dict = dict()
        for index in vm_dict:
            ip_detail_dict[index] = dict()
            ip_detail_dict[index]["floating_ip"] = None
            ip_detail_dict[index]["static_ip"] = None
            for key in vm_dict[index]:
                if key.startswith("addresses"):
                    for ip_detail in vm_dict[index][key]:
                        if ip_detail["OS-EXT-IPS:type"] is not None:
                            if ip_detail["OS-EXT-IPS:type"] == "fixed":
                                ip_detail_dict[index]["static_ip"] = ip_detail["addr"]
                            elif ip_detail["OS-EXT-IPS:type"] == "floating":
                                ip_detail_dict[index]["floating_ip"] = ip_detail["addr"]

            secgroup_list_dict[index] = ""

            sec_index = 0
            for secgroup in vm_dict[index]["security_groups"]:
                secgroup_list_dict[index] += secgroup["name"]
                sec_index += 1
                # Append comma if not the last element
                if sec_index < len(vm_dict[index]["security_groups"]):
                    secgroup_list_dict[index] += ","

        for index in vm_dict:
            vm_dict[index]["floating_ip"] = ip_detail_dict[index]["floating_ip"]
            vm_dict[index]["static_ip"] = ip_detail_dict[index]["static_ip"]
            vm_dict[index]["security_ groups"] = secgroup_list_dict[index]

        return vm_dict

    def list_limits(self, tenant, **kwargs):
        return self.provider.limits.get(tenant_id=tenant).__dict__["_info"]

    def list_floating_ips(self, **kwargs):
        return self._to_dict(self.provider.floating_ips.list())

    def list_floating_ip_pools(self, **kwargs):
        return self._to_dict(self.provider.floating_ip_pools.list())

    def list_quota(self, cloudname, **kwargs):
        # pprint(self.provider.__dict__)
        # pprint(dir(self.provider.quotas))
        tenant = self.cloud_details["credentials"]["OS_TENANT_NAME"]
        # print (tenant)
        # pprint(self.provider.quotas.defaults(tenant))
        result = self.provider.quotas.defaults(tenant).__dict__["_info"]
        del result['id']
        return result

    def list_usage(self, cloudname, **kwargs):
        raise ValueError("list usage is not supported")

    def boot_vm(self, name, image=None, flavor=None, cloud="India", key=None,
                secgroup=None, meta=None):
        """
        Spawns a VM instance on the cloud.
        If image and flavor passed as none, it would consider the defaults specified in cloudmesh.yaml.

        :param name: Name of the instance to be started
        :param image: Image id to be used for the instance
        :param flavor: Flavor to be used for the instance
        :param cloud: Cloud on which to spawn the machine. Defaults to 'India'.
        :param key: Key to be used for the instance
        :param secgroup: Security group for the instance
        :param meta: A dict of arbitrary key/value metadata to store for this server
        """
        if image is None:
            image = self.default_image
        if flavor is None:
            flavor = self.default_flavor

        server = self.provider.servers.create(name, image, flavor, meta=meta,
                                              key_name=key,
                                              security_groups=secgroup)
        # return the server id
        return server.__dict__["id"]

    def delete_vm(self, name, group=None, force=None):
        """
        Deletes a machine on the target cloud indicated by the id or name
        :param id: Name or ID of the instance to be deleted
        :param group: Security group of the instance to be deleted
        :param force: Force delete option
        :return:
        """

        if self.isUuid(name):
            server = self.provider.servers.get(name)
        else:
            server = self.provider.servers.find(name=name)

        server.delete()

    def delete_floating_ip(self, floating_ip):
        """
        Method deletes a floating IP address
        :param floating_ip:
        :return: None
        """
        return self.provider.floating_ips.delete(floating_ip)

    def start_vm(self, name, group=None, force=None):
        """
        Starts a suspended machine on the target cloud indicated by the id or name
        :param id: Name or ID of the instance to be deleted
        :param group: Security group of the instance to be deleted
        :param force: Force delete option
        :return:
        """

        if self.isUuid(name):
            server = self.provider.servers.get(name)
        else:
            server = self.provider.servers.find(name=name)

        server.start()

    def stop_vm(self, name, group=None, force=None):
        """
        Stops a machine on the target cloud indicated by the id or name
        :param id: Name or ID of the instance to be deleted
        :param group: Security group of the instance to be deleted
        :param force: Force delete option
        :return:
        """

        if self.isUuid(name):
            server = self.provider.servers.get(name)
        else:
            server = self.provider.servers.find(name=name)

        server.stop()

    def get_ips(self, name, group=None, force=None):
        """
        Returns the ip of the instance indicated by name_or_id
        :param name_or_id:
        :param group:
        :param force:
        :return: IP address of the instance
        """
        if self.isUuid(name):
            server = self.provider.servers.get(name)
        else:
            server = self.provider.servers.find(name=name)

        return self.provider.servers.ips(server)

    def get_floating_ip(self, floating_ip_id):
        """
        Returns the floating ip info associated with floating_ip_id
        :param floating_ip_id:
        :return: floating ip info
        """
        float_ip = self.provider.floating_ips.get(floating_ip_id)
        return float_ip.__dict__["_info"]

    def get_fixed_ip(self, fixed_ip_addr):
        """
        Returns the fixed ip info associated with fixed ip addr
        :param fixed_ip_addr:
        :return: fixed ip info
        """
        fixed_ip = self.provider.fixed_ips.get(fixed_ip_addr)
        return fixed_ip.__dict__["_info"]

    def reserve_fixed_ip(self, fixed_ip_addr):
        """
        Reserves a fixed ip address
        :param fixed_ip_addr:
        :return:
        """
        self.provider.fixed_ips.reserve(fixed_ip_addr)

    def unreserve_fixed_ip(self, fixed_ip_addr):
        """
        Unreserves a fixed ip address
        :param fixed_ip_addr:
        :return:
        """
        self.provider.fixed_ips.unreserve(fixed_ip_addr)

    def create_assign_floating_ip(self, server_name):
        """
        Function creates a new floating ip and associates it with the machine specified.
        :param server_name: Name of the machine to which the floating ip needs to be assigned.
        :return: Floating IP | None if floating ip already assigned.
        """

        float_pool = self.provider.floating_ip_pools.list()[0].name

        floating_ip = self.provider.floating_ips.create(pool=float_pool)
        server = self.provider.servers.find(name=server_name)
        try:
            server.add_floating_ip(floating_ip)
        except Exception, e:
            print (e)
            self.provider.floating_ips.delete(floating_ip)
            return None

        return floating_ip.ip

    def create_floating_ip(self, float_pool):
        """
        Method creates a new floating ip under the specified pool
        :param float_pool:
        :return: Floating IP
        """
        floating_ip = self.provider.floating_ips.create(pool=float_pool)
        return floating_ip.ip

    # TODO: define this
    def get_image(self, **kwargs):

        """
        finds the image based on a query
        TODO: details TBD
        """
        name = kwargs['name']
        if self.isUuid(name):
            return self.provider.images.get(name)._info
        else:
            return self.provider.images.find(name=name)._info

    def isUuid(self, name):
        try:
            UUID(name, version=4)
            return True
        except ValueError:
            return False

    def get_flavor(self, **kwargs):
        """
        finds the flavor based on a query
        TODO: details TBD
        """
        if kwargs['id'].isdigit():
            pass
        else:
            kwargs['name'] = kwargs['id']
            del kwargs['id']
        return self.provider.flavors.find(**kwargs)._info

    def get_vm(self, **kwargs):
        """
        finds the flavor based on a query
        TODO: details TBD
        """
        vm_name = kwargs['name']
        if self.isUuid(vm_name):
            return self.provider.servers.get(vm_name)._info
        else:
            return self.provider.servers.find(name=vm_name)._info

    def attributes(self, kind):
        header = None
        order = None

        layout = {
            'flavor': {
                'order': [
                    'id',
                    'name',
                    'user',
                    'ram',
                    'os_flv_disabled',
                    'vcpus',
                    'swap',
                    'os_flavor_acces',
                    'rxtx_factor',
                    'os_flv_ext_data',
                    'disk',
                    'cloud',
                    'uuid'
                ],
                'header': [
                    'Id',
                    'Name',
                    'User',
                    'RAM',
                    'Disabled',
                    'vCPUs',
                    'Swap',
                    'Access',
                    'rxtx_factor',
                    'os_flv_ext_data',
                    'Disk',
                    'Cloud',
                    'UUID'
                ]
            },
            'image': {
                'order': [
                    'id',
                    'os_image_size',
                    'created',
                    'metadata__description',
                    'minDisk',
                    'minRam',
                    'name',
                    'progress',
                    'status',
                    'updated'
                ],
                'header': [
                    'id',
                    'size',
                    'created',
                    'description',
                    'minDisk',
                    'minRam',
                    'name',
                    'progress',
                    'status',
                    'updated'
                ]
            },
            'vm': {
                'order': None,
                'header': None,
            },
            'floating_ip': {
                'order': [
                    "instance_name",
                    "ip",
                    "pool",
                    "fixed_ip",
                    "id",
                    "instance_id"
                ],
                'header': [
                    "instance_name",
                    "floating_ip",
                    "floating_ip_pool",
                    "fixed_ip",
                    "floating_ip_id",
                    "instance_id"
                ],
            },
            'floating_ip_pool': {
                'order': [
                    "name"
                ],
                'header': [
                    "floating_ip_pool"
                ],
            },
            'limits': {
                'order': [
                    'Name',
                    'Value'
                ],
                'header': [
                    'Name',
                    'Value'
                ]
            },
            'quota': {
                'order': [
                    'Quota',
                    'Limit'
                ],
                'header': [
                    'Quota',
                    'Limit'
                ]
            },
            'default': {
                'order': None,
                'header': None,
            }
        }

        if kind in layout:
            order = layout[kind]["order"]
            header = layout[kind]["header"]
        else:
            order = None
            header = None

        if kind == 'default':
            order = ['user',
                     'cloud',
                     'name',
                     'value',
                     'created_at',
                     'updated_at'
                     ]
        elif kind == 'vm':
            order = [
                'id',
                'uuid',
                'label',
                'status',
                'static_ip',
                'floating_ip',
                'key_name',
                'project',
                'user',
                'cloud'
            ]
            header = [
                'id',
                'uuid',
                'label',
                'status',
                'static_ip',
                'floating_ip',
                'key_name',
                'project',
                'user',
                'cloud'
            ]
        return order, header


# CloudProviderBase.register(CloudProviderOpenstackAPI)

if __name__ == "__main__":
    cloudname = 'juno'
    d = ConfigDict("cloudmesh.yaml")
    cloud_details = d["cloudmesh"]["clouds"][cloudname]

    cp = CloudProviderOpenstackAPI('juno', cloud_details)

    d = {'name': '390792c3-66a0-4c83-a0d7-c81e1c787710'}
    pprint(cp.list_quota('juno'))