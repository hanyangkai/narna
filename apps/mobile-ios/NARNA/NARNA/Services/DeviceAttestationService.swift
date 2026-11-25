//
//  DeviceAttestationService.swift
//  NARNA
//
//  DeviceCheck token for free-pool daily limits. Falls back to Keychain device UUID.
//

import Foundation
import DeviceCheck

enum DeviceAttestationService {
    /// Returns a DeviceCheck token when available; otherwise nil (Worker still accepts X-Device-Id).
    static func deviceCheckToken() async -> String? {
        guard DCDevice.current.isSupported else { return nil }
        return await withCheckedContinuation { continuation in
            DCDevice.current.generateToken { data, _ in
                guard let data else {
                    continuation.resume(returning: nil)
                    return
                }
                continuation.resume(returning: data.base64EncodedString())
            }
        }
    }
}
