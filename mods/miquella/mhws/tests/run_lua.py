import sys
from lupa import lua54
lua = lua54.LuaRuntime(unpack_returned_tuples=True)
lua.execute("arg = {...}", *sys.argv[2:])
lua.execute(open(sys.argv[1], encoding="utf-8").read())
