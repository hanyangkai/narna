package narna_test

import (
	"testing"

	narna "github.com/hanyangkai/narna/sdks/go"
)

func TestCompileManifest(t *testing.T) {
	m := narna.Manifest{}
	m.APIVersion = "narna.ai/v1alpha1"
	m.Kind = "Manifest"
	m.Identity.ID = "research-agent"
	m.Capabilities = []string{"web.search"}
	m.Trust.MinimumScore = 0.9
	c := narna.CompileManifest(m)
	meta := c["metadata"].(map[string]any)
	if meta["entityId"] != "agent_research_agent" {
		t.Fatalf("entityId=%v", meta["entityId"])
	}
	if narna.BadgeForLevel("L3") != "Enterprise Ready" {
		t.Fatal("badge")
	}
}
