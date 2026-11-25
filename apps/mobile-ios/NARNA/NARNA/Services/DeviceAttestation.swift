//
//  DeviceAttestation.swift
//  NARNA
//
//  App Attest / DeviceCheck tokens for the free-pool daily cap.
//  No secrets are stored in the app.
//

import Foundation
import DeviceCheck
import CryptoKit

struct DeviceAttestationPayload: Equatable {
    var deviceCheckToken: String?
    var appAttestKeyID: String?
    var appAttestAssertion: String?
    var debugDeviceID: String?

    var asHeaders: [String: String] {
        var h: [String: String] = [:]
        if let deviceCheckToken { h["X-DeviceCheck-Token"] = deviceCheckToken }
        if let appAttestKeyID { h["X-App-Attest-Key-Id"] = appAttestKeyID }
        if let appAttestAssertion { h["X-App-Attest-Assertion"] = appAttestAssertion }
        #if DEBUG
        if let debugDeviceID { h["X-Debug-Device-Id"] = debugDeviceID }
        #endif
        return h
    }
}

enum DeviceAttestation {
    private static let keyIDAccount = "app_attest_key_id"

    static func payload(challenge: Data? = nil) async -> DeviceAttestationPayload {
        var result = DeviceAttestationPayload()
        if DCDevice.current.isSupported {
            if let token = try? await DCDevice.current.generateToken() {
                result.deviceCheckToken = token.base64EncodedString()
            }
        }
        if DCAppAttestService.shared.isSupported {
            if let assertion = await appAttestAssertion(challenge: challenge ?? Data("nana-free-pool".utf8)) {
                result.appAttestKeyID = assertion.keyID
                result.appAttestAssertion = assertion.assertion
            }
        }
        #if DEBUG
        result.debugDeviceID = debugIdentifier()
        #endif
        return result
    }

    #if DEBUG
    private static func debugIdentifier() -> String {
        let stored = UserDefaults.standard.string(forKey: "nana_debug_device_id")
        if let stored, !stored.isEmpty { return stored }
        let fresh = UUID().uuidString
        UserDefaults.standard.set(fresh, forKey: "nana_debug_device_id")
        return fresh
    }
    #endif

    private static func appAttestAssertion(challenge: Data) async -> (keyID: String, assertion: String)? {
        let service = DCAppAttestService.shared
        guard service.isSupported else { return nil }
        var keyID = KeychainService.shared.getAPIKey(account: keyIDAccount)
        if keyID == nil {
            keyID = try? await service.generateKey()
            if let keyID {
                KeychainService.shared.saveAPIKey(keyID, account: keyIDAccount)
            }
        }
        guard let keyID else { return nil }
        let hash = Data(SHA256.hash(data: challenge))
        guard let assertion = try? await service.generateAssertion(keyID, clientDataHash: hash) else {
            return nil
        }
        return (keyID, assertion.base64EncodedString())
    }
}
