import Capacitor
import WebKit

// Registered in AppDelegate.swift via: CAPBridge.registerPlugin("EspnCookie", EspnCookiePlugin.self)
@objc(EspnCookiePlugin)
public class EspnCookiePlugin: CAPPlugin, WKNavigationDelegate, WKScriptMessageHandler {

    private var pendingCall: CAPPluginCall?
    private var containerVC: UIViewController?

    @objc func extractCookies(_ call: CAPPluginCall) {
        call.keepAlive = true
        pendingCall = call

        DispatchQueue.main.async { [weak self] in
            guard let self else { return }

            // Configure a WKWebView with a JS message handler
            let contentController = WKUserContentController()
            contentController.add(self, name: "espnCookies")

            let config = WKWebViewConfiguration()
            config.userContentController = contentController

            let webView = WKWebView(frame: UIScreen.main.bounds, configuration: config)
            webView.navigationDelegate = self
            webView.customUserAgent = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

            // Wrap in a navigation controller so the user can see a title and close button
            let vc = UIViewController()
            vc.view.backgroundColor = .black
            vc.view = webView

            let nav = UINavigationController(rootViewController: vc)
            vc.title = "Sign in to ESPN"
            vc.navigationItem.leftBarButtonItem = UIBarButtonItem(
                barButtonSystemItem: .cancel,
                target: self,
                action: #selector(self.cancelTapped)
            )
            self.containerVC = nav

            self.bridge?.viewController?.present(nav, animated: true)
            webView.load(URLRequest(url: URL(string: "https://www.espn.com/fantasy/football/")!))
        }
    }

    // After each page load, attempt to extract cookies
    public func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        let js = """
        (function() {
            var d = document.cookie;
            var swid = (d.match(/(?:^|;\\s*)SWID=([^;]+)/) || [])[1];
            var s2   = (d.match(/(?:^|;\\s*)espn_s2=([^;]+)/) || [])[1];
            var lid  = (location.search.match(/[?&]leagueId=(\\d+)/) || [])[1] || '';
            if (swid && s2) {
                window.webkit.messageHandlers.espnCookies.postMessage(
                    { swid: swid, espnS2: s2, leagueId: lid }
                );
            }
        })();
        """
        webView.evaluateJavaScript(js, completionHandler: nil)
    }

    // Called by JS when cookies are found
    public func userContentController(
        _ userContentController: WKUserContentController,
        didReceive message: WKScriptMessage
    ) {
        guard
            message.name == "espnCookies",
            let body = message.body as? [String: Any],
            let swid = body["swid"] as? String,
            let espnS2 = body["espnS2"] as? String
        else { return }

        DispatchQueue.main.async { [weak self] in
            self?.containerVC?.dismiss(animated: true)
        }
        pendingCall?.resolve([
            "swid": swid,
            "espnS2": espnS2,
            "leagueId": body["leagueId"] as? String ?? "",
        ])
        pendingCall = nil
    }

    @objc private func cancelTapped() {
        containerVC?.dismiss(animated: true)
        pendingCall?.reject("User cancelled ESPN login.")
        pendingCall = nil
    }
}
