import pw

import slumber

host = pw.richard['test']

api = slumber.API(host['url'])

# hunt down any previous data that looks like the data we are working with
# and kill it.
cats = api.category.get()
for cat in cats['objects']:
    if cat['slug']  in [ 
            'test_show', 'carlcon-2012', 'chipy_aug_2012' 
            'scipy_2012']:
        cat_id = cat['id']
        print cat_id, cat['slug'],
        print api.category(cat_id).delete(
                username=host['user'], 
                api_key=host['api_key'])

