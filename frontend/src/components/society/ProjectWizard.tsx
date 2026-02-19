/**
 * Project Creation Wizard - plan IDE Frontend Phase 1.1
 * Steps: template → description → tech stack → review → create
 */
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { runWorkflow } from "@/lib/society-api";

const TEMPLATES = [
  { id: "web_app", name: "Web Application", description: "Full-stack web app with React + FastAPI", icon: "🌐" },
  { id: "saas_app", name: "SaaS App", description: "Auth, billing, admin panel", icon: "📦" },
  { id: "api", name: "REST API", description: "Backend API service", icon: "🔌" },
  { id: "mobile_app", name: "Mobile App", description: "React Native + backend", icon: "📱" },
];

export interface ProjectConfig {
  template: string;
  projectName: string;
  description: string;
  techStack?: { frontend?: string; backend?: string; database?: string };
}

export function ProjectWizard({ onComplete }: { onComplete?: (config: ProjectConfig) => void }) {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [config, setConfig] = useState<Partial<ProjectConfig>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    const idea = [config.projectName, config.description].filter(Boolean).join(": ") || "A new application";
    setLoading(true);
    setError(null);
    try {
      const res = await runWorkflow(idea);
      onComplete?.(config as ProjectConfig);
      navigate(`/run?run_id=${res.run_id}`, { replace: true });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 text-white p-6">
      <div className="max-w-2xl mx-auto">
        <div className="flex gap-2 mb-8">
          {[1, 2, 3, 4].map((s) => (
            <div
              key={s}
              className={`h-2 flex-1 rounded-full ${s <= step ? "bg-blue-500" : "bg-gray-700"}`}
            />
          ))}
        </div>
        <p className="text-sm text-gray-400 mb-6">Step {step} of 4</p>

        {step === 1 && (
          <div>
            <h1 className="text-2xl font-bold mb-2">Choose a template</h1>
            <p className="text-gray-400 mb-6">Start with a template or build from scratch</p>
            <div className="grid grid-cols-2 gap-4">
              {TEMPLATES.map((t) => (
                <button
                  key={t.id}
                  type="button"
                  onClick={() => setConfig((c) => ({ ...c, template: t.id }))}
                  className={`p-6 rounded-xl border-2 text-left transition-all ${
                    config.template === t.id ? "border-blue-500 bg-blue-500/10" : "border-gray-700 hover:border-gray-600"
                  }`}
                >
                  <span className="text-3xl block mb-2">{t.icon}</span>
                  <h3 className="text-lg font-semibold">{t.name}</h3>
                  <p className="text-sm text-gray-400">{t.description}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {step === 2 && (
          <div>
            <h1 className="text-2xl font-bold mb-2">Describe your project</h1>
            <p className="text-gray-400 mb-6">What should your app do?</p>
            <div className="space-y-4">
              <div>
                <Label>Project name</Label>
                <Input
                  placeholder="my-awesome-app"
                  value={config.projectName ?? ""}
                  onChange={(e) => setConfig((c) => ({ ...c, projectName: e.target.value }))}
                  className="mt-2 bg-gray-800 border-gray-700"
                />
              </div>
              <div>
                <Label>Description</Label>
                <textarea
                  rows={6}
                  placeholder="e.g. A task management app with auth, categories, and due dates."
                  value={config.description ?? ""}
                  onChange={(e) => setConfig((c) => ({ ...c, description: e.target.value }))}
                  className="w-full mt-2 px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:border-blue-500 outline-none resize-none text-white placeholder:text-gray-500"
                />
              </div>
            </div>
          </div>
        )}

        {step === 3 && (
          <div>
            <h1 className="text-2xl font-bold mb-2">Tech stack</h1>
            <p className="text-gray-400 mb-6">We'll suggest a stack based on your project</p>
            <div className="p-6 bg-gray-800 rounded-lg border border-gray-700">
              <p className="text-gray-300">Recommended: React + TypeScript, FastAPI, PostgreSQL</p>
              <p className="text-sm text-gray-500 mt-2">Customize later in the IDE</p>
            </div>
          </div>
        )}

        {step === 4 && (
          <div>
            <h1 className="text-2xl font-bold mb-2">Review & create</h1>
            <p className="text-gray-400 mb-6">Start the agent workflow to generate your project</p>
            <div className="p-6 bg-gray-800 rounded-lg border border-gray-700 space-y-2">
              <p><strong>Template:</strong> {config.template ?? "web_app"}</p>
              <p><strong>Name:</strong> {config.projectName ?? "—"}</p>
              <p><strong>Description:</strong> {config.description ? `${config.description.slice(0, 100)}...` : "—"}</p>
            </div>
            {error && <p className="text-red-400 text-sm mt-4">{error}</p>}
          </div>
        )}

        <div className="flex justify-between mt-8">
          <Button
            type="button"
            variant="outline"
            onClick={() => setStep((s) => Math.max(1, s - 1))}
            disabled={step === 1}
            className="bg-gray-700 border-gray-600"
          >
            Back
          </Button>
          {step < 4 ? (
            <Button type="button" onClick={() => setStep((s) => s + 1)}>Next</Button>
          ) : (
            <Button type="button" onClick={handleCreate} disabled={loading}>
              {loading ? "Creating…" : "Create project"}
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
