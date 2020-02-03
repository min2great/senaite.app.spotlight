# -*- coding: utf-8 -*-

from operator import itemgetter

from bika.lims import api
from bika.lims.catalog import CATALOG_ANALYSIS_REQUEST_LISTING
from bika.lims.catalog import CATALOG_WORKSHEET_LISTING
from bika.lims.catalog import SETUP_CATALOG
from plone.memoize import forever
from senaite.core.spotlight.interfaces import ISpotlightSearchAdapter
from zope.interface import implementer
from zope.interface import implements

CATALOGS = [
    "portal_catalog",
    CATALOG_ANALYSIS_REQUEST_LISTING,
    SETUP_CATALOG,
    CATALOG_WORKSHEET_LISTING,
]


@implementer(ISpotlightSearchAdapter)
class SpotlightSearchAdapter(object):
    """Spotlight Search Adapter
    """
    implements(ISpotlightSearchAdapter)

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def __call__(self):
        search_results = []
        for catalog in CATALOGS:
            search_results.extend(search(catalog=catalog))

        # extract the data from all the brains
        items = map(get_brain_info, search_results)

        return {
            "count": len(items),
            "items": sorted(items, key=itemgetter("title")),
        }


def get_brain_info(brain):
    """Extract the brain info
    """
    icon = api.get_icon(brain)
    # avoid 404 errors with these guys
    if "document_icon.gif" in icon:
        icon = ""

    id = api.get_id(brain)
    url = api.get_url(brain)
    title = api.get_title(brain)
    description = api.get_description(brain)
    parent = api.get_parent(brain)
    parent_title = api.get_title(parent)
    parent_url = api.get_url(parent)

    return {
        "id": id,
        "title": title,
        "title_or_id": title or id,
        "description": description,
        "url": url,
        "parent_title": parent_title,
        "parent_url": parent_url,
        "icon": icon,
    }


def search(query=None, catalog=None):
    """Search
    """
    if query is None:
        query = make_query(catalog)
    if query is None:
        return []
    return api.search(query, catalog=catalog)


@forever.memoize
def get_search_index_for(catalog):
    """Returns the search index to query
    """
    searchable_text_index = "SearchableText"
    listing_searchable_text_index = "listing_searchable_text"

    if catalog == CATALOG_ANALYSIS_REQUEST_LISTING:
        tool = api.get_tool(catalog)
        indexes = tool.indexes()
        if listing_searchable_text_index in indexes:
            return listing_searchable_text_index

    return searchable_text_index


def make_query(catalog):
    """A function to prepare a query
    """
    query = {}
    request = api.get_request()
    index = get_search_index_for(catalog)
    limit = request.form.get("limit")

    q = request.form.get("q")
    if len(q) > 0:
        query[index] = q + "*"
    else:
        return None

    portal_type = request.form.get("portal_type")
    if portal_type:
        if not isinstance(portal_type, list):
            portal_type = [portal_type]
        query["portal_type"] = portal_type

    if limit and limit.isdigit():
        query["sort_limit"] = int(limit)

    return query
