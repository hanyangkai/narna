//
//  CalendarReminderSkills.swift
//  NARNA
//
//  EventKit calendar events and reminders. Requires user permission with
//  clear purpose strings in Info.plist. No hidden calendar access.
//

import Foundation
import EventKit

/// Injectable EventKit façade so unit tests can run without a real store.
protocol EventKitGateway: Sendable {
    func requestCalendarAccess() async -> Bool
    func requestRemindersAccess() async -> Bool
    func createEvent(title: String, start: Date, end: Date, notes: String?) throws -> String
    func listEvents(from: Date, to: Date) throws -> [(title: String, start: Date, end: Date)]
    func createReminder(title: String, due: Date?) throws -> String
    func listReminders() async throws -> [(title: String, completed: Bool, due: Date?)]
}

final class SystemEventKitGateway: EventKitGateway, @unchecked Sendable {
    private let store = EKEventStore()

    func requestCalendarAccess() async -> Bool {
        do {
            if #available(iOS 17.0, *) {
                return try await store.requestFullAccessToEvents()
            } else {
                return try await store.requestAccess(to: .event)
            }
        } catch {
            return false
        }
    }

    func requestRemindersAccess() async -> Bool {
        do {
            if #available(iOS 17.0, *) {
                return try await store.requestFullAccessToReminders()
            } else {
                return try await store.requestAccess(to: .reminder)
            }
        } catch {
            return false
        }
    }

    func createEvent(title: String, start: Date, end: Date, notes: String?) throws -> String {
        let event = EKEvent(eventStore: store)
        event.title = title
        event.startDate = start
        event.endDate = end
        event.notes = notes
        event.calendar = store.defaultCalendarForNewEvents
        try store.save(event, span: .thisEvent)
        return event.eventIdentifier ?? title
    }

    func listEvents(from: Date, to: Date) throws -> [(title: String, start: Date, end: Date)] {
        let predicate = store.predicateForEvents(withStart: from, end: to, calendars: nil)
        return store.events(matching: predicate).map { ($0.title ?? "(untitled)", $0.startDate, $0.endDate) }
    }

    func createReminder(title: String, due: Date?) throws -> String {
        let rem = EKReminder(eventStore: store)
        rem.title = title
        rem.calendar = store.defaultCalendarForNewReminders()
        if let due {
            rem.dueDateComponents = Calendar.current.dateComponents([.year, .month, .day, .hour, .minute], from: due)
        }
        try store.save(rem, commit: true)
        return rem.calendarItemIdentifier
    }

    func listReminders() async throws -> [(title: String, completed: Bool, due: Date?)] {
        let calendars = store.calendars(for: .reminder)
        let predicate = store.predicateForReminders(in: calendars)
        return try await withCheckedThrowingContinuation { cont in
            store.fetchReminders(matching: predicate) { reminders in
                let mapped = (reminders ?? []).map { r -> (String, Bool, Date?) in
                    let due = r.dueDateComponents.flatMap { Calendar.current.date(from: $0) }
                    return (r.title ?? "(untitled)", r.isCompleted, due)
                }
                cont.resume(returning: mapped)
            }
        }
    }
}

