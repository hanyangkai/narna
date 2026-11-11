//
//  BotsView.swift
//  NARNA
//
//  List of chat bots. NaNa Bot (Chief of Staff) is pinned at the top and cannot
//  be deleted. User bots are stored only on this iPhone.
//

import SwiftUI

struct BotsView: View {
    @EnvironmentObject var app: AppState
    @EnvironmentObject var bots: ChatBotStore
    @EnvironmentObject var store: ConversationStore
    @EnvironmentObject var settings: LLMSettings
    @Environment(\.dismiss) private var dismiss
    @State private var query = ""
    @State private var showCreate = false
    @State private var editing: ChatBot?
    @State private var confirmDelete: ChatBot?

    var body: some View {
        NavigationStack {
            ScrollView {
                LazyVStack(spacing: 10) {
                    ForEach(Array(bots.filtered(query: query).enumerated()), id: \.element.id) { i, bot in
                        let featured = i == 0 && bot.isChiefOfStaff && query.isEmpty
                        Button {
                            open(bot)
                        } label: {
                            BotRow(bot: bot, preview: preview(for: bot), featured: featured, unread: unread(for: bot))
                        }
                        .buttonStyle(.plain)
                        .contextMenu { contextMenu(for: bot) }
                        .swipeActions(edge: .trailing, allowsFullSwipe: false) {
                            if !bot.isChiefOfStaff {
                                Button(role: .destructive) { confirmDelete = bot } label: { Label("Delete", systemImage: "trash") }
                                Button { editing = bot } label: { Label("Edit", systemImage: "pencil") }
                                    .tint(.blue)
                            }
                        }
                    }
                }
                .padding(.horizontal)
                .padding(.top, 8)
                .padding(.bottom, 16)
            }
            .navigationTitle("Bots")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button { showCreate = true } label: { Image(systemName: "plus") }
                        .accessibilityLabel("Create bot")
                }
            }
            .safeAreaInset(edge: .bottom) {
                HStack {
                    Image(systemName: "magnifyingglass").foregroundStyle(.secondary)
                    TextField("Search bots", text: $query)
                        .textInputAutocapitalization(.never)
                        .autocorrectionDisabled()
                }
                .padding(12)
                .background(.ultraThinMaterial, in: Capsule())
                .padding(.horizontal, 20)
                .padding(.vertical, 10)
            }
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
        }
        .presentationDragIndicator(.visible)
            .onAppear {
                #if DEBUG
                if ProcessInfo.processInfo.arguments.contains("-NARNA_OPEN_CREATE") {
                    showCreate = true
                }
                #endif
            }
    }

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
        app.currentBotID = bot.id
        app.currentConversationID = store.sorted(for: bot.id).first?.id
        bots.markViewed(bot.id)
        dismiss()
    }

    @ViewBuilder
    private func contextMenu(for bot: ChatBot) -> some View {
        if !bot.isChiefOfStaff {
            Button { editing = bot } label: { Label("Edit", systemImage: "pencil") }
            Button(role: .destructive) { confirmDelete = bot } label: { Label("Delete", systemImage: "trash") }
        }
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
        HStack(spacing: 12) {
            BotAvatar(bot: bot, size: featured ? 64 : 48)
            VStack(alignment: .leading, spacing: 3) {
                HStack {
                    Text(bot.name).font(featured ? .title3.bold() : .headline).lineLimit(1)
                    if bot.isChiefOfStaff {
                        Text("Chief of Staff")
                            .font(.caption2.weight(.semibold))
                            .padding(.horizontal, 6).padding(.vertical, 2)
                            .background(Color.accentColor.opacity(0.18), in: Capsule())
                    }
                    Spacer()
                    if let d = preview.date {
                        Text(d.formatted(.relative(presentation: .named)))
                            .font(.caption2).foregroundStyle(.secondary)
                    }
                    if unread {
                        Circle().fill(Color.accentColor).frame(width: 8, height: 8)
                            .accessibilityLabel("Unread")
                    }
                }
                Text(preview.text)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .lineLimit(featured ? 2 : 1)
            }
        }
        .padding(featured ? 14 : 10)
        .background(Color(.secondarySystemBackground), in: RoundedRectangle(cornerRadius: featured ? 20 : 16, style: .continuous))
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
