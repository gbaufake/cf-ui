from common.ui_utils import ui_utils
from hawkular.hawkular_api import hawkular_api
from views.providers import providers
from selenium.webdriver.common.by import By
from common.view import view
from common.ssh import ssh
from common.timeout import timeout
import os
import time
import datetime
import socket
import pytest
from common.db import db
from common.navigate import navigate

class servers():
    web_session = None
    web_driver = None
    ui_utils = None
    hawkular_api = None
    db = None
    MIQ_BASE_VERSION = "master"

    power_stop = {'action':'Stop Server', 'wait_for':'Stop initiated for selected server', 'start_state':'running', 'end_state':None}
    power_restart = {'action': 'Restart Server', 'wait_for': 'Restart initiated for selected server', 'start_state': 'running', 'end_state': 'running'}
    # TO-DO - Validate Start / End states:
    power_reload = {'action': 'Reload Server', 'wait_for': 'Reload initiated for selected server', 'start_state':'running', 'end_state':'running'}
    power_force_reload = {'action': 'Reload Server', 'wait_for': 'Reload initiated for selected server', 'start_state': 'reload-required', 'end_state': 'running'}
    power_graceful_shutdown = {'action': 'Gracefully shutdown Server', 'wait_for': 'Shutdown initiated for selected server', 'start_state':'running', 'end_state':'running'}

    # Note: BZ - EAP currently showing only "running" state:
    power_suspend = {'action': 'Suspend Server', 'wait_for': 'Suspend initiated for selected server', 'start_state':'running', 'end_state':'running'}
    power_resume = {'action': 'Resume Server', 'wait_for': 'Resume initiated for selected server', 'start_state':'running', 'end_state':'running'}

    APPLICATION_WAR = "cfui_test_war.war"
    APPLICATION_JAR = "cfui_test_jar.jar"
    APPLICATION_EAR = "cfui_test_ear.ear"
    JDBCDriver = "postgresql-9.4.1207.jar"
    JDBCDriver_Name = "mypostgres"
    JDBCDriver_Module_Name = "org.postgresql"
    JDBCDriver_Class_Name = "org.postgresql.Driver"
    JDBCDriver_Major_Version = "9"
    JDBCDriver_Minor_Version = "4"
    DatasourceUsernamePasswd = "admin"
    runtime_name = "TestDeployment.jar"

    def __init__(self, web_session):
        self.web_session = web_session
        self.web_driver = web_session.web_driver
        self.ui_utils = ui_utils(web_session)
        self.hawkular_api = hawkular_api(self.web_session)
        self.appliance_version = self.web_session.appliance_version

        try:
            self.db = db(self.web_session)
        except Exception, e:
            self.web_session.logger.warning("Unable to connecto to database. {}".format(e))

    def server_policy_edit(self, server_type):
        origValue = -1
        server = None

        navigate(self.web_session).get("{}/middleware_server/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage(self.web_session.HAWKULAR_PROVIDER_NAME, 10)
        servers_ui = self.ui_utils.get_list_table()
        assert servers_ui, "No servers found."

        if server_type == 'provider':
            server = self.ui_utils.find_row_in_list(servers_ui, 'Product', self.web_session.PROVIDER)
        elif server_type == 'eap':
            for eap in {'WildFly', 'JBoss'}:
                server = self.ui_utils.find_row_in_list(servers_ui, 'Product', eap)
                if server: break

        if not server:
            pytest.skip("No server {} found.".format(server_type))

        # Feed is unique ID for this server
        self.ui_utils.click_on_row_containing_text(server.get('Feed'))
        self.ui_utils.waitForTextOnPage('Relationships', 10)
        server_details = self.ui_utils.get_generic_table_as_dict()
        assert server_details, "No server details found for {}.".format(self.web_session.PROVIDER)

        if not str(server_details.get('My Company Tags')).__contains__("No My Company Tags have been assigned"):
            origValue = int(server_details.get('My Company Tags')[-1:])

        self.web_session.logger.info("Current Company Tags: {}".format(origValue))

        self.web_driver.find_element_by_xpath("//button[@title='Policy']").click()
        self.ui_utils.waitForElementOnPage(By.ID, 'middleware_server_policy_choice__middleware_server_tag', 5)
        self.web_driver.find_element_by_id('middleware_server_policy_choice__middleware_server_tag').click()
        assert self.ui_utils.waitForTextOnPage('Tag Assignment', 5)

        # Click on Drop-down title Name
        tag = '"&lt;Select a value to assign&gt;"'
        self.web_driver.execute_script("return $('*[data-original-title={}]').trigger('click')".format(tag))
        self.ui_utils.sleep(1)

        # Select value - always just select first value in list (list is index):
        # By Browser type - for now - to-do, find a better approach
        if self.web_session.BROWSER == 'Firefox':
            self.web_driver.find_element_by_xpath('//th[3]/div/div/div/ul/li[1]/a').click()
        else:
            tag = 'data-original-index=1'
            el = self.web_driver.execute_script("return $('*[{}]')".format(tag))
            try:
                el[0].click()
            except:
                el[1].click()

        els =  self.web_driver.find_elements_by_xpath("//*[contains(text(), '{}')]".format('Save'))
        el = els[0]
        assert  self.ui_utils.wait_until_element_displayed(el, 10)
        el.click()

        assert self.ui_utils.waitForTextOnPage("My Company Tags", 15)

        server_details = self.ui_utils.get_generic_table_as_dict()
        newValue = server_details.get('My Company Tags')[-1:]

        if newValue != origValue:
            return True
        else:
            return False


    def validate_server_details(self):
        navigate(self.web_session).get("{}/middleware_server/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage(self.web_session.HAWKULAR_PROVIDER_NAME, 10)

        servers_ui = self.ui_utils.get_list_table()
        servers_hawk = self.hawkular_api.get_hawkular_servers()

        for serv_ui in servers_ui:
            feed = serv_ui.get('Feed')  # Unique Server identifier
            navigate(self.web_session).get("{}/middleware_server/show_list".format(self.web_session.MIQ_URL))
            assert self.ui_utils.waitForTextOnPage(self.web_session.HAWKULAR_PROVIDER_NAME, 10)


            self.ui_utils.click_on_row_containing_text(serv_ui.get('Feed'))
            assert self.ui_utils.waitForTextOnPage("Properties", 15)

            server_details_ui = self.ui_utils.get_generic_table_as_dict()
            server_details_hawk = self.ui_utils.find_row_in_list(servers_hawk, 'Feed', feed)

            assert server_details_hawk, "Feed {} not found in Hawkular Server List".format(feed)

            #assert (server_details_ui.get('Product') == server_details_hawk.get("details").get("Product Name")), \
            #        "Product mismatch ui:{}, hawk:{}".format(server_details_ui.get('Product'), server_details_hawk.get("details").get("Product Name"))
            #assert (server_details_ui.get('Version') == server_details_hawk.get("details").get("Version")), \
            #        "Version mismatch ui:{}, hawk:{}".format(server_details_ui.get('Version'), server_details_hawk.get("details").get("Version"))

        return True

    def validate_servers_list(self):
        servers_db = None
        navigate(self.web_session).get("{}/middleware_server/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage(self.web_session.HAWKULAR_PROVIDER_NAME, 10)
        servers_ui = self.ui_utils.get_list_table()
        servers_hawk = self.hawkular_api.get_hawkular_servers()

        if self.db:
            servers_db = self.db.get_servers()
            assert len(servers_ui) == len(servers_hawk) == len(servers_db), "Servers lists size mismatch."
        else:
            assert len(servers_ui) == len(servers_hawk), "Servers lists size mismatch."

        for serv_ui in servers_ui:
            vals = [{'column_name':'Feed', 'value':serv_ui.get('Feed')},
                    {'column_name':'Server Name', 'value':serv_ui.get('Server Name')}]
            serv_hawk = self.ui_utils.find_row_in_list_by_multi_value(servers_hawk, vals)

            assert serv_hawk, "Feed {} not found in Hawkular Server".format(serv_ui.get('Feed'))
            # BZ 1376929 assert (serv_ui.get('Host Name') == serv_hawk.get("details").get("Hostname")), \
            #    "Host Name mismatch ui:{}, hawk:{}".format(serv_ui.get('Feed'), serv_hawk.get("details").get("Hostname"))
            # BZ 1376929 assert (serv_ui.get('Product') == serv_hawk.get("details").get("Product Name")), \
            #    "Product mismatch ui:{}, hawk:{}".format(serv_ui.get('Product'), serv_hawk.get("Product Name"))

        return True

    # BEGIN - EAP Power

    def __get_eap_app_path(self,eap_hawk):

        home_dir = eap_hawk.get('details').get('Home Directory')
        self.web_session.logger.info("EAP Home Directory: {}".format(home_dir))

        return home_dir

    def eap_power_restart(self):

        # Find an EAP in 'start state'
        # Get EAP pid
        # Restart EAP
        # Validate that pid changed

        if self.find_eap_in_state("reload-required"):
            self.force_reload_eap()
            self.navigate_and_refresh_provider()

        power = self.power_restart

        eap_hawk = self.find_eap_in_state(power.get('start_state'))
        assert eap_hawk

        # Example format: Djboss.server.base.dir=/root/wildfly-10.0.0.Final/standalone
        eap_app = "{}{}".format("Djboss.server.base.dir=", self.__get_eap_app_path(eap_hawk))

        #eap_host = eap_hawk.get("details").get("Hostname")
        #ssh_ = ssh(self.web_session, eap_host)
        #orig_pid = ssh_.get_pid(eap_app)

        self.web_session.logger.info("About to Restart EAP server {} Feed {}".format(eap_hawk.get('Product'), eap_hawk.get('Feed')))
        self.eap_power_action(power, eap_hawk)
        self.ui_utils.sleep(5)  # need a timer here

        # new_pid = ssh_.get_pid(eap_app)

        # assert orig_pid != new_pid, "Orig Pid: {}  New Pid: {}".format(orig_pid, new_pid)

        # Validate eap server state on Summary Page in MIQ UI

        if self.appliance_version == self.MIQ_BASE_VERSION:
            self.verify_eap_status_in_ui(eap_hawk, "Running")

        return True

    def eap_power_stop(self):
        pid = None

        power = self.power_stop

        # Find an EAP in 'start state'
        # Get EAP pid (should be a pid)
        # Stop EAP
        # Validate that no pid (EAP has stopped)

        eap_hawk = self.find_eap_in_state(power.get('start_state'), check_if_resolvable_hostname=True)
        pytest.skip("No EAP with Resolvable Hostname found.")

        eap_hostname = eap_hawk.get("details").get("Hostname")
        ssh_ = ssh(self.web_session, eap_hostname)
        # assert ssh_.get_pid(eap_app) != None, "No EAP pid found."

        self.eap_power_action(power, eap_hawk)
        with timeout(15, error_message="Timeout waiting for EAP Standalone server to Stop on host: {}".format(eap_hostname)):
            while True:
                if ssh_.get_pid('standalone.sh') == None:
                    break

        # Validate eap server state on Summary Page in MIQ UI

        if self.appliance_version == self.MIQ_BASE_VERSION:
            self.web_session.logger.info("Verify IN UI")
            self.verify_eap_status_in_ui(eap_hawk, "Down")

        # Start EAP Standalone server, as to leave the EAP server in the starting state

        assert self.start_eap_standalone_server(eap_hawk)

        with timeout(15, error_message="Timeout waiting for EAP Standalone server to Start on host: {}".format(eap_hostname)):
            while True:
                if ssh_.get_pid('standalone.sh') != None:
                    break

        # Validate eap server state on Summary Page in MIQ UI

        if self.appliance_version == self.MIQ_BASE_VERSION:
            self.verify_eap_status_in_ui(eap_hawk, "Running")

        return True

    def eap_power_reload(self):
        power = self.power_reload

        # Find an EAP in 'start state'
        # Reload EAP
        # Validate - TO-DO

        #eap_hawk = self.find_eap_in_state(power.get('start_state'))
        eap_hawk = self.find_eap_in_state(power.get('start_state'), check_if_resolvable_hostname=True)
        assert eap_hawk

        self.eap_power_action(power, eap_hawk)

        # TO-DO - Validate

        return True

    def eap_power_suspend(self):
        power = self.power_suspend

        # Find an EAP in 'start state'
        # Suspend EAP
        # Validate - TO-DO

        #eap_hawk = self.find_eap_in_state(power.get('start_state'))
        eap_hawk = self.find_eap_in_state(power.get('start_state'), check_if_resolvable_hostname=True)
        assert eap_hawk

        self.eap_power_action(power, eap_hawk, alert_button_name='Suspend')

        # TO-DO - Validate

        return True

    def eap_power_resume(self):
        power = self.power_resume
        # 'Resume initiated for selected server(s)'
        # Find an EAP in 'start state'
        # Resume EAP
        # Validate - TO-DO

        #eap_hawk = self.find_eap_in_state(power.get('start_state'))
        eap_hawk = self.find_eap_in_state(power.get('start_state'), check_if_resolvable_hostname=True)
        assert eap_hawk

        self.eap_power_action(power, eap_hawk)

        # TO-DO - Validate

        return True

    def eap_power_graceful_shutdown(self):
        power = self.power_graceful_shutdown

        # Find an EAP in 'start state'
        # Graceful-Shutdown EAP
        # Validate - TO-DO

        eap_hawk = self.find_eap_in_state(power.get('start_state'))
        assert eap_hawk

        self.eap_power_action(power, eap_hawk)

        # TO-DO - Validate

        # Validate eap server state on Summary Page in MIQ UI
        if self.appliance_version == self.MIQ_BASE_VERSION:
            self.verify_eap_status_in_ui(eap_hawk, "Down")

        return True

    def eap_power_action(self, power, eap_hawk, alert_button_name = None):

        self.web_session.logger.info(
            "About to {} EAP server {} Feed {}".format(power.get('action'), eap_hawk.get('Product'), eap_hawk.get('Feed')))

        feed = eap_hawk.get('Feed') # Unique server id

        navigate(self.web_session).get("{}//middleware_server/show_list".format(self.web_session.MIQ_URL))
        self.ui_utils.waitForTextOnPage('Feed', 15)

        self.ui_utils.click_on_row_containing_text(feed)
        assert self.ui_utils.waitForTextOnPage("Properties", 15)

        self.web_driver.find_element_by_xpath("//button[@title='Power']").click()
        self.ui_utils.waitForElementOnPage(By.XPATH, "//a[contains(.,'{}')]".format(power.get('action')), 5)
        self.web_driver.find_element_by_xpath("//a[contains(.,'{}')]".format(power.get('action'))).click()
        self.ui_utils.accept_alert(10, alert_button_name)
        assert self.ui_utils.waitForTextOnPage(power.get('wait_for'), 15)

        # Validate backend - Hawkular
        if power.get('end_state'):
            assert self.wait_for_eap_state(feed, power.get('end_state'), 15)

    def deploy_application_archive(self, app_to_deploy = APPLICATION_WAR):

        navigate(self.web_session).get("{}//middleware_server/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage('Server Name', 20)

        # Find EAP on which to deploy
        eap= self.find_eap_in_state("Running", check_if_resolvable_hostname=True)
        assert eap, "No EAP found in desired state."

        self.ui_utils.click_on_row_containing_text(eap.get('Feed'))
        assert self.ui_utils.waitForTextOnPage('Version', 15)

        self.add_server_deployment(self.APPLICATION_WAR)
        self.navigate_and_refresh_provider()
        self.web_session.logger.info("Waiting for the archive to appear")

        # Validate UI
        navigate(self.web_session).get("{}/middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.refresh_until_text_appears(self.APPLICATION_WAR, 300)

        if not self.appliance_version == self.MIQ_BASE_VERSION:
            self.navigate_and_refresh_provider()
        else:
            self.web_session.logger.info("Waiting for the archive to be enabled")

        navigate(self.web_session).get("{}/middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.refresh_until_text_appears('Enabled', 300)

        # Validate DB
        deployments_db = self.db.get_deployments()
        assert self.ui_utils.find_row_in_list(deployments_db, "name", self.APPLICATION_WAR), "Deployment {} not found in DB.".format(app_to_deploy)

        # Validate HS API
        deployments_hawk = hawkular_api(self.web_session).get_hawkular_deployments()
        assert self.ui_utils.find_row_in_list(deployments_hawk, "Name", self.APPLICATION_WAR), "Deployment {} not found in Hawkular.".format(app_to_deploy)

        return True

    def undeploy_application_archive(self, app_to_undeploy=APPLICATION_WAR):

        navigate(self.web_session).get("{}//middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage('Deployment Name', 20)

        if self.ui_utils.get_elements_containing_text(app_to_undeploy):
            self.ui_utils.click_on_row_containing_text(app_to_undeploy)
        else:
            self.web_session.logger.warning("The archive to undeploy does not exist. Expected: {}".format(app_to_undeploy))
            return True

        # Undeploy
        self.undeploy_server_deployment(app_to_undeploy)
        self.navigate_and_refresh_provider()

        # Validate that application is "Removed from the deployments list"
        navigate(self.web_session).get("{}//middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForElementOnPage(By.XPATH, "//td[contains(.,'{}')]".format(app_to_undeploy), 120,
                                                               exist=False)
        if not self.ui_utils.get_elements_containing_text(app_to_undeploy):
            self.web_session.logger.info("The archive is removed successfully.")

        return True

    def restart_application_archive(self, app_to_redeploy=APPLICATION_WAR):

        # Find EAP with application to redeploy
        navigate(self.web_session).get("{}//middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage('Deployment Name', 20)

        if self.ui_utils.get_elements_containing_text(app_to_redeploy):
            self.ui_utils.click_on_row_containing_text(app_to_redeploy)
        else:
            self.deploy_application_archive()

        # Redeploy

        self.restart_server_deployment(app_to_redeploy)

        if not self.appliance_version == self.MIQ_BASE_VERSION:
            self.navigate_and_refresh_provider()
        else:
            self.web_session.logger.info("Waiting for the archive to be enabled")

        # Validate that application status is enabled:
        # ( Existing issues: https://github.com/ManageIQ/manageiq/issues/9876, Issue#10138 )
        navigate(self.web_session).get("{}//middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage('Deployment Name', 20)
        self.ui_utils.click_on_row_containing_text(app_to_redeploy)
        assert self.ui_utils.refresh_until_text_appears('Enabled', 300)
        return True

    def disable_application_archive(self, app_to_stop=APPLICATION_WAR):

        # Find EAP with application to stop
        navigate(self.web_session).get("{}//middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage('Deployment Name', 20)
        self.ui_utils.click_on_row_containing_text(app_to_stop)

        # Stop the application archive

        self.disable_server_deployment(app_to_stop)

        if not self.appliance_version == self.MIQ_BASE_VERSION:
            self.navigate_and_refresh_provider()
        else:
            self.web_session.logger.info("Waiting for the archive to be disabled")

        # Validate that application status is Disabled:
        # ( Existing issues: https://github.com/ManageIQ/manageiq/issues/10138 )
        navigate(self.web_session).get("{}//middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage('Deployment Name', 20)
        self.ui_utils.click_on_row_containing_text(app_to_stop)
        assert self.ui_utils.refresh_until_text_appears('Disabled', 300)
        return True

    def enable_application_archive(self, app_to_start=APPLICATION_WAR):

        # Find EAP with application to start
        navigate(self.web_session).get("{}//middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage('Deployment Name', 20)
        self.ui_utils.click_on_row_containing_text(app_to_start)

        # Start the application archive

        self.enable_server_deployment(app_to_start)

        if not self.appliance_version == self.MIQ_BASE_VERSION:
            self.navigate_and_refresh_provider()
        else:
            self.web_session.logger.info("Waiting for the archive to be enabled")

        # Validate that application status is Enabled:
        # ( Existing issues: https://github.com/ManageIQ/manageiq/issues/10138 )
        navigate(self.web_session).get("{}//middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage('Deployment Name', 20)
        self.ui_utils.click_on_row_containing_text(app_to_start)
        assert self.ui_utils.refresh_until_text_appears('Enabled', 300)
        return True

    def wait_for_eap_state(self, feed, expected_state, wait_time):
        currentTime = time.time()

        while True:
            servers_hawk = self.hawkular_api.get_hawkular_servers()
            assert servers_hawk, "No Hawkular Servers found."

            eap = self.ui_utils.find_row_in_list(servers_hawk, 'Feed', feed)
            assert eap, "No EAP found for Feed {}".format(feed)
            current_state = eap.get("details").get("Server State")

            if current_state == expected_state:
                self.web_session.logger.info("Feed {} found to be in state {}".format(feed, expected_state))
                break
            else:
                if time.time() - currentTime >= wait_time:
                    self.web_session.logger.error("Timed out waiting for EAP Feed {} to be in state {}, but is in state {}.".format(feed, expected_state, current_state))
                    return False
                else:
                    time.sleep(2)

        return True

    # EAPs that are running in a container will NOT have a resolvable Hostname (Hostname will be either POD or Container ID)
    def find_eap_in_state(self, state, check_if_resolvable_hostname = False):
        rows = self.hawkular_api.get_hawkular_servers()
        for row in rows:
            self.web_session.logger.info("Product: {}  Feed: {}   State: {}".
                            format(row.get("Product Name"), row.get("Feed"), row.get("details").get("Server State")))

            if not row.get("Product Name"):
                self.web_session.logger.warning ("Product Name 'None'. Feed: {}.".format(row.get("Feed")))

            elif (row.get("Product Name") == 'JBoss EAP' or 'wildfly' in row.get("Product Name").lower()) \
                    and row.get("Node Name") != 'master:server-*' \
                    and (state.lower() == "any" or row.get("details").get("Server State") == state.lower()) \
                    and "domain" not in row.get("Feed").lower():

                if check_if_resolvable_hostname:
                    hostname = row.get("details").get("Hostname")
                    try:
                        socket.gethostbyname(hostname)
                        self.web_session.logger.debug("Found resolvable Hostname: {}".format(hostname))
                        return row
                    except:
                        self.web_session.logger.debug("Note a resolvable Hostname: {}".format(hostname))
                else:
                    return row

        return None

    def add_server_deployment(self, app_to_deploy,runtime_name=None, enable_deploy=True, overwrite=False, cancel=False):
        app = "{}/data/{}".format(os.getcwd(), app_to_deploy)

        self.web_session.logger.info("Deploying App: {}".format(app))
        try:
            self.web_driver.find_element_by_xpath("//button[@title='Deployments']").click()
        except:
            self.web_driver.find_element_by_xpath("//*[contains(text(),'Middleware Deployments')]").click()

        self.ui_utils.waitForElementOnPage(By.ID, 'middleware_server_deployments_choice__middleware_deployment_add', 5)
        self.web_driver.find_element_by_id('middleware_server_deployments_choice__middleware_deployment_add').click()
        assert self.ui_utils.waitForTextOnPage('Select the file to deploy', 15)

        el = self.web_driver.find_element_by_id("upload_file")
        el.send_keys(app)
        self.ui_utils.sleep(2)

        if cancel:
            self.web_driver.find_element_by_xpath(".//*[@id='deploy_div']//button[1]").click()

        elif runtime_name:
            self.web_driver.find_element_by_id('runtime_name_input').clear()
            self.web_driver.find_element_by_id('runtime_name_input').send_keys(runtime_name)
            self.web_driver.find_element_by_xpath("//button[@ng-click='addDeployment()']").click()
            assert self.ui_utils.waitForTextOnPage('completed successfully', 15)
            assert self.ui_utils.waitForTextOnPage(
                'Deployment "{}" has been initiated on this server.'.format(runtime_name), 15)


        elif overwrite:
            self.ui_utils.waitForTextOnPage("Add Middleware Deployment", 15)
            self.web_driver.find_element_by_xpath("//label[contains(.,'Overwrite (if exists)')]").click()
            self.web_driver.find_element_by_xpath("//button[@ng-click='addDeployment()']").click()

            assert self.ui_utils.waitForTextOnPage('completed successfully', 15)
            assert self.ui_utils.waitForTextOnPage(
                'Deployment "{}" has been initiated on this server.'.format(app_to_deploy), 15)

        elif not enable_deploy:
            self.web_driver.find_element_by_xpath("//span[contains(.,'Yes')]").click()
            self.web_driver.find_element_by_xpath("//button[@ng-click='addDeployment()']").click()
            assert self.ui_utils.waitForTextOnPage('completed successfully', 15)
            assert self.ui_utils.waitForTextOnPage(
                'Deployment "{}" has been initiated on this server.'.format(app_to_deploy), 15)
        else:
            self.web_driver.find_element_by_xpath("//button[@ng-click='addDeployment()']").click()
            assert self.ui_utils.waitForTextOnPage('completed successfully', 15)
            assert self.ui_utils.waitForTextOnPage(
                'Deployment "{}" has been initiated on this server.'.format(app_to_deploy), 15)

    def undeploy_server_deployment(self, app_to_undeploy = APPLICATION_WAR):
        self.web_session.logger.info("Undeploying App: {}".format(app_to_undeploy))
        self.web_driver.find_element_by_xpath("//button[@title='Operations']").click()
        self.ui_utils.waitForElementOnPage(By.ID, 'middleware_deployment_deploy_choice__middleware_deployment_undeploy', 5)
        self.web_driver.find_element_by_id('middleware_deployment_deploy_choice__middleware_deployment_undeploy').click()
        self.ui_utils.sleep(2)
        self.ui_utils.accept_alert(10)
        assert self.ui_utils.waitForTextOnPage('completed successfully', 15)
        assert self.ui_utils.waitForTextOnPage('Undeployment initiated for selected deployment(s)', 15)

    def restart_server_deployment(self, app_to_redeploy=APPLICATION_WAR):
        self.web_session.logger.info("Redeploying App: {}".format(app_to_redeploy))
        self.web_driver.find_element_by_xpath("//button[@title='Operations']").click()
        self.ui_utils.waitForElementOnPage(By.ID, 'middleware_deployment_deploy_choice__middleware_deployment_restart', 5)
        self.web_driver.find_element_by_id(
            'middleware_deployment_deploy_choice__middleware_deployment_restart').click()
        self.ui_utils.sleep(2)
        self.ui_utils.accept_alert(10)
        assert self.ui_utils.waitForTextOnPage('completed successfully', 15)
        assert self.ui_utils.waitForTextOnPage('Restart initiated for selected deployment(s)', 15)

    def disable_server_deployment(self, app_to_stop=APPLICATION_WAR):
        self.web_session.logger.info("Stopping App: {}".format(app_to_stop))
        self.web_driver.find_element_by_xpath("//button[@title='Operations']").click()
        self.ui_utils.waitForElementOnPage(By.ID, 'middleware_deployment_deploy_choice__middleware_deployment_disable', 5)
        self.web_driver.find_element_by_id(
            'middleware_deployment_deploy_choice__middleware_deployment_disable').click()
        self.ui_utils.sleep(2)
        self.ui_utils.accept_alert(10)
        assert self.ui_utils.waitForTextOnPage('completed successfully', 15)
        assert self.ui_utils.waitForTextOnPage('Disable initiated for selected deployment(s)', 15)

    def enable_server_deployment(self, app_to_start=APPLICATION_WAR):
        self.web_session.logger.info("Starting App: {}".format(app_to_start))
        self.web_driver.find_element_by_xpath("//button[@title='Operations']").click()
        self.ui_utils.waitForElementOnPage(By.ID, 'middleware_deployment_deploy_choice__middleware_deployment_enable', 5)
        self.web_driver.find_element_by_id(
            'middleware_deployment_deploy_choice__middleware_deployment_enable').click()
        self.ui_utils.sleep(2)
        self.ui_utils.accept_alert(10)
        assert self.ui_utils.waitForTextOnPage('completed successfully', 15)
        assert self.ui_utils.waitForTextOnPage('Enable initiated for selected deployment(s)', 15)

    def wait_for_deployment_state(self, deployment_name, state, wait_time):
        currentTime = time.time()
        deployment = None

        self.web_session.logger.info("Wait for Deployment: {} to be in state: ".format(deployment_name, state))

        while True:
            deployments = self.db.get_deployments()
            for row in deployments:
                if deployment_name in row['name']:
                    deployment = row
                    break

            assert deployment, "Deployment: {} not found in DB".format(deployment_name)

            if state.lower() == deployment['status'].lower():
                break
            else:
                if time.time() - currentTime >= wait_time:
                    self.web_session.logger.error(
                        "Timed out waiting for Deployment {} to be in state {}.".format(deployment_name, state))
                    return False
                else:
                    time.sleep(2)

        return True

    def navigate_and_refresh_provider(self):
        navigate(self.web_session).get("{}//ems_middleware/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage('Middleware Providers', 15)
        view(self.web_session).list_View()
        assert self.ui_utils.waitForTextOnPage(self.web_session.HAWKULAR_PROVIDER_NAME, 15)
        self.ui_utils.click_on_row_containing_text(self.web_session.HAWKULAR_PROVIDER_NAME)
        providers(self.web_session).refresh_provider()

    def add_jdbc_driver(self):

        # Adds PostgreSQL JDBC driver to EAP server and validates success message in UI

        navigate(self.web_session).get("{}//middleware_server/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage('Server Name', 20)

        # Find running EAP server
        eap = self.find_eap_in_state("any", check_if_resolvable_hostname=True)
        assert eap, "No EAP found in desired state."

        self.ui_utils.click_on_row_containing_text(eap.get('Feed'))
        assert self.ui_utils.waitForTextOnPage('Version', 15)

        self.deploy_jdbc_driver(self.JDBCDriver)
        self.navigate_and_refresh_provider()

        # TODO : Validate if added JDBC driver is available while creating the datasource
        # Reference bug: https://bugzilla.redhat.com/show_bug.cgi?id=1383426

        self.validate_jdbc_driver()

        return True

    def deploy_jdbc_driver(self, app_to_add=JDBCDriver):
        app = "{}/data/{}".format(os.getcwd(), app_to_add)
        self.web_session.logger.info("Adding PostgreSQL JDBC Driver: {}".format(app))

        self.web_driver.find_element_by_xpath("//button[@title='JDBC Drivers']").click()
        self.ui_utils.waitForElementOnPage(By.ID, 'middleware_server_jdbc_drivers_choice__middleware_jdbc_driver_add', 5)
        self.web_driver.find_element_by_id('middleware_server_jdbc_drivers_choice__middleware_jdbc_driver_add').click()
        assert self.ui_utils.waitForTextOnPage('Select the file to deploy', 15)

        el = self.web_driver.find_element_by_id("jdbc_driver_file")
        el.send_keys(app)
        self.ui_utils.sleep(2)
        self.web_driver.find_element_by_id("jdbc_driver_name_input").send_keys(self.JDBCDriver_Name)
        self.web_driver.find_element_by_id("jdbc_module_name_input").send_keys(self.JDBCDriver_Module_Name)
        self.web_driver.find_element_by_id("jdbc_driver_class_input").send_keys(self.JDBCDriver_Class_Name)
        self.web_driver.find_element_by_id("major_version_input").send_keys(self.JDBCDriver_Major_Version)
        self.web_driver.find_element_by_id("minor_version_input").send_keys(self.JDBCDriver_Minor_Version)

        self.web_driver.find_element_by_xpath("//button[@ng-click='addJdbcDriver()']").click()
        assert self.ui_utils.waitForTextOnPage(
            'JDBC Driver "{}" has been installed on this server.'.format(self.JDBCDriver_Name), 300)

    def add_datasource(self, datasourceName, xa=False):

        # Adds H2 datasource to EAP server, validates success message
        # verifies if the added datasource is listed in datasource list page
        # Add datasource form may change in future to accommodate selection of existing JDBC drivers

        navigate(self.web_session).get("{}//middleware_server/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage('Server Name', 20)

        # Find running EAP server
        eap = self.find_eap_in_state("any", check_if_resolvable_hostname=True)
        assert eap, "No EAP found in desired state."

        self.ui_utils.click_on_row_containing_text(eap.get('Feed'))
        assert self.ui_utils.waitForTextOnPage('Version', 15)

        if xa:
            self.web_session.logger.info("Adding H2-XA datasource")
            self.add_datasource_eap(datasourceName,xa=True)
        else:
            self.web_session.logger.info("Adding H2 datasource")
            self.add_datasource_eap(datasourceName)


        self.navigate_and_refresh_provider()

        # Validate UI if added datasource is available in the datasource list
        # Reference existing bug: https://bugzilla.redhat.com/show_bug.cgi?id=1383414

        navigate(self.web_session).get("{}//middleware_datasource/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.refresh_until_text_appears(datasourceName, 60)

        return True

    def add_datasource_eap(self, datasourceName, xa=False):
        now = datetime.datetime.now()

        self.web_driver.find_element_by_xpath("//button[@title='Datasources']").click()
        self.ui_utils.waitForElementOnPage(By.ID, 'middleware_server_datasources_choice__middleware_datasource_add', 5)
        self.web_driver.find_element_by_id(
            'middleware_server_datasources_choice__middleware_datasource_add').click()
        self.ui_utils.sleep(2)
        assert self.ui_utils.waitForTextOnPage('Create Datasource', 15)

        self.web_driver.find_element_by_xpath("//select[@id='chooose_datasource_input']").click()

        if xa:
            self.web_driver.find_element_by_xpath("//option[@label='H2 XA']").click()
        else:
            self.web_driver.find_element_by_xpath("//label[contains(.,'XA Datasource:')]").click()
            self.web_driver.find_element_by_xpath("//select/option[@value='H2']").click()

        self.ui_utils.waitForElementOnPage(By.XPATH, "//button[@ng-click='vm.addDatasourceChooseNext()']", 5)
        self.web_driver.find_element_by_xpath("//button[@ng-click='vm.addDatasourceChooseNext()']").click()
        self.web_driver.find_element_by_id("ds_name_input").clear()
        self.web_driver.find_element_by_id("ds_name_input").send_keys(datasourceName + str(now.hour) + str(now.minute) + str(now.second))

        self.web_driver.find_element_by_id("jndi_name_input").clear()

        if xa:
            self.web_driver.find_element_by_id("jndi_name_input").send_keys(
                "java:/H2XADS" + datasourceName + str(now.hour) + str(now.minute) + str(now.second))
        else:
            self.web_driver.find_element_by_id("jndi_name_input").send_keys(
                "java:jboss/datasources/H2DS" + datasourceName + str(now.hour) + str(now.minute) + str(now.second))

        self.web_driver.find_element_by_xpath("//button[@ng-click='vm.addDatasourceStep1Next()']").click()
        self.web_driver.find_element_by_xpath("//button[@ng-click='vm.addDatasourceStep2Next()']").click()

        self.web_driver.find_element_by_id("user_name_input").send_keys(self.DatasourceUsernamePasswd)
        self.web_driver.find_element_by_id("password_input").send_keys(self.DatasourceUsernamePasswd)

        self.web_driver.find_element_by_xpath("//button[@ng-click='vm.finishAddDatasource()']").click()
        self.ui_utils.waitForTextOnPage(
            'installation has started on this server.'.format(datasourceName), 15)

    def force_reload_eap(self):
        if self.find_eap_in_state('reload-required'):
            self.web_session.logger.info("Reloading non-container EAP standalone")
            power = self.power_force_reload
            eap_hawk = self.find_eap_in_state('reload-required')
            assert eap_hawk
            self.eap_power_action(power, eap_hawk)
        else:
            self.web_session.logger.info("No Eap server in 'reload-required' state")
        return True

    def add_deployment_disable(self, app_to_deploy=APPLICATION_JAR):

        navigate(self.web_session).get("{}//middleware_server/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage('Server Name', 20)

        # Find EAP on which to deploy
        eap = self.find_eap_in_state("Running", check_if_resolvable_hostname=True)
        assert eap, "No EAP found in desired state."

        self.ui_utils.click_on_row_containing_text(eap.get('Feed'))
        assert self.ui_utils.waitForTextOnPage('Version', 15)

        self.add_server_deployment(self.APPLICATION_JAR, enable_deploy=False)
        self.navigate_and_refresh_provider()
        self.web_session.logger.info("Waiting for the archive to appear")

        # Validate UI
        navigate(self.web_session).get("{}/middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.refresh_until_text_appears(self.APPLICATION_JAR, 300)

        if not self.appliance_version == self.MIQ_BASE_VERSION:
            self.navigate_and_refresh_provider()
        else:
            self.web_session.logger.info("Waiting for the archive to be disabled")
        navigate(self.web_session).get("{}/middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.refresh_until_text_appears('Disabled', 300)

        return True

    def add_deployment_overwrite(self, app_to_deploy=APPLICATION_JAR):

        navigate(self.web_session).get("{}//middleware_server/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage('Server Name', 20)
        eap = self.find_eap_in_state("Running", check_if_resolvable_hostname=True)
        assert eap, "No EAP found in desired state."
        self.ui_utils.click_on_row_containing_text(eap.get('Feed'))
        assert self.ui_utils.waitForTextOnPage('Version', 15)
        self.add_server_deployment(self.APPLICATION_JAR, overwrite=True)
        self.navigate_and_refresh_provider()
        navigate(self.web_session).get("{}/middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.refresh_until_text_appears(self.APPLICATION_JAR, 300)

        if not self.appliance_version == self.MIQ_BASE_VERSION:
            self.navigate_and_refresh_provider()
        else:
            self.web_session.logger.info("Waiting for the archive to be enabled")
        navigate(self.web_session).get("{}/middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.refresh_until_text_appears('Enabled', 300)

        return True

    def add_deployment_runtime_name(self, app_to_deploy=APPLICATION_JAR):

        navigate(self.web_session).get("{}/middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage('Deployment Name', 20)
        if self.ui_utils.get_elements_containing_text(self.APPLICATION_JAR):
            self.undeploy_application_archive(self.APPLICATION_JAR)

        navigate(self.web_session).get("{}//middleware_server/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage('Server Name', 20)
        eap = self.find_eap_in_state("Running", check_if_resolvable_hostname=True)
        assert eap, "No EAP found in desired state."
        self.ui_utils.click_on_row_containing_text(eap.get('Feed'))
        assert self.ui_utils.waitForTextOnPage('Version', 15)
        self.add_server_deployment(self.APPLICATION_JAR, self.runtime_name)
        self.navigate_and_refresh_provider()
        navigate(self.web_session).get("{}/middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.refresh_until_text_appears(self.runtime_name, 300)

        if not self.appliance_version == self.MIQ_BASE_VERSION:
            self.navigate_and_refresh_provider()
        else:
            self.web_session.logger.info("Waiting for the archive to be enabled")

        navigate(self.web_session).get("{}/middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.refresh_until_text_appears('Enabled', 300)
        self.undeploy_application_archive(self.runtime_name)

        return True

    def add_deployment_cancel(self, app_to_deploy=APPLICATION_JAR):
        navigate(self.web_session).get("{}//middleware_server/show_list".format(self.web_session.MIQ_URL))
        eap = self.find_eap_in_state("Running", check_if_resolvable_hostname=True)
        assert eap, "No EAP found in desired state."
        self.ui_utils.click_on_row_containing_text(eap.get('Feed'))
        assert self.ui_utils.waitForTextOnPage('Version', 15)
        self.add_server_deployment(self.APPLICATION_JAR, cancel=True)
        assert self.ui_utils.waitForTextOnPage('Version', 15)

        return True

    def start_eap_standalone_server(self, eap_hawk):
        # Assumption is that the EAP is not running in a container.

        pid = None

        ssh_ = ssh(self.web_session, eap_hawk.get("details").get("Hostname"))
        start_str = 'nohup {}{} -Djboss.service.binding.set=ports-01 -b=0.0.0.0 -bmanagement=0.0.0.0  > /dev/null 2>&1 &\n'.format(self.__get_eap_app_path(eap_hawk), "/bin/standalone.sh")

        self.web_session.logger.debug("About to start EAP: {}".format(start_str))
        result = ssh_.execute_command(start_str).get('result')
        self.web_session.logger.debug("Result: {}".format(result))
        if result == 0:
            pid = ssh_.get_pid('standalone.sh')

        return pid

    def stop_eap_standalone_server(self, eap_hawk):
        # Assumption is that the EAP is not running in a container.

        ssh_ = ssh(self.web_session, eap_hawk.get("details").get("Hostname"))
        result = ssh_.execute_command("kill -9 {}".format(ssh_.get_pid('standalone')))

        return result.get('result')

    def navigate_to_non_container_eap(self):

        navigate(self.web_session).get("{}//middleware_server/show_list".format(self.web_session.MIQ_URL))

        eap = servers(self.web_session).find_eap_in_state("any", check_if_resolvable_hostname=True)
        assert eap, "No EAP found in desired state."

        self.ui_utils.click_on_row_containing_text(eap.get('Feed'))
        assert self.ui_utils.waitForTextOnPage('Version', 15)

        return True

    def verify_eap_status_in_ui(self, eap_hawk, expected_status):

        feed = eap_hawk.get('Feed')

        self.web_session.logger.info("Beginning UI verification")

        navigate(self.web_session).get("{}//middleware_server/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage(feed, 15)
        self.ui_utils.click_on_row_containing_text(feed)
        assert self.ui_utils.waitForTextOnPage("Properties", 15)
        assert self.ui_utils.refresh_until_text_appears(expected_status, 300)
        self.web_session.logger.info("EAP is in {} status".format(expected_status))

    def validate_jdbc_driver(self):

        self.web_session.logger.info("Verify if the jdbc driver is shown while adding datasource")
        navigate(self.web_session).get("{}//middleware_server/show_list".format(self.web_session.MIQ_URL))
        assert self.ui_utils.waitForTextOnPage('Server Name', 20)

        # Find running EAP server
        eap = self.find_eap_in_state("any", check_if_resolvable_hostname=True)
        assert eap, "No EAP found in desired state."

        self.ui_utils.click_on_row_containing_text(eap.get('Feed'))
        assert self.ui_utils.waitForTextOnPage('Version', 15)

        self.web_driver.find_element_by_xpath("//button[@title='Datasources']").click()
        self.ui_utils.waitForElementOnPage(By.ID, 'middleware_server_datasources_choice__middleware_datasource_add', 5)
        self.web_driver.find_element_by_id(
            'middleware_server_datasources_choice__middleware_datasource_add').click()
        self.ui_utils.sleep(2)
        assert self.ui_utils.waitForTextOnPage('Create Datasource', 15)

        self.web_driver.find_element_by_xpath("//select[@id='chooose_datasource_input']").click()

        self.web_driver.find_element_by_xpath("//label[contains(.,'XA Datasource:')]").click()
        self.web_driver.find_element_by_xpath("//option[contains(.,'Postgres')]").click()

        self.ui_utils.waitForElementOnPage(By.XPATH, "//button[@ng-click='vm.addDatasourceChooseNext()']", 5)
        self.web_driver.find_element_by_xpath("//button[@ng-click='vm.addDatasourceChooseNext()']").click()
        self.web_driver.find_element_by_xpath("//button[@ng-click='vm.addDatasourceStep1Next()']").click()
        assert self.ui_utils.waitForTextOnPage('Existing Driver', 15)

        # Verify if the existing Driver dropdown list shows the PostgreSQL driver:
        self.web_driver.find_element_by_xpath("//a[contains(.,'Existing Driver')]").click()
        assert self.ui_utils.waitForTextOnPage('Existing JDBC Driver', 15)
        self.web_driver.find_element_by_xpath("//select[@id='existing_jdbc_driver_input']").click()
        assert self.ui_utils.waitForTextOnPage(self.JDBCDriver_Name, 15)


