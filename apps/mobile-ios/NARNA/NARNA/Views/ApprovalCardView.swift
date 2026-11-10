//
//  ApprovalCardView.swift
//  NARNA
//
//  Created by NARNA Team on 11/10/2026.
//

import SwiftUI

struct ApprovalCardView: View {
    let approval: ApprovalInfo
    let onAllow: () -> Void
    let onDeny: () -> Void
    
    @State private var isProcessing = false
    @Environment(\.dismiss) var dismiss
    
    var body: some View {
        NavigationView {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    HStack {
                        Image(systemName: approval.actionTypeIcon)
                            .font(.system(size: 40))
                            .foregroundColor(actionColor)
                            .frame(width: 60, height: 60)
                            .background(actionColor.opacity(0.1))
                            .cornerRadius(12)
                        
                        VStack(alignment: .leading, spacing: 4) {
                            Text(actionTypeText)
                                .font(.headline)
                            
                            Text(approval.botId)
                                .font(.caption)
                                .foregroundColor(.secondary)
                        }
                        
                        Spacer()
                    }
                    
                    VStack(alignment: .leading, spacing: 12) {
                        Text("Description")
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                        
                        Text(approval.description)
                            .font(.body)
                            .padding()
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(Color(.systemGray6))
                            .cornerRadius(8)
                    }
                    
                    if !approval.details.isEmpty {
                        VStack(alignment: .leading, spacing: 12) {
                            Text("Details")
                                .font(.subheadline)
                                .foregroundColor(.secondary)
                            
                            VStack(alignment: .leading, spacing: 8) {
                                ForEach(Array(approval.details.keys.sorted()), id: \.self) { key in
                                    DetailRow(key: key, value: approval.details[key])
                                }
                            }
                            .padding()
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(Color(.systemGray6))
                            .cornerRadius(8)
                        }
                    }
                    
                    Spacer()
                    
                    VStack(spacing: 12) {
                        Button(action: handleAllow) {
                            if isProcessing {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                    .frame(maxWidth: .infinity)
                                    .padding()
                            } else {
                                HStack {
                                    Image(systemName: "checkmark.circle.fill")
                                    Text("Allow")
                                }
                                .frame(maxWidth: .infinity)
                                .padding()
                            }
                        }
                        .background(Color.green)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                        .disabled(isProcessing)
                        
                        Button(action: handleDeny) {
                            if isProcessing {
                                ProgressView()
                                    .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                    .frame(maxWidth: .infinity)
                                    .padding()
                            } else {
                                HStack {
                                    Image(systemName: "xmark.circle.fill")
                                    Text("Deny")
                                }
                                .frame(maxWidth: .infinity)
                                .padding()
                            }
                        }
                        .background(Color.red)
                        .foregroundColor(.white)
                        .cornerRadius(12)
                        .disabled(isProcessing)
                    }
                }
                .padding()
            }
            .navigationTitle("Approval Required")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Cancel") {
                        dismiss()
                    }
                    .disabled(isProcessing)
                }
            }
        }
    }
    
    private var actionColor: Color {
        switch approval.actionTypeColor {
        case "blue": return .blue
        case "green": return .green
        case "purple": return .purple
        default: return .gray
        }
    }
    
    private var actionTypeText: String {
        switch approval.actionType {
        case "shell_command": return "Shell Command"
        case "file_edit": return "File Edit"
        case "web_action": return "Web Action"
        default: return "Unknown Action"
        }
    }
    
    private func handleAllow() {
        isProcessing = true
        onAllow()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            dismiss()
        }
    }
    
    private func handleDeny() {
        isProcessing = true
        onDeny()
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
            dismiss()
        }
    }
}

struct DetailRow: View {
    let key: String
    let value: AnyCodable?
    
    var body: some View {
        HStack(alignment: .top, spacing: 8) {
            Text(formatKey(key))
                .font(.caption)
                .foregroundColor(.secondary)
                .frame(width: 100, alignment: .leading)
            
            Text(formatValue(value))
                .font(.caption)
                .foregroundColor(.primary)
            
            Spacer()
        }
    }
    
    private func formatKey(_ key: String) -> String {
        key.replacingOccurrences(of: "_", with: " ")
            .capitalized
    }
    
    private func formatValue(_ value: AnyCodable?) -> String {
        guard let value = value?.value else {
            return "N/A"
        }
        
        if let string = value as? String {
            return string
        } else if let number = value as? Int {
            return "\(number)"
        } else if let double = value as? Double {
            return String(format: "%.2f", double)
        } else if let bool = value as? Bool {
            return bool ? "Yes" : "No"
        } else {
            return String(describing: value)
        }
    }
}

#Preview {
    ApprovalCardView(
        approval: ApprovalInfo(
            approvalId: "approval_1",
            botId: "bot_1",
            actionType: "shell_command",
            description: "Run: git pull origin main",
            details: [
                "command": AnyCodable("git pull origin main"),
                "working_dir": AnyCodable("/workspace")
            ],
            createdAt: ISO8601DateFormatter().string(from: Date())
        ),
        onAllow: {},
        onDeny: {}
    )
}
