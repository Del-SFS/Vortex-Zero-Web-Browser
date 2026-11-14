import sys
from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QToolBar, QLineEdit, 
    QPushButton, QTabWidget, QMenu
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

class VortexBrowserWindow(QMainWindow):
    def __init__(self, profile=None, is_incognito=False):
        super().__init__()
        
        if profile is None:
            self.profile = QWebEngineProfile.defaultProfile()
        else:
            self.profile = profile

        self.is_muted = False
        self.bookmarks = {}  # Dicionário para guardar { "Nome do Site": "URL" }

        title = "Vortex-Zero (Modo Anônimo)" if is_incognito else "Vortex-Zero Browser"
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 1280, 720)

        # Abas
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.update_url_bar_from_tab)
        self.setCentralWidget(self.tabs)

        # --- BARRA DE NAVEGAÇÃO PRINCIPAL ---
        navbar = QToolBar("Navegação")
        self.addToolBar(navbar)

        back_btn = QPushButton("◀")
        back_btn.clicked.connect(self.current_browser_back)
        navbar.addWidget(back_btn)

        forward_btn = QPushButton("▶")
        forward_btn.clicked.connect(self.current_browser_forward)
        navbar.addWidget(forward_btn)

        reload_btn = QPushButton("↻")
        reload_btn.clicked.connect(self.current_browser_reload)
        navbar.addWidget(reload_btn)

        home_btn = QPushButton("🏠")
        home_btn.clicked.connect(self.go_home)
        navbar.addWidget(home_btn)

        navbar.addSeparator()

        self.url_bar = QLineEdit()
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        navbar.addWidget(self.url_bar)

        # Botão para adicionar a página atual aos favoritos
        star_btn = QPushButton("⭐")
        star_btn.setToolTip("Adicionar aos Favoritos")
        star_btn.clicked.connect(self.add_bookmark)
        navbar.addWidget(star_btn)

        navbar.addSeparator()

        self.mute_btn = QPushButton("🔊 Som Ligado")
        self.mute_btn.setToolTip("Mutar ou Ativar o som globalmente")
        self.mute_btn.clicked.connect(self.toggle_mute)
        navbar.addWidget(self.mute_btn)

        navbar.addSeparator()

        new_tab_btn = QPushButton("＋")
        new_tab_btn.clicked.connect(lambda: self.add_new_tab("https://www.google.com", "Nova Aba"))
        navbar.addWidget(new_tab_btn)

        menu_btn = QPushButton("☰ Opções")
        menu_menu = QMenu(self)
        
        if not is_incognito:
            menu_menu.addAction("Abrir Janela Anônima", self.open_incognito_window)

        menu_btn.setMenu(menu_menu)
        navbar.addWidget(menu_btn)

        # --- BARRA DE FAVORITOS (SEGUNDA BARRA) ---
        self.bookmark_bar = QToolBar("Favoritos")
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.bookmark_bar)
        
        # Adiciona alguns favoritos padrão para exemplo
        self.add_default_bookmark("Google", "https://www.google.com")
        self.add_default_bookmark("YouTube", "https://www.youtube.com")
        self.add_default_bookmark("GitHub", "https://github.com")

        self.add_new_tab("https://www.google.com", "Página Inicial")

    def create_browser(self):
        page = QWebEnginePage(self.profile, self)
        browser = QWebEngineView()
        browser.setPage(page)
        browser.urlChanged.connect(lambda q, b=browser: self.update_url_if_current(q, b))
        page.setAudioMuted(self.is_muted)
        return browser

    def add_new_tab(self, url_str, label):
        browser = self.create_browser()
        browser.setUrl(QUrl(url_str))
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            self.close()

    def current_browser(self):
        return self.tabs.currentWidget()

    def current_browser_back(self):
        b = self.current_browser()
        if b: b.back()

    def current_browser_forward(self):
        b = self.current_browser()
        if b: b.forward()

    def current_browser_reload(self):
        b = self.current_browser()
        if b: b.reload()

    def go_home(self):
        b = self.current_browser()
        if b: b.setUrl(QUrl("https://www.google.com"))

    def navigate_to_url(self):
        text = self.url_bar.text().strip()
        browser = self.current_browser()
        if not browser:
            return

        if "." not in text or " " in text:
            url = f"https://www.google.com/search?q={text.replace(' ', '+')}"
        elif not text.startswith("http://") and not text.startswith("https://"):
            url = "https://" + text
        else:
            url = text

        browser.setUrl(QUrl(url))

    def update_url_if_current(self, q, browser):
        if self.current_browser() == browser:
            self.url_bar.setText(q.toString())
            index = self.tabs.indexOf(browser)
            if index != -1:
                self.tabs.setTabText(index, q.host() if q.host() else "Página")

    def update_url_bar_from_tab(self, index):
        browser = self.tabs.widget(index)
        if browser:
            self.url_bar.setText(browser.url().toString())

    def add_default_bookmark(self, title, url):
        btn = QPushButton(f"📌 {title}")
        btn.clicked.connect(lambda: self.open_bookmark(url))
        self.bookmark_bar.addWidget(btn)

    def add_bookmark(self):
        browser = self.current_browser()
        if not browser:
            return
        url = browser.url().toString()
        title = browser.page().title() or url
        
        # Cria um botão de favorito dinâmico na barra
        btn = QPushButton(f"📌 {title[:15]}...")
        btn.setToolTip(url)
        btn.clicked.connect(lambda checked, u=url: self.open_bookmark(u))
        self.bookmark_bar.addWidget(btn)

    def open_bookmark(self, url):
        browser = self.current_browser()
        if browser:
            browser.setUrl(QUrl(url))

    def toggle_mute(self):
        self.is_muted = not self.is_muted
        for i in range(self.tabs.count()):
            browser = self.tabs.widget(i)
            if browser and browser.page():
                browser.page().setAudioMuted(self.is_muted)

        if self.is_muted:
            self.mute_btn.setText("🔇 Silenciado")
        else:
            self.mute_btn.setText("🔊 Som Ligado")

    def open_incognito_window(self):
        self.incognito_profile = QWebEngineProfile()
        self.incognito_window = VortexBrowserWindow(profile=self.incognito_profile, is_incognito=True)
        self.incognito_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VortexBrowserWindow()
    window.show()
    sys.exit(app.exec())