PAGE_ROUTES = {}


def register_page(name: str, handler):

    PAGE_ROUTES[name] = handler


def get_page(name: str):

    return PAGE_ROUTES.get(name)
