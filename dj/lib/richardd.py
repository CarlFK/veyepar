# richardd.py

def pyvideod(ep):
    # given an episode orm object, return a dict to send to pyvideo

    # make a list of the non empty URLs
    videos = []
    for t,u in (
                ( 'host', ep.host_url ),
                ( 'archive', ep.archive_mp4_url ),
            ):

        if u:

            # PyVideo wants "youtube"
            if "youtu" in u: t="youtube"

            videos.append(
                    {
                      "type": t,
                      "url": u
                    }
                )

    related_urls = []
    for t,u in (
                ( 'public', ep.public_url ),
                ( 'archive', ep.archive_url ),
                ( 'conf', ep.conf_url ),
                ( 'tweet', ep.twitter_url ),
            ):

        if u:
            related_urls.append(
                    {
                      "label": t,
                      "url": u
                    }
                )


    d = {
      "category": ep.show.client.category_key,
      "copyright_text": ep.license,
      "description": ep.description,
      # "duration": ep.cuts_time(),
      "language": ep.language or "eng",
      "quality_notes": ep.video_quality,
      "recorded": ep.start.isoformat(),
      "slug": ep.slug,
      "source_url": ep.host_url,
      "speakers": ep.get_authors(),
      "summary": ep.summary,
      "tags": [] if ( (ep.tags is None) or (not ep.tags)) \
              else ep.tags.split(','),
      "thumbnail_url": ep.thumbnail,
      "title": ep.name,
      "videos": videos,
      "related_urls": related_urls,
      "veyepar_state": ep.state,
    }

    return d
