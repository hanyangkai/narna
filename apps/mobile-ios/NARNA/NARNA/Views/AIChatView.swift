//
//  AIChatView.swift
//  NARNA
//

import SwiftUI

struct AIChatView: View {
    @EnvironmentObject var app: AppState
    @EnvironmentObject var settings: LLMSettings
    @EnvironmentObject var store: ConversationStore
    @StateObject private var vm = AIChatViewModel()
    @FocusState private var inputFocused: Bool

    private let suggestions = [
        "Should we switch our team to a new CI provider?",
        "Help me plan a 3-day trip on a budget",
        "Explain this error message and how to fix it",
        "Draft a polite follow-up email for a late invoice"
    ]

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                if !settings.isReady {
                    NoKeyEmptyState { app.selectedTab = .settings }
                } else if let convo = vm.conversation, !convo.messages.isEmpty {
                    messageList(convo)
                } else {
                    StartEmptyState(suggestions: suggestions) { s in
                        vm.input = s
                        vm.send()
                    }
                }
                if settings.isReady { inputBar }
            }
            .navigationTitle(vm.conversation?.title ?? "NaNa Bot")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    if settings.isReady {
                        Text(settings.model)
                            .font(.caption2.monospaced())
                            .foregroundStyle(.secondary)
                            .lineLimit(1)
                            .fixedSize()
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Button { vm.newChat() } label: { Image(systemName: "square.and.pencil") }
                        .disabled(vm.conversation == nil)
                        .accessibilityLabel("New chat")
                }
            }
            .onAppear {
                #if DEBUG
                if ProcessInfo.processInfo.arguments.contains("-NARNA_DEMO_AUTOSEND"), vm.conversation == nil {
                    vm.input = "Our 12-person team wants to move from Jenkins to a hosted CI. Should we switch now?"
                    vm.send()
                }
                #endif
            }
        }
    }

    private func messageList(_ convo: Conversation) -> some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 14) {
                    ForEach(convo.messages) { msg in
                        VStack(alignment: .leading, spacing: 8) {
                            AIMessageRow(message: msg) { vm.retry(errorMessageID: msg.id) }
                            if msg.role == .assistant && !msg.isError {
                                if let a = msg.adqa {
                                    ADQACardView(assessment: a)
                                } else if vm.scoringIDs.contains(msg.id) {
                                    HStack(spacing: 8) {
                                        ProgressView().controlSize(.small)
                                        Text("ADQA is scoring this answer…").font(.caption).foregroundStyle(.secondary)
                                    }
                                    .padding(.leading, 4)
                                } else if settings.adqaEnabled {
                                    Button { vm.rescore(messageID: msg.id) } label: {
                                        Label("Score with ADQA", systemImage: "gauge.with.dots.needle.67percent")
                                            .font(.caption)
                                    }
                                    .buttonStyle(.bordered)
                                    .controlSize(.small)
                                }
                            }
                        }
                        .id(msg.id)
                    }
                    if vm.isSending {
                        HStack(spacing: 8) {
                            ProgressView().controlSize(.small)
                            Text("Thinking…").font(.callout).foregroundStyle(.secondary)
                        }
                        .id("typing")
                    }
                }
                .padding()
            }
            .scrollDismissesKeyboard(.interactively)
            .onChange(of: convo.messages) { _, _ in
                withAnimation { proxy.scrollTo(convo.messages.last?.id, anchor: .bottom) }
            }
            .onAppear { proxy.scrollTo(convo.messages.last?.id, anchor: .bottom) }
        }
    }

    private var inputBar: some View {
        HStack(alignment: .bottom, spacing: 10) {
            TextField("Message NaNa Bot", text: $vm.input, axis: .vertical)
                .lineLimit(1...6)
                .focused($inputFocused)
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(Color(.secondarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 20))
            Button { vm.send() } label: {
                Image(systemName: "arrow.up.circle.fill").font(.system(size: 34))
            }
            .disabled(!vm.canSend)
            .accessibilityLabel("Send")
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .background(.bar)
    }
}

