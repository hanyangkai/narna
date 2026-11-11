//
//  HistoryView.swift
//  NARNA
//

import SwiftUI

struct HistoryView: View {
    @EnvironmentObject var app: AppState
    @EnvironmentObject var store: ConversationStore
    @State private var confirmDeleteAll = false

    var body: some View {
        NavigationStack {
            Group {
                if store.conversations.isEmpty {
                    ContentUnavailableView("No conversations yet",
                                           systemImage: "bubble.left.and.text.bubble.right",
                                           description: Text("Your chats are saved only on this iPhone."))
                } else {
                    List {
                        ForEach(store.sorted) { c in
                            Button {
                                app.currentConversationID = c.id
                                app.selectedTab = .chat
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
                                .contentShape(Rectangle())
                            }
                            .buttonStyle(.plain)
                        }
                        .onDelete { idx in
                            let list = store.sorted
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
            .toolbar {
                if !store.conversations.isEmpty {
                    ToolbarItem(placement: .topBarTrailing) {
                        Button(role: .destructive) { confirmDeleteAll = true } label: { Image(systemName: "trash") }
                            .accessibilityLabel("Delete all")
                    }
                }
            }
            .confirmationDialog("Delete all conversations from this iPhone?", isPresented: $confirmDeleteAll, titleVisibility: .visible) {
                Button("Delete All", role: .destructive) {
                    app.currentConversationID = nil
                    store.deleteAll()
                }
            }
        }
    }
}