struct CalendarEventSkill: SkillHandler {
    let gateway: EventKitGateway
    private let iso: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }()
    private let isoBasic: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime]
        return f
    }()

    init(gateway: EventKitGateway = SystemEventKitGateway()) {
        self.gateway = gateway
    }

    var definition: SkillDefinition {
        SkillDefinition(
            name: "calendar_event",
            description: "Create or list calendar events via iOS EventKit after the user grants calendar permission. Actions: create, list.",
            parameters: SkillJSONSchema(
                properties: [
                    "action": SkillJSONProperty(type: "string", description: "create | list", enum: ["create", "list"]),
                    "title": SkillJSONProperty(type: "string", description: "Event title (create)"),
                    "start": SkillJSONProperty(type: "string", description: "ISO-8601 start (create)"),
                    "end": SkillJSONProperty(type: "string", description: "ISO-8601 end (create)"),
                    "notes": SkillJSONProperty(type: "string", description: "Optional notes"),
                    "days_ahead": SkillJSONProperty(type: "number", description: "Days ahead to list (default 7)"),
                ],
                required: ["action"]
            ),
            location: .onDevice,
            permission: .calendars,
            displayName: "Calendar"
        )
    }

    func run(arguments: [String: SkillJSONValue]) async -> SkillResult {
        let allowed = await gateway.requestCalendarAccess()
        guard allowed else {
            return .failure("Calendar access was not granted. Enable it in Settings so Nana can manage events you request.")
        }
        let action = (arguments["action"]?.stringValue ?? "list").lowercased()
        switch action {
        case "create":
            guard let title = arguments["title"]?.stringValue?.trimmingCharacters(in: .whitespacesAndNewlines),
                  !title.isEmpty else { return .failure("Missing title.") }
            guard let start = parseDate(arguments["start"]?.stringValue),
                  let end = parseDate(arguments["end"]?.stringValue) else {
                return .failure("Provide ISO-8601 start and end.")
            }
            do {
                let id = try gateway.createEvent(title: title, start: start, end: end, notes: arguments["notes"]?.stringValue)
                return .success("Created event “\(title)”.", data: ["id": .string(id)])
            } catch {
                return .failure("Could not create event: \(error.localizedDescription)")
            }
        case "list":
            let days = Int(arguments["days_ahead"]?.doubleValue ?? 7)
            let from = Date()
            let to = Calendar.current.date(byAdding: .day, value: max(1, days), to: from) ?? from.addingTimeInterval(86400)
            do {
                let events = try gateway.listEvents(from: from, to: to)
                if events.isEmpty { return .success("No events in the next \(days) day(s).") }
                let df = DateFormatter()
                df.dateStyle = .medium
                df.timeStyle = .short
                let lines = events.prefix(20).map { "• \($0.title) — \(df.string(from: $0.start))" }
                return .success(lines.joined(separator: "\n"))
            } catch {
                return .failure("Could not list events: \(error.localizedDescription)")
            }
        default:
            return .failure("Unknown action.")
        }
    }

    private func parseDate(_ s: String?) -> Date? {
        guard let s, !s.isEmpty else { return nil }
        return iso.date(from: s) ?? isoBasic.date(from: s)
    }
}

struct ReminderSkill: SkillHandler {
    let gateway: EventKitGateway
    private let iso = ISO8601DateFormatter()

    init(gateway: EventKitGateway = SystemEventKitGateway()) {
        self.gateway = gateway
        iso.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
    }

    var definition: SkillDefinition {
        SkillDefinition(
            name: "reminder",
            description: "Create or list Reminders via iOS EventKit after the user grants reminders permission. Actions: create, list.",
            parameters: SkillJSONSchema(
                properties: [
                    "action": SkillJSONProperty(type: "string", description: "create | list", enum: ["create", "list"]),
                    "title": SkillJSONProperty(type: "string", description: "Reminder title (create)"),
                    "due": SkillJSONProperty(type: "string", description: "Optional ISO-8601 due date"),
                ],
                required: ["action"]
            ),
            location: .onDevice,
            permission: .reminders,
            displayName: "Reminder"
        )
    }

    func run(arguments: [String: SkillJSONValue]) async -> SkillResult {
        let allowed = await gateway.requestRemindersAccess()
        guard allowed else {
            return .failure("Reminders access was not granted. Enable it in Settings so Nana can create reminders you request.")
        }
        let action = (arguments["action"]?.stringValue ?? "list").lowercased()
        switch action {
        case "create":
            guard let title = arguments["title"]?.stringValue?.trimmingCharacters(in: .whitespacesAndNewlines),
                  !title.isEmpty else { return .failure("Missing title.") }
            let due = arguments["due"]?.stringValue.flatMap { iso.date(from: $0) ?? ISO8601DateFormatter().date(from: $0) }
            do {
                let id = try gateway.createReminder(title: title, due: due)
                return .success("Reminder set: \(title)", data: ["id": .string(id)])
            } catch {
                return .failure("Could not create reminder: \(error.localizedDescription)")
            }
        case "list":
            do {
                let items = try await gateway.listReminders()
                let open = items.filter { !$0.completed }
                if open.isEmpty { return .success("No open reminders.") }
                let lines = open.prefix(20).map { "○ \($0.title)" }
                return .success(lines.joined(separator: "\n"))
            } catch {
                return .failure("Could not list reminders: \(error.localizedDescription)")
            }
        default:
            return .failure("Unknown action.")
        }
    }
}
