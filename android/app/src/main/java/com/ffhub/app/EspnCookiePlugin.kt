package com.ffhub.app

import android.annotation.SuppressLint
import android.app.AlertDialog
import android.webkit.JavascriptInterface
import android.webkit.WebView
import android.webkit.WebViewClient
import com.getcapacitor.JSObject
import com.getcapacitor.Plugin
import com.getcapacitor.PluginCall
import com.getcapacitor.PluginMethod
import com.getcapacitor.annotation.CapacitorPlugin

@CapacitorPlugin(name = "EspnCookie")
class EspnCookiePlugin : Plugin() {

    private var activeDialog: AlertDialog? = null

    @SuppressLint("SetJavaScriptEnabled")
    @PluginMethod
    fun extractCookies(call: PluginCall) {
        activity.runOnUiThread {
            val webView = WebView(context).apply {
                settings.javaScriptEnabled = true
                settings.domStorageEnabled = true
                settings.userAgentString =
                    "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36"
            }

            // JS bridge: Android.onCookies(swid, espnS2, leagueId)
            webView.addJavascriptInterface(
                object : Any() {
                    @JavascriptInterface
                    fun onCookies(swid: String, espnS2: String, leagueId: String) {
                        val result = JSObject().apply {
                            put("swid", swid)
                            put("espnS2", espnS2)
                            put("leagueId", leagueId)
                        }
                        call.resolve(result)
                        activity.runOnUiThread { activeDialog?.dismiss() }
                    }
                },
                "Android"
            )

            webView.webViewClient = object : WebViewClient() {
                override fun onPageFinished(view: WebView, url: String) {
                    view.evaluateJavascript(
                        """
                        (function() {
                            var d = document.cookie;
                            var swid = (d.match(/(?:^|;\s*)SWID=([^;]+)/) || [])[1] || '';
                            var s2   = (d.match(/(?:^|;\s*)espn_s2=([^;]+)/) || [])[1] || '';
                            var lid  = (location.search.match(/[?&]leagueId=(\d+)/) || [])[1] || '';
                            if (swid && s2) { Android.onCookies(swid, s2, lid); }
                        })();
                        """.trimIndent(),
                        null
                    )
                }
            }

            val dialog = AlertDialog.Builder(activity)
                .setTitle("Sign in to ESPN")
                .setView(webView)
                .setNegativeButton("Cancel") { _, _ ->
                    call.reject("User cancelled ESPN login.")
                }
                .create()

            activeDialog = dialog
            dialog.show()
            webView.loadUrl("https://www.espn.com/fantasy/football/")
        }
    }
}
