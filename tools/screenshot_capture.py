from playwright.sync_api import sync_playwright
import time
import os

def capture():
    outdir = os.path.join('docs', 'screenshots')
    os.makedirs(outdir, exist_ok=True)
    base = 'http://127.0.0.1:8000'
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width':1280,'height':800})
        targets = [
            ('/', 'landing.png'),
            ('/about', 'about.png'),
            ('/enhanced-research', 'enhanced_research.png')
        ]
        for path, name in targets:
            url = base + path
            print('Visiting', url)
            page.goto(url, wait_until='networkidle', timeout=60000)
            time.sleep(1.5)
            dest = os.path.join(outdir, name)
            page.screenshot(path=dest, full_page=True)
            print('Saved', dest)

        # Try to fetch PDF report via API endpoint
        try:
            print('Requesting PDF report (may take a while)')
            res = page.request.post(base + '/api/research/enhanced-report-pdf', data=None, json={'symbol':'AAPL', 'period':'1mo'})
            if res.ok:
                pdf_bytes = res.body()
                pdf_path = os.path.join(outdir, 'report.pdf')
                with open(pdf_path, 'wb') as f:
                    f.write(pdf_bytes)
                print('Saved PDF to', pdf_path)
            else:
                print('PDF request returned', res.status)
        except Exception as e:
            print('PDF request failed:', e)

        browser.close()

if __name__ == '__main__':
    capture()
