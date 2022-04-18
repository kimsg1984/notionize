# database = ['object', 'id', 'cover', 'icon', 'created_time', 'last_edited_time', 'title', 'properties', 'parent', 'url']
# page = ['archived', 'cover', 'created_time', 'icon', 'id', 'last_edited_time', 'object', 'parent', 'properties', 'url']

database = ['object', 'id', 'cover', 'icon', 'created_time', 'last_edited_time', 'title', 'properties', 'parent', 'url']
page = ['archived', 'cover', 'created_time', 'icon', 'id', 'last_edited_time', 'object', 'parent', 'properties', 'url']
block = ['object','id','type','created_time','created_by','last_edited_time','last_edited_by','archived','has_children']


print(set(database).intersection(set(page)).intersection(set(block)))