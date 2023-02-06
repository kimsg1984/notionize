from notionizer import Notion


notion = Notion("secret_zt7EQn6Vo5xkFzz5j36AeJSgaYlc3J6kECYXZp7C1mE")
me = notion.get_me()
print(dir(me))
print(me)
print(me.id)
print(me.name)

