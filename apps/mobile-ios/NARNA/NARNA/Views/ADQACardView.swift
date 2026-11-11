//
//  ADQACardView.swift
//  NARNA
//
//  Shows the ADQA (NGS-0024) decision-quality assessment for an answer.
//

import SwiftUI

struct ADQACardView: View {
    let assessment: ADQAAssessment
    @State private var expanded = false

    private var color: Color {
        switch assessment.guardian {
        case .approve: return .green
        case .revise: return .yellow
        case .escalate: return .orange
        case .reject: return .red
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack(spacing: 10) {
                ZStack {
                    Circle().stroke(color.opacity(0.25), lineWidth: 5)
                    Circle().trim(from: 0, to: CGFloat(assessment.dqs) / 100)
                        .stroke(color, style: StrokeStyle(lineWidth: 5, lineCap: .round))
                        .rotationEffect(.degrees(-90))
                    Text("\(assessment.dqs)").font(.system(.subheadline, design: .rounded).bold())
                }
                .frame(width: 44, height: 44)

                VStack(alignment: .leading, spacing: 2) {
                    Text("ADQA · Decision Quality").font(.caption.bold()).foregroundStyle(.secondary)
                    HStack(spacing: 6) {
                        Label(assessment.guardian.label, systemImage: assessment.guardian.symbol)
                            .font(.subheadline.bold())
                            .foregroundStyle(color)
                        Text("Risk: \(assessment.riskBand)")
                            .font(.caption2.bold())
                            .padding(.horizontal, 6).padding(.vertical, 2)
                            .background(Color(.tertiarySystemFill))
                            .clipShape(Capsule())
                    }
                }
                Spacer()
                Button { withAnimation(.snappy) { expanded.toggle() } } label: {
                    Image(systemName: expanded ? "chevron.up.circle.fill" : "chevron.down.circle.fill")
                        .font(.title3)
                        .foregroundStyle(.secondary)
                }
                .accessibilityLabel(expanded ? "Hide details" : "Show details")
            }

            if !assessment.reasons.isEmpty {
                VStack(alignment: .leading, spacing: 4) {
                    ForEach(assessment.reasons, id: \.self) { r in
                        HStack(alignment: .top, spacing: 6) {
                            Text("•").foregroundStyle(color)
                            Text(r).font(.caption)
                        }
                    }
                }
            }

            if expanded {
                Divider()
                let grid = [GridItem(.flexible(), spacing: 12), GridItem(.flexible(), spacing: 12)]
                LazyVGrid(columns: grid, alignment: .leading, spacing: 8) {
                    ForEach(ADQA.attributeKeys, id: \.self) { k in
                        AttributeBar(name: k.capitalized, value: assessment.attributes[k] ?? 0)
                    }
                }
                Text("Constitution").font(.caption.bold()).foregroundStyle(.secondary)
                FlowChips(items: ADQA.constitutionKeys.map { ($0.capitalized, assessment.constitution[$0] ?? "warn") })
                if let rec = assessment.recommendation {
                    Label(rec, systemImage: "lightbulb").font(.caption)
                }
            } else {
                HStack(spacing: 14) {
                    MiniStat(name: "Evidence", value: assessment.attributes["evidence"] ?? 0)
                    MiniStat(name: "Risk", value: assessment.attributes["risk"] ?? 0)
                    MiniStat(name: "Confidence", value: assessment.attributes["confidence"] ?? 0)
                    MiniStat(name: "Policy", value: assessment.attributes["policy"] ?? 0)
                }
            }

            Text(footer)
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 14).fill(Color(.secondarySystemBackground).opacity(0.6))
        )
        .overlay(RoundedRectangle(cornerRadius: 14).stroke(color.opacity(0.5), lineWidth: 1))
    }

    private var footer: String {
        if assessment.source == "heuristic" {
            return "AI-generated assessment unavailable — offline heuristic estimate (NGS-0024). Not professional advice."
        }
        return "AI-generated assessment by \(assessment.model ?? "your model") using ADQA (NGS-0024). Not professional advice."
    }
}

private func scoreColor(_ v: Int) -> Color {
    v >= 80 ? .green : (v >= 60 ? .yellow : .red)
}

struct MiniStat: View {
    let name: String
    let value: Int
    var body: some View {
        VStack(alignment: .leading, spacing: 1) {
            Text("\(value)").font(.system(.callout, design: .rounded).bold()).foregroundStyle(scoreColor(value))
            Text(name).font(.caption2).foregroundStyle(.secondary)
        }
    }
}

struct AttributeBar: View {
    let name: String
    let value: Int
    var body: some View {
        VStack(alignment: .leading, spacing: 3) {
            HStack {
                Text(name).font(.caption2)
                Spacer()
                Text("\(value)").font(.caption2.monospacedDigit().bold())
            }
            GeometryReader { g in
                ZStack(alignment: .leading) {
                    Capsule().fill(Color(.tertiarySystemFill))
                    Capsule().fill(scoreColor(value)).frame(width: g.size.width * CGFloat(value) / 100)
                }
            }
            .frame(height: 5)
        }
    }
}

struct FlowChips: View {
    let items: [(String, String)]
    var body: some View {
        let cols = [GridItem(.adaptive(minimum: 100), spacing: 6)]
        LazyVGrid(columns: cols, alignment: .leading, spacing: 6) {
            ForEach(items, id: \.0) { item in
                HStack(spacing: 4) {
                    Image(systemName: icon(item.1)).foregroundStyle(tint(item.1))
                    Text(item.0)
                }
                .font(.caption2)
                .padding(.horizontal, 8).padding(.vertical, 4)
                .background(tint(item.1).opacity(0.12))
                .clipShape(Capsule())
            }
        }
    }
    private func icon(_ s: String) -> String { s == "pass" ? "checkmark.circle.fill" : (s == "fail" ? "xmark.circle.fill" : "exclamationmark.circle.fill") }
    private func tint(_ s: String) -> Color { s == "pass" ? .green : (s == "fail" ? .red : .orange) }
}
