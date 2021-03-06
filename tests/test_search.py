import pytest
from common.session import session
from views.search import search


@pytest.fixture (scope='session')
def web_session(request):
    web_session = session(add_provider=True)

    def closeSession():
        web_session.logger.info("Close browser session")
        web_session.close_web_driver()
    request.addfinalizer(closeSession)

    return web_session

def test_cfui_simple_search_provider(web_session):
    web_session.logger.info("Begin test - search by name on provider list page")
    assert search(web_session).simple_search_provider()

def test_cfui_simple_search_domain(web_session):
    web_session.logger.info("Begin test - search by name on domain list page")
    assert search(web_session).simple_search_domain()

def test_cfui_simple_search_server(web_session):
    web_session.logger.info("Begin test - search by name on server list page")
    assert search(web_session).simple_search_server()

def test_cfui_simple_search_deployments(web_session):
    web_session.logger.info("Begin test - search by name on deployments list page")
    assert search(web_session).simple_search_deployments()

def test_cfui_simple_search_datasources(web_session):
    web_session.logger.info("Begin test - search by name on datasources list page")
    assert search(web_session).simple_search_datasources()

def test_cfui_simple_search_messagings(web_session):
    web_session.logger.info("Begin test - search by name on messagings list page")
    assert search(web_session).simple_search_messagings()

def test_cfui_save_advanced_search(web_session):
    web_session.logger.info("Begin save search filter test")
    assert search(web_session).save_advanced_search()

def test_cfui_apply_advanced_search(web_session):
    web_session.logger.info("Begin apply saved filter test")
    assert search(web_session).apply_advanced_search()

def test_cfui_clear_advanced_search(web_session):
    web_session.logger.info("Begin clear saved filter test")
    assert search(web_session).clear_advanced_search()

def test_cfui_delete_saved_search(web_session):
    web_session.logger.info("Begin delete search filter test")
    assert search(web_session).delete_saved_search()
