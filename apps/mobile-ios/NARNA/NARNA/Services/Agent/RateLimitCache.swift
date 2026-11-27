//
//  RateLimitCache.swift
//  NARNA
//
//  In-memory TTL cache + simple token-bucket rate limit for free API skills.
//

import Foundation

actor RateLimitCache {
    static let shared = RateLimitCache()

    private struct Entry {
        let value: String
        let expiresAt: Date
    }

    private var cache: [String: Entry] = [:]
    private var buckets: [String: (tokens: Double, updated: Date)] = [:]

    func get(_ key: String) -> String? {
        guard let e = cache[key] else { return nil }
        if e.expiresAt < Date() {
            cache.removeValue(forKey: key)
            return nil
        }
        return e.value
    }

    func set(_ key: String, value: String, ttl: TimeInterval) {
        cache[key] = Entry(value: value, expiresAt: Date().addingTimeInterval(ttl))
    }

    /// Returns true when the caller may proceed. Capacity refills at `refillPerSecond`.
    func consume(bucket: String, cost: Double = 1, capacity: Double = 10, refillPerSecond: Double = 0.2) -> Bool {
        let now = Date()
        var state = buckets[bucket] ?? (tokens: capacity, updated: now)
        let elapsed = now.timeIntervalSince(state.updated)
        state.tokens = min(capacity, state.tokens + elapsed * refillPerSecond)
        state.updated = now
        guard state.tokens >= cost else {
            buckets[bucket] = state
            return false
        }
        state.tokens -= cost
        buckets[bucket] = state
        return true
    }

    func resetForTests() {
        cache.removeAll()
        buckets.removeAll()
    }
}
