def get_entries(url,source,weekday,series,team,httpproxy=None):
    """
    Args:
        source      string.
        url         string.
        httpproxy   string.

    Return:
        entries     list. A list of items and the type of items is dict.

    """
    if source == 'share_dmhy_org':
        from rssparser.share_dmhy_org import get_entries
    elif source == 'share_xfsub_com':
        from rssparser.share_xfsub_com import get_entries
    elif source == 'share_acgnx_se':
        from rssparser.share_acgnx_se import get_entries
    elif source == 'bangumi_moe':
        from rssparser.bangumi_moe import get_entries
    return get_entries(url,source,weekday,series,team,httpproxy=httpproxy)
