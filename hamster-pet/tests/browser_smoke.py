from playwright.sync_api import sync_playwright
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import threading, shutil
import json
ROOT=Path(__file__).resolve().parents[1]
ROOT.joinpath('checks').mkdir(exist_ok=True)
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
URL=f'http://127.0.0.1:{server.server_port}/index.html'
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=shutil.which('chromium'),headless=True,args=['--no-sandbox'])
 page=browser.new_page(viewport={'width':1440,'height':1100})
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(URL);page.locator('[data-type="pudding"]').click();page.locator('#nameInput').fill('小杏仁');page.locator('#adoptButton').click()
 page.screenshot(path=str(ROOT/'checks/desktop.png'),full_page=True)
 assert page.locator('#petName').inner_text()=='小杏仁'
 def s():return page.evaluate("JSON.parse(localStorage.getItem('hamster-little-home-v1'))")
 before=s();page.locator('[data-action="feed"]').click();page.locator('[data-food="carrot"]').click();page.wait_for_timeout(14000)
 after=s();assert after['inventory']['carrot']==before['inventory']['carrot']-1,(before,after)
 assert after['stats']['hunger']>before['stats']['hunger'];assert 'feed' in after['daily']['tasks']
 page.locator('[data-action="water"]').click();page.wait_for_timeout(14000);assert s()['stats']['bond']>after['stats']['bond']
 page.locator('#hamster').click();page.wait_for_timeout(2200)
 page.locator('#shopButton').click();page.locator('[data-cat="toy"]').click();page.locator('[data-buy="ball"]').click();assert 'ball' in s()['owned']
 page.locator('[data-cat="storage"]').click();page.locator('[data-buy="ball"]').click();assert any(x['type']=='ball' for x in s()['decor'])
 page.locator('#finishDecor').click()
 page.locator('[data-action="play"]').click();page.locator('[data-play="ball"]').click();page.wait_for_timeout(14000)
 assert 'play' in s()['daily']['tasks']
 page.locator('[data-action="clean"]').click();page.wait_for_timeout(2500);assert s()['stats']['clean']>=99
 page.locator('[data-action="sleep"]').click();page.wait_for_timeout(14000);assert s()['sleeping'];page.locator('#hamster').click();page.locator('#wakeButton').click();assert not s()['sleeping']
 page.reload();assert page.locator('#petName').inner_text()=='小杏仁';assert 'ball' in s()['owned']
 page.locator('#settingsButton').click();page.locator('#renameButton').click();page.locator('#renameInput').fill('<杏仁>');page.locator('#saveName').click();assert page.locator('#petName').inner_text()=='<杏仁>'
 page.locator('#settingsButton').click()
 with page.expect_download() as d:page.locator('#exportSave').click()
 file=ROOT/'checks/test-save.json';d.value.save_as(str(file));assert json.loads(file.read_text())['name']=='<杏仁>'
 page.locator('#closeModal').click();page.screenshot(path=str(ROOT/'checks/desktop-game.png'),full_page=True)
 phone=browser.new_page(viewport={'width':390,'height':844},is_mobile=True,has_touch=True);phone.on('pageerror',lambda e:errors.append(str(e)));phone.goto(URL);phone.locator('#adoptButton').click();phone.screenshot(path=str(ROOT/'checks/mobile.png'),full_page=True)
 assert phone.evaluate('document.documentElement.scrollWidth<=window.innerWidth'),'mobile horizontal overflow'
 assert not errors,errors
 print(json.dumps({'result':'passed','flows':['adoption','feeding','water','petting','purchase','placement','play','clean','sleep/wake','reload/save','safe rename','save export','mobile layout'],'page_errors':errors},ensure_ascii=False),flush=True)
 browser.close()
