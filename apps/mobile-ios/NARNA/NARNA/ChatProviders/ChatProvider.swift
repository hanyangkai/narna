//
//  ChatProvider.swift
//  NARNA
//

import Foundation

protocol ChatProvider: Sendable {
    var engineDisplayName: String { get }
    func stream(messages: [ChatProviderMessage]) async throws -> AsyncStream<String>
}

protocol AppleAvailabilityChecking: Sendable {
    func availability() -> AppleModelAvailabilityReason
}

enum FreePoolConfig {
    /// Overridable via Info.plist `FREE_POOL_URL` or build setting.
    static var baseURL: URL {
        if let raw = Bundle.main.object(forInfoDictionaryKey: "FREE_POOL_URL") as? String,
           let url = URL(string: raw), !raw.isEmpty {
            return url
        }
        // Placeholder worker host — replace after deploy; no secrets here.
        return URL(string: "https://nana-free-pool.example.workers.dev")!
    }
}

enum ChatRouter {
    /// Nana Auto: Apple on-device when available, else free pool. BYOK only when user picks it.
    static func resolve(
        preference: ChatEngineKind,
        appleChecker: AppleAvailabilityChecking,
        hasBYOKey: Bool
    ) -> (providerKind: ChatEngineKind, availabilityNote: AppleModelAvailabilityReason?) {
        switch preference {
        case .auto:
            let avail = appleChecker.availability()
            if avail == .available {
                return (.onDevice, avail)
            }
            return (.freePool, avail)
        case .onDevice:
            return (.onDevice, appleChecker.availability())
        case .freePool:
            return (.freePool, nil)
        case .byoOpenRouter, .byoOpenAI:
            return (preference, nil)
        }
    }
}
