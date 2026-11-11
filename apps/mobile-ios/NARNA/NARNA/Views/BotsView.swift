//
//  BotsView.swift
//  NARNA
//
//  Home screen: bot list in the style of the Grok Bot app. NaNa Bot (Chief of Staff)
//  is the large avatar on top and cannot be deleted. User bots are stored only on this iPhone.
//

import SwiftUI

struct BotsHomeView: View {
    @EnvironmentObject var app: AppState
    @EnvironmentObject var bots: ChatBotStore
    @EnvironmentObject var store: ConversationStore
    @EnvironmentObject var settings: LLMSettings
    @State private var query = ""
    @State private var showCreate = false
    @State private var editing: ChatBot?
    @State private var confirmDelete: ChatBot?
    @FocusState private var searchFocused: Bool

    private var searching: Bool { !query.trimmingCharacters(in: .whitespaces).isEmpty }
    private var userBots: [ChatBot] { bots.listed.filter { !$0.isChiefOfStaff } }

    var body: some View {
        List {
            if searching {
                let results = bots.filtered(query: query)
                if results.isEmpty {
                    Text("No bots match “\(query)”")
                        .foregroundStyle(.secondary)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 40)
                        .listRowBackground(Color.clear)
                        .listRowSeparator(.hidden)
                }
                ForEach(results) { bot in row(bot) }
            } else {
                hero
                    .listRowBackground(Color.clear)
                    .listRowSeparator(.hidden)
                    .listRowInsets(EdgeInsets(top: 4, leading: 16, bottom: 20, trailing: 16))
                if userBots.isEmpty {
                    Button { showCreate = true } label: {
                        HStack(spacing: 14) {
                            ZStack {
                                Circle().strokeBorder(Color.secondary.opacity(0.4), style: StrokeStyle(lineWidth: 1.5, dash: [4]))
                                Image(systemName: "plus").foregroundStyle(.secondary)
                            }
                            .frame(width: 52, height: 52)
                            VStack(alignment: .leading, spacing: 3) {
                                Text("Create your first bot").font(.headline)
                                Text("Give it a name, a persona and its own model").font(.subheadline).foregroundStyle(.secondary)
                            }
                        }
                    }
                    .buttonStyle(.plain)
                    .listRowBackground(Color.clear)
                    .listRowSeparator(.hidden)
                } else {
                    ForEach(userBots) { bot in row(bot) }
                }
            }
        }
        .listStyle(.plain)
        .scrollContentBackground(.hidden)
        .scrollDismissesKeyboard(.interactively)
        .background(Color(.systemBackground))
        .toolbar(.hidden, for: .navigationBar)
        .safeAreaInset(edge: .top, spacing: 0) { header }
        .safeAreaInset(edge: .bottom, spacing: 0) { searchBar }
        .sheet(isPresented: $showCreate) {
            EditBotSheet(existing: nil)
                .environmentObject(bots)
                .environmentObject(settings)
        }
        .sheet(item: $editing) { bot in
            EditBotSheet(existing: bot)
                .environmentObject(bots)
                .environmentObject(settings)
        }
        .confirmationDialog("Delete \(confirmDelete?.name ?? "this bot")? Its chats on this iPhone will be removed.",
                            isPresented: Binding(get: { confirmDelete != nil },
                                                 set: { if !$0 { confirmDelete = nil } }),
                            titleVisibility: .visible) {
            Button("Delete", role: .destructive) {
                if let b = confirmDelete { bots.delete(b.id) }
                confirmDelete = nil
            }
        }
        .onAppear {
            #if DEBUG
            if ProcessInfo.processInfo.arguments.contains("-NARNA_OPEN_CREATE") {
                showCreate = true
            }
            #endif
        }
    }

    // MARK: Pieces

    private var header: some View {
        HStack {
            Button { app.showSettings = true } label: {
                ZStack {
                    Circle().fill(Color(.secondarySystemBackground))
                    Image(systemName: "person.fill")
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundStyle(.secondary)
                }
                .frame(width: 40, height: 40)
                .overlay(Circle().strokeBorder(Color.primary.opacity(0.1)))
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Profile and Settings")
            Spacer()
            Button { showCreate = true } label: {
                ZStack {
                    Circle().fill(Color(.secondarySystemBackground))
                    Image(systemName: "plus")
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundStyle(.primary)
                }
                .frame(width: 40, height: 40)
                .overlay(Circle().strokeBorder(Color.primary.opacity(0.1)))
            }
            .buttonStyle(.plain)
            .accessibilityLabel("Create bot")
        }
        .padding(.horizontal, 16)
        .padding(.top, 4)
        .padding(.bottom, 6)
        .background(Color(.systemBackground))
    }

    private var hero: some View {
        let chief = bots.chief
        let p = preview(for: chief)
        return Button { open(chief) } label: {
            VStack(spacing: 10) {
                ZStack(alignment: .topTrailing) {
                    BotAvatar(bot: chief, size: 112)
                        .shadow(color: chief.avatarColor.opacity(0.45), radius: 24, y: 6)
                    if unread(for: chief) {
                        Circle().fill(Color.accentColor).frame(width: 16, height: 16)
                            .overlay(Circle().strokeBorder(Color(.systemBackground), lineWidth: 3))
                            .accessibilityLabel("Unread")
                    }
                }
                Text(chief.name).font(.title2.bold())
                Text("Chief of Staff")
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(Color.accentColor)
                    .padding(.horizontal, 10).padding(.vertical, 3)
                    .background(Color.accentColor.opacity(0.16), in: Capsule())
                if p.date != nil {
                    Text(p.text)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                        .padding(.horizontal, 30)
                }
            }
            .frame(maxWidth: .infinity)
            .padding(.top, 18)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel("\(chief.name), Chief of Staff")
    }

    private func row(_ bot: ChatBot) -> some View {
        Button { open(bot) } label: {
            BotRow(bot: bot, preview: preview(for: bot), unread: unread(for: bot))
        }
        .buttonStyle(.plain)
        .listRowBackground(Color.clear)
        .listRowInsets(EdgeInsets(top: 8, leading: 16, bottom: 8, trailing: 16))
        .alignmentGuide(.listRowSeparatorLeading) { _ in 66 }
        .contextMenu { contextMenu(for: bot) }
        .swipeActions(edge: .trailing, allowsFullSwipe: false) {
            if !bot.isChiefOfStaff {
                Button(role: .destructive) { confirmDelete = bot } label: { Label("Delete", systemImage: "trash") }
                Button { editing = bot } label: { Label("Edit", systemImage: "pencil") }
                    .tint(.blue)
            }
        }
    }

    private var searchBar: some View {
        HStack(spacing: 8) {
            Image(systemName: "magnifyingglass").foregroundStyle(.secondary)
            TextField("Search", text: $query)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
                .focused($searchFocused)
                .submitLabel(.search)
            if !query.isEmpty {
                Button { query = "" } label: {
                    Image(systemName: "xmark.circle.fill").foregroundStyle(.secondary)
                }
                .accessibilityLabel("Clear search")
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 13)
        .background(.ultraThinMaterial, in: Capsule())
        .overlay(Capsule().strokeBorder(Color.primary.opacity(0.12)))
        .shadow(color: .black.opacity(0.35), radius: 16, y: 6)
        .padding(.horizontal, 20)
        .padding(.top, 6)
        .padding(.bottom, 8)
    }

    // MARK: Data

    private func preview(for bot: ChatBot) -> (text: String, date: Date?) {
        if let c = store.sorted(for: bot.id).first {
            return (c.preview.replacingOccurrences(of: "**", with: "").replacingOccurrences(of: "\n", with: " "), c.updatedAt)
        }
        return (bot.isChiefOfStaff ? "Chief of Staff" : (bot.role.isEmpty ? "No messages yet" : bot.role), nil)
    }

    private func unread(for bot: ChatBot) -> Bool {
        guard let c = store.sorted(for: bot.id).first,
              let last = c.messages.last, last.role == .assistant, !last.isError else { return false }
        if let seen = bot.lastViewedAt { return last.createdAt > seen }
        return false
    }

    private func open(_ bot: ChatBot) {
        searchFocused = false
        bots.markViewed(bot.id)
        app.openBot(bot.id, conversation: store.sorted(for: bot.id).first?.id)
    }

    @ViewBuilder
    private func contextMenu(for bot: ChatBot) -> some View {
        if !bot.isChiefOfStaff {
            Button { editing = bot } label: { Label("Edit", systemImage: "pencil") }
            Button(role: .destructive) { confirmDelete = bot } label: { Label("Delete", systemImage: "trash") }
        }
    }
}

/// Short timestamps like the Grok Bot list: "now", "5m", "3h", "Mon", "12/10".
enum ShortTime {
    static func string(_ d: Date, now: Date = Date()) -> String {
        let s = now.timeIntervalSince(d)
        if s < 60 { return "now" }
        if s < 3600 { return "\(Int(s / 60))m" }
        let cal = Calendar.current
        if cal.isDateInToday(d) { return d.formatted(date: .omitted, time: .shortened) }
        if cal.isDateInYesterday(d) { return "Yesterday" }
        if s < 6 * 86400 { return d.formatted(.dateTime.weekday(.abbreviated)) }
        return d.formatted(.dateTime.day().month(.defaultDigits))
    }
}

struct BotAvatar: View {
    let bot: ChatBot
    var size: CGFloat = 48
    var body: some View {
        ZStack {
            Circle().fill(bot.avatarColor)
            Text(bot.emoji).font(.system(size: size * 0.48))
        }
        .frame(width: size, height: size)
        .overlay(Circle().strokeBorder(Color.primary.opacity(0.08)))
        .accessibilityHidden(true)
    }
}

struct BotRow: View {
    let bot: ChatBot
    let preview: (text: String, date: Date?)
    var featured = false
    var unread = false

    var body: some View {
        HStack(spacing: 14) {
            BotAvatar(bot: bot, size: 52)
            VStack(alignment: .leading, spacing: 3) {
                HStack(alignment: .firstTextBaseline) {
                    Text(bot.name).font(.headline).lineLimit(1)
                    if bot.isChiefOfStaff {
                        Text("Chief of Staff")
                            .font(.caption2.weight(.semibold))
                            .padding(.horizontal, 6).padding(.vertical, 2)
                            .background(Color.accentColor.opacity(0.18), in: Capsule())
                    }
                    Spacer(minLength: 8)
                    if let d = preview.date {
                        Text(ShortTime.string(d))
                            .font(.caption)
                            .foregroundStyle(unread ? Color.accentColor : Color.secondary)
                    }
                }
                HStack {
                    Text(preview.text)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                    Spacer(minLength: 8)
                    if unread {
                        Circle().fill(Color.accentColor).frame(width: 9, height: 9)
                            .accessibilityLabel("Unread")
                    }
                }
            }
        }
        .padding(.vertical, 2)
        .contentShape(Rectangle())
    }
}

struct EditBotSheet: View {
    let existing: ChatBot?
    @EnvironmentObject var bots: ChatBotStore
    @EnvironmentObject var settings: LLMSettings
    @Environment(\.dismiss) private var dismiss

    @State private var name = ""
    @State private var emoji = "💡"
    @State private var hue: Double = 0.60
    @State private var persona = ""
    @State private var role = ""
    @State private var useGlobalKey = true
    @State private var provider: LLMProvider = .openai
    @State private var model = ""
    @State private var baseURL = ""
    @State private var key = ""

    var isNew: Bool { existing == nil }

    var body: some View {
        NavigationStack {
            Form {
                Section("Identity") {
                    HStack {
                        BotAvatar(bot: previewBot, size: 52)
                        TextField("Name", text: $name)
                    }
                    TextField("Role, e.g. Research assistant", text: $role)
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack {
                            ForEach(ChatBotEmoji.presets, id: \.self) { e in
                                Button {
                                    emoji = e
                                } label: {
                                    Text(e)
                                        .font(.title2)
                                        .padding(8)
                                        .background(emoji == e ? Color.accentColor.opacity(0.2) : Color.clear, in: Circle())
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }
                    HStack {
                        Text("Color")
                        Slider(value: $hue, in: 0...1)
                        Circle().fill(Color(hue: hue, saturation: 0.55, brightness: 0.82)).frame(width: 22, height: 22)
                    }
                }
                Section {
                    TextField("What should this bot be good at? Tone, expertise, limits…", text: $persona, axis: .vertical)
                        .lineLimit(4...10)
                } header: {
                    Text("Persona / system prompt")
                } footer: {
                    Text("Used as the system prompt for this bot’s chats. Leave empty to use a short default.")
                }
                Section {
                    Picker("Provider", selection: $provider) {
                        ForEach(LLMProvider.allCases) { p in Text(p.displayName).tag(p) }
                    }
                    // Simpler: always a provider picker defaulting to global
                    TextField("Model", text: $model)
                        .textInputAutocapitalization(.never).autocorrectionDisabled()
                        .font(.callout.monospaced())
                    if provider == .custom {
                        TextField("Base URL", text: $baseURL)
                            .textInputAutocapitalization(.never).autocorrectionDisabled().keyboardType(.URL)
                    }
                    Toggle("Use a different API key", isOn: $useGlobalKey.toggledInverted)
                    if !useGlobalKey {
                        SecureField("Paste API key", text: $key)
                            .textInputAutocapitalization(.never).autocorrectionDisabled()
                        Text("Stored only in this iPhone’s Keychain and sent only to the provider you pick.")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                } header: {
                    Text("Provider & model")
                } footer: {
                    Text("By default this bot uses the API key and model saved in Settings. You can give it its own key if you want.")
                }
            }
            .navigationTitle(isNew ? "Create Bot" : "Edit Bot")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) { Button("Cancel") { dismiss() } }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") { save() }.disabled(name.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
            .onAppear { load() }
        }
        .presentationDragIndicator(.visible)
    }

    private var previewBot: ChatBot {
        ChatBot(id: existing?.id ?? UUID(), name: name, role: role, emoji: emoji, hue: hue,
                persona: persona, useGlobalKey: useGlobalKey, providerRaw: provider.rawValue,
                model: model, baseURLOverride: baseURL, createdAt: Date(), updatedAt: Date(), lastViewedAt: nil)
    }

    private func load() {
        let g = settings
        if let b = existing {
            name = b.name
            emoji = b.emoji
            hue = b.hue
            persona = b.persona
            role = b.role
            useGlobalKey = b.useGlobalKey
            provider = b.provider ?? g.provider
            model = b.model ?? g.model
            baseURL = b.baseURLOverride
            key = ""
        } else {
            provider = g.provider
            model = g.model
            hue = Double.random(in: 0...1)
        }
    }

    private func save() {
        var bot = existing ?? ChatBot(
            id: UUID(), name: "", role: "", emoji: "💡", hue: hue, persona: "",
            useGlobalKey: true, providerRaw: nil, model: nil, baseURLOverride: "",
            createdAt: Date(), updatedAt: Date(), lastViewedAt: nil
        )
        bot.name = name.trimmingCharacters(in: .whitespacesAndNewlines)
        bot.role = role.trimmingCharacters(in: .whitespacesAndNewlines)
        bot.emoji = emoji
        bot.hue = hue
        bot.persona = persona.trimmingCharacters(in: .whitespacesAndNewlines)
        bot.useGlobalKey = useGlobalKey
        bot.providerRaw = provider.rawValue
        bot.model = model.trimmingCharacters(in: .whitespacesAndNewlines)
        bot.baseURLOverride = baseURL
        bots.upsert(bot)
        if !useGlobalKey {
            if !key.isEmpty { bots.setAPIKey(key, for: bot.id) }
        } else {
            bots.setAPIKey(nil, for: bot.id)
        }
        dismiss()
    }
}

private extension Binding where Value == Bool {
    var toggledInverted: Binding<Bool> {
        Binding(
            get: { !wrappedValue },
            set: { wrappedValue = !$0 }
        )
    }
}
