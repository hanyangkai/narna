//
//  AIChatView.swift
//  NARNA
//

import SwiftUI

struct AIChatView: View {
    @EnvironmentObject var app: AppState
    @EnvironmentObject var settings: LLMSettings
    @EnvironmentObject var store: ConversationStore
    @EnvironmentObject var bots: ChatBotStore
    @StateObject private var vm = AIChatViewModel()
    @FocusState private var inputFocused: Bool

    private let suggestions = [
        "Research Wikipedia on decision quality and summarize it",
        "Calculate (19.99 * 3) + 4.5 and remind me to review the total",
        "Draft a polite follow-up email for a late invoice",
        "1. Translate hello to Spanish\n2. Add a to-do to practice Spanish",
    ]

    var body: some View {
        VStack(spacing: 0) {
            Group {
                if vm.emptyStateNeedsSetup {
                    NoKeyEmptyState { app.navigate(.settings) }
                } else if let convo = vm.conversation, !convo.messages.isEmpty {
                    messageList(convo)
                } else if vm.currentBot.isChiefOfStaff {
                    StartEmptyState(suggestions: suggestions) { s in
                        vm.input = s
                        vm.send()
                    }
                } else {
                    BotEmptyState(bot: vm.currentBot) { s in
                        vm.input = s
                        vm.send()
                    }
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            // Tap anywhere outside the input to put the keyboard away.
            .contentShape(Rectangle())
            .simultaneousGesture(TapGesture().onEnded { dismissKeyboard() })
            if vm.isReady { inputBar }
        }
        .background(Color(.systemBackground))
        .navigationBarTitleDisplayMode(.inline)
        .toolbar(.visible, for: .navigationBar)
        .toolbar {
            ToolbarItem(placement: .principal) {
                HStack(spacing: 8) {
                    BotAvatar(bot: vm.currentBot, size: 28)
                    VStack(alignment: .leading, spacing: 0) {
                        Text(vm.currentBot.name)
                            .font(.subheadline.weight(.semibold))
                            .lineLimit(1)
                        if vm.isReady {
                            Text(vm.activeModel)
                                .font(.caption2.monospaced())
                                .foregroundStyle(.secondary)
                                .lineLimit(1)
                        }
                    }
                }
                .accessibilityElement(children: .combine)
            }
            ToolbarItem(placement: .topBarTrailing) {
                HStack(spacing: 14) {
                    Button {
                        if vm.agentModeEnabled {
                            vm.agentModeEnabled = false
                        } else if AgentSubscriptionManager.shared.isSubscribed {
                            vm.agentModeEnabled = true
                        } else {
                            vm.showPaywall = true
                        }
                    } label: {
                        Image(systemName: vm.agentModeEnabled ? "sparkles.rectangle.stack.fill" : "sparkles")
                    }
                    .accessibilityLabel(vm.agentModeEnabled ? "Agent mode on" : "Agent mode")
                    Button { dismissKeyboard(); app.navigate(.history) } label: { Image(systemName: "clock.arrow.circlepath") }
                        .accessibilityLabel("History")
                    Button { vm.newChat() } label: { Image(systemName: "square.and.pencil") }
                        .disabled(vm.conversation == nil)
                        .accessibilityLabel("New chat")
                }
            }
        }
        .onAppear {
            bots.markViewed(vm.currentBot.id)
            #if DEBUG
            if ProcessInfo.processInfo.arguments.contains("-NARNA_DEMO_AUTOSEND"), vm.conversation == nil, vm.isReady {
                vm.input = "Our 12-person team wants to move from Jenkins to a hosted CI. Should we switch now?"
                vm.send()
            }
            if ProcessInfo.processInfo.arguments.contains("-NARNA_FOCUS_INPUT") {
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.6) { inputFocused = true }
            }
            #endif
        }
        .onDisappear {
            dismissKeyboard()
            bots.markViewed(vm.currentBot.id)
        }
        .sheet(isPresented: $vm.showPaywall) {
            PaywallView()
                .environmentObject(AgentSubscriptionManager.shared)
        }
    }

    private func dismissKeyboard() {
        inputFocused = false
        narnaEndEditing()
    }

    private func messageList(_ convo: Conversation) -> some View {
        ScrollViewReader { proxy in
            ScrollView {
                LazyVStack(alignment: .leading, spacing: 14) {
                    ForEach(convo.messages) { msg in
                        VStack(alignment: .leading, spacing: 8) {
                            AIMessageRow(message: msg) { vm.retry(errorMessageID: msg.id) }
                            if msg.role == .assistant && !msg.isError {
                                if let tasks = msg.agentTasks, !tasks.isEmpty {
                                    AgentTaskProgressView(tasks: tasks, isLive: false)
                                }
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
                        VStack(alignment: .leading, spacing: 10) {
                            if !vm.liveAgentTasks.isEmpty {
                                AgentTaskProgressView(tasks: vm.liveAgentTasks, isLive: true)
                            } else {
                                HStack(spacing: 8) {
                                    ProgressView().controlSize(.small)
                                    Text("Thinking…").font(.callout).foregroundStyle(.secondary)
                                }
                            }
                        }
                        .id("typing")
                    }
                }
                .padding()
                    .padding(.bottom, 24)
            }
            .scrollDismissesKeyboard(.immediately)   // any drag on the list puts the keyboard away
            .scrollBounceBehavior(.always)
            .defaultScrollAnchor(.bottom)
            .onChange(of: inputFocused) { _, focused in
                guard focused else { return }
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                    withAnimation { proxy.scrollTo(convo.messages.last?.id, anchor: .bottom) }
                }
            }
            .onChange(of: convo.messages) { _, _ in
                withAnimation { proxy.scrollTo(convo.messages.last?.id, anchor: .bottom) }
            }
            .onAppear { proxy.scrollTo(convo.messages.last?.id, anchor: .bottom) }
        }
    }

    private var inputBar: some View {
        HStack(alignment: .bottom, spacing: 10) {
            TextField("Message \(vm.currentBot.name)", text: $vm.input, axis: .vertical)
                .lineLimit(1...6)
                .focused($inputFocused)
                .padding(.horizontal, 14)
                .padding(.vertical, 10)
                .background(Color(.secondarySystemBackground))
                .clipShape(RoundedRectangle(cornerRadius: 20))
            if inputFocused {
                Button { dismissKeyboard() } label: {
                    Image(systemName: "keyboard.chevron.compact.down")
                        .font(.system(size: 20))
                        .foregroundStyle(.secondary)
                        .frame(width: 34, height: 34)
                }
                .accessibilityLabel("Hide keyboard")
                .transition(.opacity)
            }
            Button { vm.send() } label: {
                Image(systemName: "arrow.up.circle.fill").font(.system(size: 34))
            }
            .disabled(!vm.canSend)
            .accessibilityLabel("Send")
        }
        .padding(.horizontal)
        .padding(.vertical, 8)
        .padding(.bottom, 4)
        .background(.bar)
        .animation(.easeInOut(duration: 0.15), value: inputFocused)
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
                if message.role == .assistant, let name = message.modelDisplayName, !name.isEmpty {
                    Text(name)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                        .accessibilityLabel("Model \(name)")
                }
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
            Text("Free chat is not available on this iPhone yet")
                .font(.title2.bold())
            Text("Nana AI chats for free with the on-device model when Apple Intelligence is available, or with the free cloud pool (Gemini Flash, GPT-OSS, Gemma). You can also add your own API key in Settings > Advanced, or subscribe to Nana Agent.")
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
                Text("Ask Nana AI anything")
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
                .padding(.bottom, 36)
            }
        }
        .scrollDismissesKeyboard(.immediately)   // any drag on the list puts the keyboard away
    }
}

/// Empty state for user-created bots. The Chief of Staff keeps StartEmptyState / NoKeyEmptyState.
struct BotEmptyState: View {
    let bot: ChatBot
    var pick: (String) -> Void
    var body: some View {
        ScrollView {
        VStack(spacing: 16) {
            Spacer(minLength: 80)
            BotAvatar(bot: bot, size: 72)
            Text("Message \(bot.name)")
                .font(.title2.bold())
            if !bot.role.isEmpty {
                Text(bot.role).font(.callout).foregroundStyle(.secondary)
            }
            if !bot.persona.isEmpty {
                Text(bot.persona)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 28)
                    .lineLimit(4)
            }
            Spacer(minLength: 40)
        }
        .frame(maxWidth: .infinity)
        }
        .scrollBounceBehavior(.always)
        .scrollDismissesKeyboard(.immediately)   // any drag on the list puts the keyboard away
    }
}
