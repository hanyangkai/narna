//
//  AppConfig.swift
//  NARNA
//
//  Non-secret endpoints and legal URLs. Provider API keys must never be
//  placed in the app bundle; they live only on the Worker / agent proxy.
//

import Foundation

enum AppConfig {
    static var freePoolURL: URL? {
        url(named: "FREE_POOL_URL", environment: "FREE_POOL_URL")
    }

    static var agentProxyURL: URL? {
        url(named: "AGENT_PROXY_URL", environment: "AGENT_PROXY_URL")
    }

    static var privacyURL: URL {
        url(named: "NANA_PRIVACY_URL", environment: "NANA_PRIVACY_URL")
            ?? URL(string: "https://narna.org/privacy")!
    }

    static var termsURL: URL {
        url(named: "NANA_TERMS_URL", environment: "NANA_TERMS_URL")
            ?? URL(string: "https://www.apple.com/legal/internet-services/itunes/dev/stdeula/")!
    }

    static var isFreePoolConfigured: Bool { freePoolURL != nil }
    static var isAgentProxyConfigured: Bool { agentProxyURL != nil }

    private static func url(named infoKey: String, environment: String) -> URL? {
        if let env = ProcessInfo.processInfo.environment[environment]?.trimmingCharacters(in: .whitespacesAndNewlines),
           let url = URL(string: env), url.scheme?.hasPrefix("http") == true {
            return url
        }
        if let raw = Bundle.main.object(forInfoDictionaryKey: infoKey) as? String {
            let trimmed = raw.trimmingCharacters(in: .whitespacesAndNewlines)
            if let url = URL(string: trimmed), url.scheme?.hasPrefix("http") == true {
                return url
            }
        }
        return nil
    }
}
