// Package narna is a Go reference stub for the NARNA Constitution Layer.
// Specs in /specs are the source of truth. Never Replace. Always Extend.
package narna

import "strings"

const Version = "0.1.0"

type Manifest struct {
	APIVersion string `yaml:"apiVersion" json:"apiVersion"`
	Kind       string `yaml:"kind" json:"kind"`
	Metadata   struct {
		Name  string `yaml:"name" json:"name"`
		Owner string `yaml:"owner" json:"owner"`
	} `yaml:"metadata" json:"metadata"`
	Identity struct {
		ID      string `yaml:"id" json:"id"`
		Version string `yaml:"version" json:"version"`
	} `yaml:"identity" json:"identity"`
	Capabilities []string `yaml:"capabilities" json:"capabilities"`
	Trust        struct {
		MinimumScore float64 `yaml:"minimum_score" json:"minimum_score"`
	} `yaml:"trust" json:"trust"`
}

type Constitution map[string]any

var Badges = map[string]string{
	"L1": "NARNA Certified",
	"L2": "NARNA Certified+",
	"L3": "Enterprise Ready",
}

func CompileManifest(m Manifest) Constitution {
	id := m.Identity.ID
	if !strings.HasPrefix(id, "agent_") {
		id = "agent_" + strings.ReplaceAll(id, "-", "_")
	}
	supports := make([]string, 0, len(m.Capabilities))
	for _, c := range m.Capabilities {
		s := strings.ToLower(c)
		s = strings.ReplaceAll(s, ".", "_")
		s = strings.ReplaceAll(s, "-", "_")
		supports = append(supports, s)
	}
	if len(supports) == 0 {
		supports = []string{"general"}
	}
	minScore := m.Trust.MinimumScore
	if minScore == 0 {
		minScore = 0.7
	}
	owner := m.Metadata.Owner
	if owner == "" {
		owner = "local"
	}
	version := m.Identity.Version
	if version == "" {
		version = "0.1.0"
	}
	name := m.Metadata.Name
	if name == "" {
		name = id
	}
	return Constitution{
		"apiVersion": "narna.ai/v1alpha1",
		"kind":       "Constitution",
		"metadata": map[string]any{
			"name":       name + " Constitution",
			"entityKind": "Agent",
			"entityId":   id,
			"owner":      owner,
			"version":    version,
		},
		"spec": map[string]any{
			"identity": map[string]any{
				"id":      id,
				"owner":   owner,
				"version": version,
			},
			"capability": map[string]any{"supports": supports},
			"trust": map[string]any{
				"algorithm": "vap-trust-v0",
				"minScore":  minScore,
			},
		},
	}
}

func BadgeForLevel(level string) string {
	if b, ok := Badges[level]; ok {
		return b
	}
	return ""
}