struct AIMessageRow: View {
    let message: AIMessage
    var onRetry: () -> Void

    var body: some View {
        HStack {
            if message.role == .user { Spacer(minLength: 40) }
            VStack(alignment: .leading, spacing: 8) {
                if message.isError {
                    Label("Couldn't get an answer", systemImage: "exclamationmark.triangle.fill")
                        .font(.caption.bold())
                        .foregroundStyle(.orange)
                }
                Text(Self.markdown(message.content))
                    .textSelection(.enabled)
                    .font(.body)
                if message.isError {
                    Button("Retry", action: onRetry).buttonStyle(.bordered).controlSize(.small)
                }
            }
            .padding(12)
            .background(background)
            .foregroundStyle(message.role == .user ? Color.white : Color.primary)
            .clipShape(RoundedRectangle(cornerRadius: 16))
            if message.role == .assistant { Spacer(minLength: 24) }
        }
    }

    private var background: Color {
        if message.isError { return Color.orange.opacity(0.15) }
        return message.role == .user ? Color.accentColor : Color(.secondarySystemBackground)
    }

    static func markdown(_ s: String) -> AttributedString {
        // Render block markdown loosely: headings -> bold, keep line breaks.
        let lines = s.components(separatedBy: "\n").map { line -> String in
            let t = line.trimmingCharacters(in: .whitespaces)
            if t.hasPrefix("#") {
                let h = t.drop(while: { $0 == "#" }).trimmingCharacters(in: .whitespaces)
                return h.isEmpty ? "" : "**\(h)**"
            }
            if t.hasPrefix("- ") || t.hasPrefix("* ") { return "• " + t.dropFirst(2) }
            return line
        }
        let joined = lines.joined(separator: "\n")
        let opts = AttributedString.MarkdownParsingOptions(interpretedSyntax: .inlineOnlyPreservingWhitespace)
        return (try? AttributedString(markdown: joined, options: opts)) ?? AttributedString(s)
    }
}

struct NoKeyEmptyState: View {
    var openSettings: () -> Void
    var body: some View {
        VStack(spacing: 18) {
            Spacer()
            Image(systemName: "key.horizontal.fill")
                .font(.system(size: 56))
                .foregroundStyle(Color.accentColor)
            Text("Add your API key to start")
                .font(.title2.bold())
            Text("NaNa Bot works with your own API key from OpenAI, Anthropic, OpenRouter, ckey.vn, Groq, DeepSeek, Gemini, xAI, Together, Mistral or any OpenAI-compatible service. The key is stored only in this iPhone's Keychain and requests go directly to the provider you choose.")
                .font(.callout)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 32)
            Button(action: openSettings) {
                Label("Open Settings", systemImage: "gearshape")
                    .frame(maxWidth: 260)
                    .padding(.vertical, 6)
            }
            .buttonStyle(.borderedProminent)
            Text("Every answer gets an ADQA decision-quality score.")
                .font(.caption)
                .foregroundStyle(.secondary)
            Spacer()
        }
        .frame(maxWidth: .infinity)
    }
}

struct StartEmptyState: View {
    let suggestions: [String]
    var pick: (String) -> Void
    var body: some View {
        ScrollView {
            VStack(spacing: 16) {
                Image(systemName: "sparkles")
                    .font(.system(size: 48))
                    .foregroundStyle(Color.accentColor)
                    .padding(.top, 60)
                Text("Ask NaNa Bot anything")
                    .font(.title2.bold())
                Text("Each answer comes with an ADQA card that scores its decision quality: evidence, risk, confidence and more.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 28)
                VStack(spacing: 10) {
                    ForEach(suggestions, id: \.self) { s in
                        Button { pick(s) } label: {
                            Text(s).font(.callout).frame(maxWidth: .infinity, alignment: .leading)
                                .padding(12)
                                .background(Color(.secondarySystemBackground))
                                .clipShape(RoundedRectangle(cornerRadius: 12))
                        }
                        .buttonStyle(.plain)
                    }
                }
                .padding(.horizontal)
            }
        }
    }
}
