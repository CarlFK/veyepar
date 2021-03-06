import urllib
import urllib.parse
import re
# from urllib.parse import urlparse, parse_qs

import mwparserfromhell
import requests


def one_page(conf_url):

    parsed = urllib.parse.urlparse(conf_url)

    www = "{scheme}://{netloc}".format(scheme=parsed.scheme, netloc=parsed.netloc)

    url = www + "/w/api.php"

    page = (urllib.parse.unquote(parsed.path[6:]),)  # strip /wiki/

    params = {
        # 'action': "render",
        "action": "parse",
        "page": page,
        "format": "json",
        "prop": "wikitext",
    }

    session = requests.session()
    response = session.get(url=url, params=params)
    j = response.json()
    wiki_re = re.compile(r"{{.*}}(?P<desc>.*)", flags=re.DOTALL)
    wiki_match = wiki_re.match(j["parse"]["wikitext"]["*"])
    d = wiki_match.groupdict()
    desc = d["desc"].strip()

    wikicode = mwparserfromhell.parse(desc)
    desc_text = wikicode.strip_code()

    links1 = ""
    for link in wikicode.filter_external_links():
        links1 += "{title} {url}\n".format(title=link.title, url=link.url)

    links2 = ""
    for link in wikicode.filter_wikilinks():
        url="{}/{}".format(www, link.title.strip_code())
        try:
            text = link.text.strip_code()
        except AttributeError:
            text = link.title.strip_code()
        url="{}/{}".format(www, link.title.strip_code())
        links2 += "{text} {url}\n".format(text=text, url=url)


    comment = "{}\n\nTEXT:{}\n\n{}\n{}".format(desc, desc_text, links1, links2)


    print("\ndesc:\n{}".format(desc))
    print("\n\ncomment:\n{}".format(comment))

    return


def main():

    one_page(
        "https://www.mediawiki.org/wiki/EMWCon_Spring_2019/Using_(Semantic)_Mediawiki_on_an_Enterprise_Knowledge_Management_Platform:_From_Banking_IT_Governance_to_Smart_City_Hub_Portals"
    )

    one_page(
        "https://www.mediawiki.org/wiki/EMWCon_Spring_2019/State_of_the_MediaWiki_Ecosystem"
    )


if __name__ == "__main__":
    main()
