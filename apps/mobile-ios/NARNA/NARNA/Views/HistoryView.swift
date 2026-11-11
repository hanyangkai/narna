//
//  HistoryView.swift
//  NARNA
//

import SwiftUI

struct HistoryView: View {
    @EnvironmentObject var app: AppState
    @EnvironmentObject var store: ConversationStore
    @State private var confirmDeleteAll = false
    @State private var autoOpenFirst = false

    var body: some View {
        NavigationStack {
            Group {
                if store.sorted(for: app.currentBotID).isEmpty {
                    ContentUnavailableView("No conversations yet",
                                           systemImage: "bubble.left.and.text.bubble.right",
                                           description: Text("Your chats are saved only on this iPhone."))
                } else {
                    List {
                        ForEach(store.sorted(for: app.currentBotID)) { c in
                            NavigationLink {
                                HistoryDetailView(conversation: c)
                            } label: {
                                VStack(alignment: .leading, spacing: 4) {
                                    HStack {
                                        Text(c.title).font(.headline).lineLimit(1)
                                        Spacer()
                                        Text(c.updatedAt.formatted(.relative(presentation: .named)))
                                            .font(.caption2).foregroundStyle(.secondary)
                                    }
                                    Text(c.preview.replacingOccurrences(of: "**", with: "").replacingOccurrences(of: "\n", with: " ")).font(.subheadline).foregroundStyle(.secondary).lineLimit(2)
                                    HStack(spacing: 8) {
                                        Label("\(c.messages.count)", systemImage: "text.bubble").font(.caption2)
                                        if let m = c.model { Text(m).font(.caption2.monospaced()) }
                                        if let d = c.messages.last(where: { $0.adqa != nil })?.adqa {
                                            Text("DQS \(d.dqs) · \(d.guardian.label)").font(.caption2.bold())
                                        }
                                    }
                                    .foregroundStyle(.secondary)
                                }
                                .padding(.vertical, 4)
                            }
                        }
                        .onDelete { idx in
                            let list = store.sorted(for: app.currentBotID)
                            for i in idx {
                                let id = list[i].id
                                if app.currentConversationID == id { app.currentConversationID = nil }
                                store.delete(id)
                            }
                        }
                    }
                }
            }
            .navigationTitle("History")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button("Done") { app.showHistory = false }
                        .accessibilityLabel("Close History")
                }
                if !store.sorted(for: app.currentBotID).isEmpty {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button(role: .destructive) { confirmDeleteAll = true } label: { Image(systemName: "trash") }
                            .accessibilityLabel("Delete all")
                    }
                }
            }
            .confirmationDialog("Delete all conversations for this bot from this iPhone?", isPresented: $confirmDeleteAll, titleVisibility: .visible) {
                Button("Delete All", role: .destructive) {
                    if app.currentConversationID != nil,
                       store.conversation(app.currentConversationID)?.botID == app.currentBotID {
                        app.currentConversationID = nil
                    }
                    store.deleteAll(for: app.currentBotID)
                }
            }
            .navigationDestination(isPresented: $autoOpenFirst) {
                if let c = store.sorted(for: app.currentBotID).first {
                    HistoryDetailView(conversation: c)
                }
            }
            .onAppear {
                #if DEBUG
                if ProcessInfo.processInfo.arguments.contains("-NARNA_OPEN_HISTORY_DETAIL"),
                   store.sorted(for: app.currentBotID).first != nil {
                    autoOpenFirst = true
                }
                #endif
            }
        }
        .narnaTabRoot()
    }
}

/// Pushed from History. System back + swipe-back return to the list; Open in Chat jumps to the Chat tab.
struct HistoryDetailView: View {
    let conversation: Conversation
    @EnvironmentObject var app: AppState

    var body: some View {
        ScrollView {
            LazyVStack(alignment: .leading, spacing: 14) {
                if conversation.messages.isEmpty {
                    Text("No messages in this conversation.")
                        .foregroundStyle(.secondary)
                        .frame(maxWidth: .infinity, alignment: .leading)
                }
                ForEach(conversation.messages) { msg in
                    VStack(alignment: .leading, spacing: 8) {
                        AIMessageRow(message: msg) {}
                        if let a = msg.adqa {
                            ADQACardView(assessment: a)
                        }
                    }
                }
            }
            .padding()
            .padding(.bottom, 36)
        }
        .navigationTitle(conversation.title)
        .navigationBarTitleDisplayMode(.inline)
        .navigationBarBackButtonHidden(false)
        .toolbar(.visible, for: .navigationBar)
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button("Open in Chat") {
                    app.currentConversationID = conversation.id
                    app.navigate(.chat)
                }
            }
        }
    }
}
