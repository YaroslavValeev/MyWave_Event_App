"""Browser smoke of the STATIC Champ App UX prototype. No backend/staging calls."""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright

HTML=Path(__file__).with_name('champ_event_workflow_v3.html').read_text(encoding='utf-8')
checks=[]

def check(ok,name):
    assert ok, name
    checks.append(name)

def nav(page,route):
    page.evaluate('(route) => pageNav(route)',route)

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,executable_path=os.getenv('CHROME_EXECUTABLE') or None,args=['--no-sandbox','--disable-dev-shm-usage'])
    for label,width,height in [('desktop',1366,900),('Xiaomi-like',393,852)]:
        page=browser.new_page(viewport={'width':width,'height':height})
        errors=[]
        page.on('pageerror', lambda err: errors.append(str(err)))
        page.set_content(HTML)
        check(page.get_by_text('Какую задачу вы хотите выполнить?').count()==1,f'{label}: welcome')
        page.locator('[data-role="organizer"]').click()
        nav(page,'prep')
        check('Подготовка мероприятия' in page.locator('#main').inner_text(), f'{label}: preparation view')
        check(page.locator('#main [data-go="docs"]').count()>0, f'{label}: direct document action')
        nav(page,'categories')
        page.locator('#main [data-edit-category="1"]').click()
        page.locator('#catName').fill('Демо категория · корректировка')
        page.locator('#main [data-save-category="1"]').click()
        check('Демо категория · корректировка' in page.locator('#main').inner_text(),f'{label}: edit category')
        nav(page,'judges')
        page.get_by_role('button',name='Предложить распределение').click()
        assigned=page.evaluate("heats.find(h=>h.id==='H2').assigned")
        check('J2' not in assigned,f'{label}: illustrative judge conflict filtered')
        nav(page,'seeding')
        page.locator('#seedCategory').select_option('2')
        page.get_by_role('button',name='Предварительный посев').click()
        check(page.evaluate('state.seedPreview.every(group=>group.length<=6)'),f'{label}: mock wakesurf heats <=6')
        nav(page,'training')
        page.locator('#trainMinutes').fill('16')
        page.get_by_role('button',name='Рассчитать расписание').click()
        check('от 1 до 15' in page.locator('#main').inner_text(),f'{label}: >15min blocked')
        page.locator('#trainMinutes').fill('15')
        page.get_by_role('button',name='Рассчитать расписание').click()
        check('Предварительное расписание' in page.locator('#main').inner_text(),f'{label}: 15min accepted')
        nav(page,'scoring')
        page.get_by_role('button',name='Сохранить судейский лист').click()
        check('Заполните' in page.locator('#main').inner_text(),f'{label}: scoring required fields')
        for key,val in [('execution','7.6'),('intensity','7.3'),('composition','8.4')]:
            page.locator(f'[data-score="{key}"]').fill(val)
        page.locator('#judgeNote').fill('Чистый FS 360, уверенное приземление')
        page.get_by_role('button',name='Выделить элементы из текста').click()
        check('FS 360' in page.locator('#main').inner_text(),f'{label}: voice notes manual parse')
        page.get_by_role('button',name='Сохранить судейский лист').click()
        check('Черновик сохранён только в памяти страницы' in page.locator('#main').inner_text(),f'{label}: local demo save')
        nav(page,'protocol')
        page.locator('#protocolFile').set_input_files({'name':'demo.pdf','mimeType':'application/pdf','buffer':b'%PDF-1.4\n%demo\n'})
        check('demo.pdf' in page.locator('#main').inner_text(),f'{label}: protocol file selected')
        nav(page,'results')
        check(page.get_by_role('button',name='Распечатать демо-грамоту').is_disabled(), f'{label}: certificate print gated')
        page.get_by_role('button',name='Симулировать утверждение').click()
        check(page.get_by_role('button',name='Распечатать демо-грамоту').is_enabled(), f'{label}: certificate print after demo approval')
        check(page.evaluate('document.documentElement.scrollWidth <= window.innerWidth+1'),f'{label}: no root horizontal overflow')
        check(not errors,f'{label}: no uncaught JS errors')
        page.close()
    # Role separation: spectator gets no judge or organizer interfaces.
    page=browser.new_page(viewport={'width':393,'height':852})
    page.set_content(HTML)
    page.locator('[data-role="guest"]').click()
    check(page.locator('#mobileNav [data-go="scoring"]').count()==0,'spectator: judge navigation hidden')
    nav(page,'scoring')
    check('Следите за соревнованием' in page.locator('#main').inner_text(),'spectator: scoring route blocked in prototype')
    browser.close()
print(f'PASS {len(checks)}/{len(checks)} STATIC UX BROWSER CHECKS')
for i,x in enumerate(checks,1):print(f'{i:02d}. {x}')
