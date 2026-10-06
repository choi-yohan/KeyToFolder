import Cocoa
import WebKit

final class AppDelegate: NSObject, NSApplicationDelegate, NSWindowDelegate, WKUIDelegate {
    private var server: Process?
    private var window: NSWindow?
    private var webView: WKWebView?
    private var started = false
    private var stopping = false
    private var output = ""
    private var pipe: Pipe?

    func applicationDidFinishLaunching(_ notification: Notification) {
        setupMenu()
        let folder = Bundle.main.resourceURL!.appendingPathComponent("Project")
        let script = folder.appendingPathComponent("app.py")
        guard FileManager.default.fileExists(atPath: script.path),
              FileManager.default.fileExists(atPath: folder.appendingPathComponent("ui.html").path) else {
            fail("Application files are missing. Extract a fresh copy of KeyToFolder.app.\n\n앱의 구성 파일이 없습니다. KeyToFolder.app을 다시 압축 해제해 주세요.")
            return
        }
        guard let python = findPython(in: folder) else {
            fail("Python 3.10 or newer is required. Install Python from python.org, then reopen KeyToFolder.\n\nPython 3.10 이상을 설치한 뒤 다시 실행해 주세요.")
            return
        }
        let process = Process()
        process.executableURL = URL(fileURLWithPath: python)
        process.arguments = ["-u", script.path, "--no-open"]
        process.currentDirectoryURL = folder
        var environment = ProcessInfo.processInfo.environment
        environment["PYTHONUNBUFFERED"] = "1"
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        process.environment = environment
        let stream = Pipe()
        process.standardOutput = stream
        process.standardError = stream
        pipe = stream
        stream.fileHandleForReading.readabilityHandler = { [weak self] handle in
            let data = handle.availableData
            guard !data.isEmpty else { return }
            let message = String(decoding: data, as: UTF8.self)
            DispatchQueue.main.async { self?.receive(message) }
        }
        process.terminationHandler = { [weak self] _ in
            DispatchQueue.main.async {
                guard let self = self, !self.stopping else { return }
                self.fail("KeyToFolder stopped unexpectedly.\n프로그램 실행이 중단되었습니다.\n\n" + String(self.output.suffix(2000)))
            }
        }
        server = process
        do {
            try process.run()
        } catch {
            fail("Unable to start KeyToFolder.\n프로그램을 시작하지 못했습니다.\n\n" + error.localizedDescription)
            return
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 20) { [weak self] in
            guard let self = self, !self.started, !self.stopping else { return }
            self.fail("KeyToFolder did not finish starting.\n프로그램이 시작되지 않았습니다.\n\n" + String(self.output.suffix(2000)))
        }
    }

    private func findPython(in folder: URL) -> String? {
        var paths = [folder.appendingPathComponent(".venv/bin/python3").path,
                     "/opt/homebrew/bin/python3", "/usr/local/bin/python3",
                     "/Library/Frameworks/Python.framework/Versions/Current/bin/python3"]
        paths += (ProcessInfo.processInfo.environment["PATH"] ?? "").split(separator: ":").map { String($0) + "/python3" }
        paths.append("/usr/bin/python3")
        var seen = Set<String>()
        for path in paths where seen.insert(path).inserted && FileManager.default.isExecutableFile(atPath: path) {
            let probe = Process()
            probe.executableURL = URL(fileURLWithPath: path)
            probe.arguments = ["-c", "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)"]
            probe.standardOutput = FileHandle.nullDevice
            probe.standardError = FileHandle.nullDevice
            do { try probe.run(); probe.waitUntilExit(); if probe.terminationStatus == 0 { return path } } catch { continue }
        }
        return nil
    }

    private func receive(_ message: String) {
        output = String((output + message).suffix(8000))
        guard !started, let range = output.range(of: "http://127.0.0.1:"),
              let end = output[range.lowerBound...].firstIndex(of: "/", offsetBy: 7) else { return }
        let address = String(output[range.lowerBound...end])
        guard let url = URL(string: address), url.host == "127.0.0.1" else { return }
        started = true
        showWindow(url)
    }

    private func showWindow(_ url: URL) {
        let config = WKWebViewConfiguration()
        // App preferences persist in .settings.json; web storage need not persist.
        config.websiteDataStore = .nonPersistent()
        let view = WKWebView(frame: .zero, configuration: config)
        view.uiDelegate = self
        let win = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 1280, height: 820),
                           styleMask: [.titled, .closable, .miniaturizable, .resizable], backing: .buffered, defer: false)
        win.title = "KeyToFolder"
        win.minSize = NSSize(width: 720, height: 500)
        win.contentView = view
        win.delegate = self
        win.isReleasedWhenClosed = false
        win.center()
        window = win
        webView = view
        view.load(URLRequest(url: url))
        win.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { true }
    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        window?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
        return true
    }
    func applicationWillTerminate(_ notification: Notification) {
        stopping = true
        pipe?.fileHandleForReading.readabilityHandler = nil
        if let server = server, server.isRunning { server.terminate(); server.waitUntilExit() }
    }

    private func fail(_ message: String) {
        guard !stopping else { return }
        stopping = true
        let alert = NSAlert()
        alert.messageText = "KeyToFolder"
        alert.informativeText = message
        alert.alertStyle = .warning
        alert.addButton(withTitle: "OK")
        NSApp.activate(ignoringOtherApps: true)
        alert.runModal()
        NSApp.terminate(nil)
    }

    private func setupMenu() {
        let menu = NSMenu()
        let appItem = NSMenuItem()
        let appMenu = NSMenu()
        appMenu.addItem(withTitle: "Quit KeyToFolder", action: #selector(NSApplication.terminate(_:)), keyEquivalent: "q")
        appItem.submenu = appMenu
        menu.addItem(appItem)
        let editItem = NSMenuItem()
        editItem.title = "Edit"
        let edit = NSMenu(title: "Edit")
        for (name, action, key) in [("Cut", "cut:", "x"), ("Copy", "copy:", "c"), ("Paste", "paste:", "v"), ("Select All", "selectAll:", "a")] {
            edit.addItem(withTitle: name, action: Selector(action), keyEquivalent: key)
        }
        editItem.submenu = edit
        menu.addItem(editItem)
        NSApp.mainMenu = menu
    }

    func webView(_ webView: WKWebView, runJavaScriptAlertPanelWithMessage message: String, initiatedByFrame frame: WKFrameInfo, completionHandler: @escaping () -> Void) {
        let alert = NSAlert(); alert.messageText = message; alert.runModal(); completionHandler()
    }
}

// Find the path delimiter after the scheme without matching either scheme slash.
private extension Substring {
    func firstIndex(of character: Character, offsetBy offset: Int) -> String.Index? {
        let start = index(startIndex, offsetBy: offset, limitedBy: endIndex) ?? endIndex
        return self[start...].firstIndex(of: character)
    }
}
let app = NSApplication.shared
let delegate = AppDelegate()
app.delegate = delegate
app.setActivationPolicy(.regular)
app.run()
