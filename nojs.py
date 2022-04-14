# Get NoJS files
import nojsbuild as build
import nopm

# Get required assets
from flask import Flask, Response
from waitress import serve as WSGI_SERVER
import click, random, os, json, gzip

# Initate run function
class NoJSServer(Flask):
  def run(self, host=False, port=8080):
    return WSGI_SERVER(self, host=['localhost', '0.0.0.0'][host], port=port)


# Configuration
config = { # Set default config settings
  "proxy": [],
  "port": 8080,
  "host": False,
  "canrebuild": False,
  "indexDirectories": False,
  "verbose": False,
  "gzip": True
}

if os.path.exists("nojs.config.json") and os.path.isfile("nojs.config.json"):
  configfile = open("nojs.config.json")
  configcont = json.loads(configfile.read())
  configfile.close()
  for i in configcont.keys():
    config[i] = configcont[i]


# Extensions
extensions = {}

def loadextensions():
  nopm.init()
  ext_list = os.listdir("nojs_files/extensions")
  for ext in ext_list:
    exec(f"import nojs_files.extensions.{ext} as func_ext_{ext}")
    exec(f"extensions['{ext}'] = func_ext_{ext}")


# Dynamic route
server_route_functions = {}

def assign(app, url="/", cache={}, view_funcs=[]):
  # Get content
  cont = cache[url]["cont"]

  # Gzip Compress
  if config["gzip"]:
    if config["verbose"]:
      print(f"Compressing {url}...")
    if type(cont) == str:
      cont = cont.encode("utf-8")
    cont = gzip.compress(cont)


  ret = Response(cont, status=200, mimetype=cache[url]["mime"])


  if config["gzip"]:
    ret.headers["Content-Encoding"] = 'gzip'
    ret.headers["Content-length"] = len(cont)
    if config["verbose"]:
      print(f"Done comrpessing {url}")

  
  server_route_functions[url] = lambda : ret
  name = f"server_route_func_{url.replace('/', '_').replace('.', '_')}_{random.randint(0, 10000000)}"
  server_route_functions[url].__name__ = name
  server_route_functions[url].__qualname__ = name
  view_funcs.append(app.route(url)(server_route_functions[url]))

  
def run(host=config["host"], port=config["port"], indexDirectories=config["indexDirectories"], rebuild=config["canrebuild"]):
  print("Building server...")
  loadextensions()
  cache = build.build(indexDirectories, config, extensions=extensions)
  
  print("Done. Initializing server...")
  app = NoJSServer(__name__)
  if rebuild:
    @app.route("/nojs/rebuild")
    def nojs_rebuild(): # to be fixed
      cache = build.build(indexDirectories)
      view_funcs = []
      for f in cache.keys():
        assign(app, f, cache, view_funcs)
      return "Rebuild completed."
  view_funcs = []
  for f in cache.keys():
    assign(app, f, cache, view_funcs)

  print(f"Done. Starting server on port {port}...")
  app.run(host, port)

@click.command()
@click.option("-h", "--host", "run_host", help="Host the server on a public port", default=config["host"], type=bool)
@click.option("-p", "--port", "run_port", help="Set the port of the server", default=config["port"], is_flag=True)
def CLICK_host(run_host, run_port):
  print("heehoo")
  run(run_host, run_port)

if __name__ == "__main__":
  run()