from common.ui_utils import ui_utils
import re
from hawkular.hawkular_api import hawkular_api
from common.db import db
from common.navigate import navigate
from common.timeout import timeout

class topology():
    web_session = None
    web_driver = None
    ui_utils = None
    hawkular_api = None
    MIQ_BASE_VERSION = "master"

    LEGENDS = '//kubernetes-topology-icon'

    entities = {'servers': 'Servers', 'deployments': 'Deployments',
                'datasources': 'Datasources', 'server_groups': 'Server Groups',
                'domains': 'Domains', 'messagings': 'Messaging', 'containers': 'Containers'}

    def __init__(self, web_session):
        self.web_session = web_session
        self.web_driver = web_session.web_driver
        self.ui_utils = ui_utils(self.web_session)
        self.hawkular_api = hawkular_api(self.web_session)
        self.db = db(self.web_session)
        self.appliance_version = self.web_session.appliance_version

    def validate_display_names_checkbox(self, select = True):

        # By default, the MW Provider is always displayed in the Topology
        # Thus, use MW Prover Name for checkbock validation

        provider_name = self.web_session.HAWKULAR_PROVIDER_NAME

        self.__navigate_to_topology__()

        self.__display_names__()

        if not self.__is_name_displayed__(provider_name):
            self.web_session.logger.error("Display Names - {} Not Displayed.".format(provider_name))
            return False

        self.__display_names__(select = False)

        if self.__is_name_displayed__(provider_name):
            self.web_session.logger.error("Display Names - {} Unexpectedly Displayed.".format(provider_name))
            return False

        return True

    def validate_default_topology_view(self):
        provider_name = self.web_session.HAWKULAR_PROVIDER_NAME

        self.web_session.logger.info("Validate that default Topology View displays {}".format(provider_name))

        self.__navigate_to_topology__()

        self.__display_names__(select = True)

        ## To-Do: Deselect "Middleware Servers" and "Middleware Deployments"

        return self.ui_utils.waitForTextOnPage(provider_name, 5)


    def validate_middleware_servers_entities(self):

        # Validate that each Server Name is displayed in Topology:
        # 1) get Servers list (from Servers view)
        # 2) Enable Display Names
        # 3) Enable Middleware Servers entities (by validating whether 1st Server Name in Servers-List is displayed)
        # 4) Validate that each Server in Servers-List is displayed

        self.web_session.logger.info("Validate that Topology View expected Servers")

        servers_list = db(self.web_session).get_servers()
        assert servers_list, "No servers found."

        self.__navigate_to_topology__()
        self.ui_utils.adjust_screen_resolution(1400, 1050)

        self.__display_names__(select=True)

        # Select "Middleware Servers"
        self.__select_entities_view__(self.entities.get('servers'), servers_list[0].get('name'))

        for server in servers_list:
            name = server.get('name')
            assert self.ui_utils.waitForTextOnPage(name, 5), "Server not found in Topology: {}".format(name)

        return True

    def validate_middleware_deployments_entities(self):
        self.web_session.logger.info("Validate that Topology View expected Deployments")

        # Validate that each Deployment is displayed in Topology:
        # 1) Get Deployment list (from Deployments view)
        # 2) Enable Display Names
        # 3) Enable Middleware Deployment entities (by validating whether 1st Deployment Name in Deployment-List is displayed)
        # 4) Validate that each Deployment in Deployments-List is displayed

        deployments_list = self.hawkular_api.get_hawkular_deployments()
        assert deployments_list, "No Deployments found."

        self.__navigate_to_topology__()
        self.ui_utils.adjust_screen_resolution(1400, 1050)

        self.__display_names__(select=True)

        # Select "Middleware Deployments"
        self.__select_entities_view__(self.entities.get('deployments'), self.__get_actual_name__(deployments_list[0].get('Name')))

        for deployment in deployments_list:
            name = self.__get_actual_name__(deployment.get('Name'))
            assert self.ui_utils.waitForTextOnPage(name, 5), "Deployment not found in Topology: {}".format(name)

        return True

    def validate_middleware_datasources_entities(self):
        self.web_session.logger.info("Validate that Topology View expected Datasources")

        # Validate that each Datasource is displayed in Topology:
        # 1) Get Datasource list (from Datasource view)
        # 2) Enable Display Names
        # 3) Enable Middleware Datasource entities (by validating whether 1st Datasource Name in Datasource-List is displayed)
        # 4) Validate that each Datasource in Datasource-List is displayed

        datasources_list = self.hawkular_api.get_hawkular_datasources()
        assert datasources_list, "No Datasources found."

        self.__navigate_to_topology__()
        self.ui_utils.adjust_screen_resolution(1400, 1050)

        self.__display_names__(select=True)

        # Select "Middleware Datasource"
        self.__select_entities_view__(self.entities.get('datasources'), datasources_list[0].get('Name'))

        for datasource in datasources_list:
            name = str(datasource.get('Name'))
            assert self.ui_utils.waitForTextOnPage(name, 5), "Datasource not found in Topology: {}".format(name)

        return True

    def validate_middleware_server_groups_entities(self):
        self.web_session.logger.info("Validate that Topology View expected Server Groups")

        # Validate that each Server Groups is displayed in Topology:
        # 1) Get Server Groups list (from DB)
        # 2) Enable Display Names
        # 3) Enable Middleware Server Groups entities
        # 4) Validate that each Server Groups in Server Groups-List is displayed

        server_groups_list = self.db.get_server_groups()
        if not  server_groups_list:
            self.web_session.logger.warning("No Server Groups found.")
            return True

        self.__navigate_to_topology__()
        self.ui_utils.adjust_screen_resolution(1400, 1050)

        self.__display_names__(select=True)

        # Select "Middleware Deployments"
        self.__select_entities_view__(self.entities.get('server_groups'), server_groups_list[0].get('name'))

        for server_group in server_groups_list:
            name = server_group.get("name")
            assert self.ui_utils.waitForTextOnPage(name, 5), "Server Group not found in Topology: {}".format(name)

        return True

    def validate_middleware_domains_entities(self):
        self.web_session.logger.info("Validate that Topology View expected Domains")

        # Validate that each Domains is displayed in Topology:
        # 1) Get Domains list (from DB)
        # 2) Enable Display Names
        # 3) Enable Middleware Domains entities
        # 4) Validate that each Domains in Domains-List is displayed

        domains_list = self.db.get_domains()
        if not domains_list:
            self.web_session.logger.warning("No Middleware Domains found.")
            return True

        self.__navigate_to_topology__()
        self.ui_utils.adjust_screen_resolution(1400, 1050)

        self.__display_names__(select=True)

        # Select "Middleware Deployments"
        self.__select_entities_view__(self.entities.get('domains'), domains_list[0].get('name'))

        for domain in domains_list:
            name = domain.get("name")
            assert self.ui_utils.waitForTextOnPage(name, 5), "Domain not found in Topology: {}".format(name)

        return True

    def validate_middleware_messaging_entities(self):
        self.web_session.logger.info("Validate that Topology View shows expected JMS Queues/Topics")

        # Validate that each JMS Queue/Topic is displayed in Topology:
        # 1) Get Messaging list (from Messaging view)
        # 2) Enable Display Names
        # 3) Enable Middleware Messaging entities (by validating whether 1st JMS Queue/Topic Name in Messaging-List is displayed)
        # 4) Validate that each JMS Queue/Topic in Messaging-List is displayed

        messaging_list = self.hawkular_api.get_hawkular_messagings()
        assert messaging_list, "No Queues/Topics found."

        self.__navigate_to_topology__()
        self.ui_utils.adjust_screen_resolution(1400, 1050)

        self.__display_names__(select=True)

        # Select "Middleware Messagings-Queues/Entities"
        self.__select_entities_view__(self.entities.get('messagings'),
                                      self.__get_actual_name__(messaging_list[0].get('name')))
        for queues_topics in messaging_list:
            name = self.__get_actual_name__(queues_topics.get('name'))
            assert self.ui_utils.waitForTextOnPage(name, 5), "Messaging not found in Topology: {}".format(name)

        return True

    def validate_middleware_container_entities(self):
        self.web_session.logger.info("Validate that Topology View expected Containers")
        self.__navigate_to_topology__()

        self.__display_names__(select=True)

        entity_name = self.entities.get('containers')
        assert self.ui_utils.isTextOnPage(entity_name), "{} not found".format(self.entities.get('containers'))

        # Select "Containers Entities"
        self.__select_entities_view__(entity_name, 'hawkular-services')

        ## Compair DB and UI until there is a way to determine Container list via Hawkular-API

        containers_db = db(self.web_session).get_container_servers()
        containers_el = self.web_driver.find_elements_by_class_name('Container')

        assert len(containers_db) == len(containers_el)
        for el in containers_el:
            name = el.text.split()[1]
            foundIt = False
            for container in containers_db:
                if name in container.get('feed'):
                    foundIt = True
                    break

            assert foundIt, "Container {} not found in DB Container list.".format(name)

        return True

    def __get_actual_name__(self, text):
        # Filter all but the actual Name. Ex: 'Deployment [hawkular-command-gateway-war.war]'
        return re.match(r"[^[]*\[([^]]*)\]", text).groups()[0]

    def __display_names__(self, select = True):

        if not self.MIQ_BASE_VERSION == self.appliance_version:
            #el = self.web_session.web_driver.find_element_by_xpath('//*[@id="box"]')
            el = self.web_session.web_driver.find_element_by_id('box_display_names')
        else:
            el = self.web_session.web_driver.find_element_by_xpath('//*[@id="box_display_names"]')

        if select and not el.is_selected():
            el.click()

        elif not select and  el.is_selected():
            el.click()

        self.ui_utils.sleep(1)

    def __select_entities_view__(self, entities_to_view, name):

        # Currently, not able to determine if Entity button is already deselected:
        # 1) If "name" is not visible - Entity button already deselected
        # 2) If "name" is visible - Click entity button
        # 3) If "name" still visible - assert

        if self.__is_name_displayed__(name):
            return

        # Click Entities view (aka: buttons "Middleware Servers" or "Middleware Deployments"):
        #  1) Get elements by Name (list of elements)
        #  2) 2nd element contains needed entities element

        self.__get_legond__(entities_to_view).click()

        if self.__is_name_displayed__(name):
            return

        assert False, "Entity button {} unexpectedly displaying entity {}.".format(entities_to_view, name)

    def __deselect_entities_view__(self, entities_to_view, name):

        # Currently, not able to determine if Entity button is already deselected:
        # 1) If "name" is not visible - Entity button already deselected
        # 2) If "name" is visible - Click entity button
        # 3) If "name" still visible - assert

        if not self.__is_name_displayed__(name):
            return

        # Click Entities view (aka: buttons "Middleware Servers" or "Middleware Deployments"):
        #  1) Get elements by Name (list of elements)
        #  2) 2nd element contains needed entities element

        self.__get_legond__(entities_to_view).click()

        if not self.__is_name_displayed__(name):
            return

        assert False, "Entity button {} unexpectedly displaying entity {}.".format(entities_to_view, name)

    def __get_legond__(self, entities_to_view):
        legond = None
        legonds = self.web_session.web_driver.find_elements_by_xpath(self.LEGENDS)

        for e in legonds:
            if e.text == entities_to_view:
                legond = e
                break

        assert legond, "Entity button {} not found.".format(entities_to_view)

        return legond

    def __refresh__(self):
        self.web_driver.find_element_by_class_name('btn-default').click()


    def __is_name_displayed__(self, name):

        # Check if a a Name is displayed:
        #  1) Get elements by Name (list of elements)
        #  2) 2nd element can be checked if "name" is Displayed or not
        el = self.ui_utils.get_elements_containing_text(name)
        if not el:
            return False

        return el[1].is_displayed()

    def __navigate_to_topology__(self):
        navigate(self.web_session).get("{}/middleware_topology/show".format(self.web_session.MIQ_URL))
        self.ui_utils.wait_until_element_displayed(self.web_driver.find_element_by_class_name('btn-default'), 10)