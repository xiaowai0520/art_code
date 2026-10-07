from playwright.sync_api import sync_playwright
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import threading, shutil
import json
root=Path(__file__).resolve().parents[1]
root.joinpath('checks').mkdir(exist_ok=True)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{server.server_port}/index.html'
with sync_playwright() as p:
 b=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
 mobile=b.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True);errors=[];mobile.on('pageerror',lambda e:errors.append(str(e)));mobile.goto(URL);mobile.locator('#adoptButton').click();mobile.screenshot(path=str(root/'checks/mobile.png'),full_page=True);assert mobile.evaluate('document.documentElement.scrollWidth<=innerWidth')
 mobile.locator('[data-action="feed"]').click();assert mobile.locator('[data-food="carrot"]').is_visible();mobile.locator('#closeModal').click()
 desktop=b.new_page(viewport={'width':1280,'height':1000});desktop.on('pageerror',lambda e:errors.append(str(e)));desktop.goto(URL);desktop.locator('#adoptButton').click()
 desktop.locator('#decorateButton').click();water=desktop.locator('[data-type="water"]');box=water.bounding_box();room=desktop.locator('#room').bounding_box();desktop.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2);desktop.mouse.down();desktop.mouse.move(room['x']+room['width']*.1,room['y']+room['height']*.85,steps=15);desktop.mouse.up();desktop.locator('#finishDecor').click()
 s=desktop.evaluate("JSON.parse(localStorage.getItem('hamster-little-home-v1'))");assert abs(next(d for d in s['decor'] if d['type']=='water')['x']-10)<1
 desktop.locator('#settingsButton').click();desktop.locator('#undoButton').click();s=desktop.evaluate("JSON.parse(localStorage.getItem('hamster-little-home-v1'))");assert next(d for d in s['decor'] if d['type']=='water')['x']==17
 desktop.locator('#closeModal').click();desktop.locator('#settingsButton').click()
 with desktop.expect_file_chooser() as fc:desktop.locator('#importSave').click()
 imported={**s,'name':'恢复小团子','coins':123};fc.value.set_files({'name':'save.json','mimeType':'application/json','buffer':json.dumps(imported).encode()});desktop.locator('#confirmImport').click();assert desktop.locator('#petName').inner_text()=='恢复小团子';assert desktop.locator('#coins').inner_text()=='123'
 desktop.locator('#settingsButton').click()
 with desktop.expect_file_chooser() as fc:desktop.locator('#importSave').click()
 fc.value.set_files({'name':'bad.json','mimeType':'application/json','buffer':b'{broken'});desktop.wait_for_timeout(300);assert desktop.locator('#petName').inner_text()=='恢复小团子';desktop.locator('#closeModal').click()
 offline=b.new_page();offline.add_init_script("let s="+json.dumps(imported)+";s.lastSaved=Date.now()-60*60*1000;s.stats.hunger=80;localStorage.setItem('hamster-little-home-v1',JSON.stringify(s))");offline.goto(URL);s=offline.evaluate("JSON.parse(localStorage.getItem('hamster-little-home-v1'))");assert 49<s['stats']['hunger']<51,s['stats']
 assert not errors,errors
 print(json.dumps({'extra_checks':'passed','flows':['mobile layout','mobile feeding menu','furniture pointer drag','undo decoration','save import','invalid import preservation','offline decay'],'errors':errors},ensure_ascii=False));b.close()
