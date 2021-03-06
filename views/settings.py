from selenium.webdriver.support.color import Color
from common.ui_utils import ui_utils
from common.timeout import timeout
from common.miq_login import miq_login
from common.navigate import navigate

class settings():
    web_session = None
    web_driver = None
    ui_utils = None

    def __init__(self, web_session):
        self.web_session = web_session
        self.web_driver = web_session.web_driver
        self.ui_utils = ui_utils(self.web_session)


    def default_view(self):
        self.navigate_to_settings_default_view()

        assert (self.ui_utils.isTextOnPage("Middleware Providers"))
        assert(self.ui_utils.isTextOnPage("Middleware Servers"))
        assert(self.ui_utils.isTextOnPage("Middleware Deployments"))
        assert(self.ui_utils.isTextOnPage("Middleware Datasources"))
        assert(self.ui_utils.isTextOnPage("Middleware Domains"))
        assert(self.ui_utils.isTextOnPage("Middleware Messaging"))

        return True;

    def validate_providers_default_views(self):

        # Middleware Providers Tile View
        self.navigate_to_settings_default_view()
        view = "a[href*='manageiq_providers_middlewaremanager&view=tile']"
        self.select_view(view)
        self.navigate_to_providers_view()
        assert self.is_tile_view_selected()

        # Middleware Providers Grid View
        self.navigate_to_settings_default_view()
        view = "a[href*='manageiq_providers_middlewaremanager&view=grid']"
        self.select_view(view)
        self.navigate_to_providers_view()
        assert self.is_grid_view_selected()

        # Middleware Providers List View
        self.navigate_to_settings_default_view()
        view = "a[href*='manageiq_providers_middlewaremanager&view=list']"
        self.select_view(view)
        self.navigate_to_providers_view()
        assert self.is_list_view_selected()

        return True

    def validate_servers_default_views(self):

        # Middleware Servers Tile View
        self.navigate_to_settings_default_view()
        view = "a[href*='middlewareserver&view=tile']"
        self.select_view(view)
        self.navigate_to_servers_view()
        assert self.is_tile_view_selected()

        # Middleware Servers Grid View
        self.navigate_to_settings_default_view()
        view = "a[href*='middlewareserver&view=grid']"
        self.select_view(view)
        self.navigate_to_servers_view()
        assert self.is_grid_view_selected()

        # Middleware Servers List View
        self.navigate_to_settings_default_view()
        view = "a[href*='middlewareserver&view=list']"
        self.select_view(view)
        self.navigate_to_servers_view()
        assert self.is_list_view_selected()
        return True

    def validate_deployments_default_views(self):

        # Middleware Deployments Tile View
        self.navigate_to_settings_default_view()
        view = "a[href*='middlewaredeployment&view=tile']"
        self.select_view(view)
        self.navigate_to_deployments_view()
        assert self.is_tile_view_selected()

        # Middleware Deployments Grid View
        self.navigate_to_settings_default_view()
        view = "a[href*='middlewaredeployment&view=grid']"
        self.select_view(view)
        self.navigate_to_deployments_view()
        assert self.is_grid_view_selected()

        # Middleware Deployments List View
        self.navigate_to_settings_default_view()
        view = "a[href*='middlewaredeployment&view=list']"
        self.select_view(view)
        self.navigate_to_deployments_view()
        assert self.is_list_view_selected()

        return True

    def validate_datasources_default_views(self):

        # Middleware Datasources Tile View
        self.navigate_to_settings_default_view()
        view = "a[href*='middlewaredatasource&view=tile']"
        self.select_view(view)
        self.navigate_to_datasources_view()
        assert self.is_tile_view_selected()

        # Middleware Datasources Grid View
        self.navigate_to_settings_default_view()
        view = "a[href*='middlewaredatasource&view=grid']"
        self.select_view(view)
        self.navigate_to_datasources_view()
        assert self.is_grid_view_selected()

        # Middleware Datasources List View
        self.navigate_to_settings_default_view()
        view = "a[href*='middlewaredatasource&view=list']"
        self.select_view(view)
        self.navigate_to_datasources_view()
        assert self.is_list_view_selected()

        return True

    def validate_messagings_default_views(self):

        # Middleware Messagings Tile View
        self.navigate_to_settings_default_view()
        view = "a[href*='middlewaremessaging&view=tile']"
        self.select_view(view)
        self.navigate_to_messagings_view()
        assert self.is_tile_view_selected()

        # Middleware Messagings Grid View
        self.navigate_to_settings_default_view()
        view = "a[href*='middlewaremessaging&view=grid']"
        self.select_view(view)
        self.navigate_to_messagings_view()
        assert self.is_grid_view_selected()

        # Middleware Messagings List View
        self.navigate_to_settings_default_view()
        view = "a[href*='middlewaremessaging&view=list']"
        self.select_view(view)
        self.navigate_to_messagings_view()
        assert self.is_list_view_selected()

        return True

    def validate_settings_after_relogin(self):
        self.navigate_to_settings_default_view()
        # Set Provider Tile View & Save
        self.navigate_to_settings_default_view()
        view = "a[href*='manageiq_providers_middlewaremanager&view=tile']"
        self.select_view(view)

        # Logout / Login
        miq_login(self.web_session).logout()
        miq_login(self.web_session).login(self.web_session.MIQ_USERNAME, self.web_session.MIQ_PASSWORD)

        # Validate Provider Tile View still set correctly:
        self.navigate_to_providers_view()
        assert self.is_tile_view_selected()

        return True

    def select_view(self, view):
        try:
            self.web_driver.find_element_by_css_selector(view).click()
            self.click_save_button()
        except:
            pass

    # Note:
    #   Selected icon color: blue(ish) = #0099d3 (hex)
    #   Non-selected icon color: black = #252525 (hex)

    def is_grid_view_selected(self):
        self.wait_for_icon_present('view_grid')

        with timeout(seconds=15, error_message="Timed out waiting Grid View to be selected."):
            while True:
                try:
                    grid, tile, list = self.get_view_color_values()
                    if grid < tile and grid < list:
                        return True
                except:
                    self.web_session.logger.debug("Grid View Icon Not Selected")
                    self.ui_utils.sleep(1)
                    pass

        return False

    def is_tile_view_selected(self):
        self.wait_for_icon_present('view_tile')

        with timeout(seconds=15, error_message="Timed out waiting Tile View to be selected."):
            while True:
                try:
                    grid, tile, list = self.get_view_color_values()
                    if tile < grid and tile < list:
                        return True
                except:
                    self.web_session.logger.debug("Tile View Icon Not Selected")
                    self.ui_utils.sleep(1)
                    pass

        return False

    def is_list_view_selected(self):
        self.wait_for_icon_present('view_list')

        with timeout(seconds=15, error_message="Timed out waiting List View to be selected."):
            while True:
                try:
                    grid, tile, list = self.get_view_color_values()
                    if list < grid and list < tile:
                        return True
                except:
                    self.web_session.logger.debug("List View Icon Not Selected")
                    self.ui_utils.sleep(1)
                    pass

        return False

    def get_view_color_values(self):
        grid = Color.from_string(self.web_driver.find_element_by_name("view_grid").value_of_css_property('color')).hex
        tile = Color.from_string(self.web_driver.find_element_by_name("view_tile").value_of_css_property('color')).hex
        list = Color.from_string(self.web_driver.find_element_by_name("view_list").value_of_css_property('color')).hex

        self.web_session.logger.debug("grid: {}  tile: {}  list: {}".format(grid, tile, list))

        return grid, tile, list

    def click_save_button(self):
        with timeout(seconds=15, error_message="Timed out waiting for Save."):
            while True:
                try:
                    self.web_driver.find_element_by_id('save').click()
                    break
                except:
                    # self.web_session.logger.debug("Settings Save Failed")
                    self.ui_utils.sleep(1)
                    pass

    def wait_for_icon_present(self, view_icon):
        with timeout(seconds=15, error_message="Failed to locate {} icon".format(view_icon)):
            while True:
                try:
                    self.web_driver.find_element_by_id(view_icon).is_displayed
                    break
                except:
                    self.web_session.logger.debug("{} Not Displayed".format(view_icon))
                    self.ui_utils.sleep(1)
                    pass

    def navigate_to_settings_default_view(self):
        navigate(self.web_session).get("{}/configuration/index".format(self.web_session.MIQ_URL))
        self.ui_utils.waitForTextOnPage("Default Views", 15)
        self.web_driver.find_element_by_xpath("//*[contains(text(),'Default View')]").click()
        self.ui_utils.waitForTextOnPage("Middleware Providers", 15)

    def navigate_to_providers_view(self):
        navigate(self.web_session).get("{}//ems_middleware/show_list".format(self.web_session.MIQ_URL))
        self.ui_utils.waitForTextOnPage("Middleware Providers", 15)

    def navigate_to_servers_view(self):
        navigate(self.web_session).get("{}//middleware_server/show_list".format(self.web_session.MIQ_URL))
        self.ui_utils.waitForTextOnPage("Middleware Servers", 15)

    def navigate_to_deployments_view(self):
        navigate(self.web_session).get("{}//middleware_deployment/show_list".format(self.web_session.MIQ_URL))
        self.ui_utils.waitForTextOnPage("Middleware Deployments", 15)

    def navigate_to_datasources_view(self):
        navigate(self.web_session).get("{}//middleware_datasource/show_list".format(self.web_session.MIQ_URL))
        self.ui_utils.waitForTextOnPage("Middleware Datasources", 15)

    def navigate_to_domains_view(self):
        navigate(self.web_session).get("{}//middleware_domain/show_list".format(self.web_session.MIQ_URL))
        self.ui_utils.waitForTextOnPage("Middleware Domains", 15)

    def navigate_to_messagings_view(self):
        navigate(self.web_session).get("{}//middleware_messaging/show_list".format(self.web_session.MIQ_URL))
        self.ui_utils.waitForTextOnPage("Middleware Messagings", 15)
