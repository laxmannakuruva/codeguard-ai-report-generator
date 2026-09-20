import { useState } from "react";

import WelcomeOverlay from "@/components/welcome-overlay";
import { useLiquidCursor } from "@/hooks/use-liquid-cursor";
import { useReveal } from "@/hooks/use-reveal";

import {
  AlertCircle,
  Check,
  List,
  FileArchive,
  FileImage,
  FileText,
  FileUp,
  LoaderCircle,
  Sparkles,
  Upload,
} from "lucide-react";

import { useQueryClient } from "@tanstack/react-query";

import {
  getGetReportInputsQueryKey,
  useAnalyzeProject,
  useGetReportInputs,
  useUploadProject,
  useUploadSampleReport,
  type ProjectProfile,
} from "@workspace/api-client-react";

import ReportStudio from "@/components/report-studio";

const formatBytes = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const API_BASE = "https://codeguard-ai-report-generator.onrender.com";

/* -------------------------------------------------------------- */
/* STAGE 1 â¬¢â¬ project upload                                        */
/* -------------------------------------------------------------- */

function ProjectStage({
  profile,
  onProjectAnalyzed,
}: {
  profile: ProjectProfile | null;
  onProjectAnalyzed: (projectId: string, profile: ProjectProfile) => void;
}) {
  const uploadProject = useUploadProject();
  const analyzeProject = useAnalyzeProject();
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);

  const startAnalysis = () => {
    if (!file) {
      setError("Choose a project ZIP before starting analysis.");
      return;
    }
    setError(null);
    uploadProject.mutate(
      { data: { file } },
      {
        onSuccess: (uploaded) => {
          analyzeProject.mutate(
            { projectId: uploaded.project_id },
            {
              onSuccess: (nextProfile) =>
                onProjectAnalyzed(uploaded.project_id, nextProfile),
              onError: () => setError("The project could not be analyzed."),
            },
          );
        },
        onError: () => setError("The project ZIP could not be uploaded."),
      },
    );
  };

  const isWorking = uploadProject.isPending || analyzeProject.isPending;
  const done = Boolean(profile);

  return (
    <section className="overflow-hidden rounded-2xl border border-[#dbe4dc] bg-white shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5">
      <header className="flex items-center justify-between border-b border-[#eef2eb] bg-[#f8fbf6] px-6 py-5">
        <div>
          <div className="mb-1 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-[#4d907e]">
            <Upload size={12} />
            Stage 1  Project
          </div>
          <h2 className="text-xl font-semibold tracking-tight text-[#0f2e2c]">
            Upload the project ZIP.
          </h2>
        </div>
        {done && (
          <span className="inline-flex items-center gap-1.5 rounded-full border border-[#cfe3d5] bg-[#edf8f0] px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-[#267967]">
            <Check size={11} /> Analyzed
          </span>
        )}
      </header>

      <div className="p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-stretch">
          <label className="flex min-h-[120px] flex-1 cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-[#b9cec0] bg-[#fcfdf9] px-4 text-center transition-colors hover:border-[#5da38d] hover:bg-[#f4faf3]">
            <input
              type="file"
              accept=".zip"
              className="hidden"
              onChange={(e) => {
                const next = e.target.files?.[0];
                if (!next || !next.name.toLowerCase().endsWith(".zip")) {
                  setError("Choose a ZIP project file.");
                  return;
                }
                setError(null);
                setFile(next);
              }}
            />
            <FileArchive size={26} className="mb-2 text-[#68a28f]" strokeWidth={1.5} />
            <span className="text-sm font-bold text-[#41605e]">
              {file ? file.name : "Choose your project ZIP"}
            </span>
            <span className="mt-1 text-xs text-[#9aa69e]">
              {file ? formatBytes(file.size) : "ZIP  Max 50 MB"}
            </span>
          </label>

          <button
            type="button"
            onClick={startAnalysis}
            disabled={isWorking || !file}
            className="inline-flex min-w-[170px] items-center justify-center gap-2 rounded-xl bg-[#216e65] px-5 py-3 text-sm font-bold text-white shadow-sm transition-all hover:bg-[#185b54] hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isWorking ? (
              <LoaderCircle size={15} className="animate-spin" />
            ) : (
              <Upload size={15} />
            )}
            {uploadProject.isPending
              ? "Uploadingâ¬¦"
              : analyzeProject.isPending
                ? "Analyzingâ¬¦"
                : "Analyze project"}
          </button>
        </div>

        {(error || uploadProject.isError || analyzeProject.isError) && (
          <div className="mt-4 flex items-start gap-2.5 rounded-lg border border-[#efc6ba] bg-[#fff4f0] p-3 text-xs text-[#934a39]">
            <AlertCircle className="mt-0.5 shrink-0" size={15} />
            <span>{error ?? "The project could not be processed."}</span>
          </div>
        )}

        {profile && (
          <div className="mt-5 rounded-xl border border-[#cfe3d5] bg-[#edf8f0] p-4">
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#d5eee0] text-[#267967]">
                <Check size={17} />
              </div>
              <div className="min-w-0">
                <p className="text-sm font-bold text-[#35655d]">
                  {profile.project_name}
                </p>
                <p className="mt-0.5 text-xs text-[#71847a]">
                  {profile.project_type}
                </p>
              </div>
            </div>
            {profile.readme_summary && (
              <p className="mt-3 line-clamp-3 text-xs leading-5 text-[#58766e]">
                {profile.readme_summary.replace(/^<{7}.*$|^={7}.*$|^>{7}.*$/gm, "").trim()}
              </p>
            )}
          </div>
        )}
      </div>
    </section>
  );
}

/* -------------------------------------------------------------- */
/* STAGE 2 â¬¢â¬ context (problem statement + images + sample)         */
/* -------------------------------------------------------------- */

function ContextStage({ projectId }: { projectId: string }) {
  const queryClient = useQueryClient();

  const reportInputs = useGetReportInputs(projectId, {
    query: {
      enabled: Boolean(projectId),
      queryKey: getGetReportInputsQueryKey(projectId),
    },
  });

  const uploadSample = useUploadSampleReport();

  const [problemText, setProblemText] = useState("");
  const [problemSaved, setProblemSaved] = useState(false);
  const [images, setImages] = useState<File[]>([]);
  const [imagesSaved, setImagesSaved] = useState(false);
  const [sampleFile, setSampleFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [chapters, setChapters] = useState<string[]>([]);
  const [chaptersSaved, setChaptersSaved] = useState(false);
  const [loadingChapters, setLoadingChapters] = useState(false);

  const invalidateInputs = () => {
    void queryClient.invalidateQueries({
      queryKey: getGetReportInputsQueryKey(projectId),
    });
  };

  const loadChapters = async () => {
    setLoadingChapters(true);
    try {
      const r = await fetch(`${API_BASE}/api/project/${projectId}/chapters/suggest`);
      if (r.ok) {
        const j = await r.json();
        setChapters(j.chapters || []);
      }
    } catch (e) { /* ignore */ }
    finally { setLoadingChapters(false); }
  };

  const saveChapters = async () => {
    setBusy("chapters");
    setError(null);
    try {
      const r = await fetch(`${API_BASE}/api/project/${projectId}/chapters`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ chapters }),
      });
      if (!r.ok) throw new Error(await r.text());
      setChaptersSaved(true);
    } catch (e) {
      setError("Chapters could not be saved.");
    } finally {
      setBusy(null);
    }
  };

  const saveProblem = async () => {
    setBusy("problem");
    setError(null);
    try {
      const r = await fetch(
        `${API_BASE}/api/project/${projectId}/problem-statement`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: problemText }),
        },
      );
      if (!r.ok) throw new Error(await r.text());
      setProblemSaved(true);
    } catch (e) {
      setError("Problem statement could not be saved.");
    } finally {
      setBusy(null);
    }
  };

  const saveImages = async () => {
    if (!images.length) return;
    setBusy("images");
    setError(null);
    try {
      const form = new FormData();
      images.forEach((f) => form.append("files", f));
      const r = await fetch(`${API_BASE}/api/project/${projectId}/images`, {
        method: "POST",
        body: form,
      });
      if (!r.ok) throw new Error(await r.text());
      setImagesSaved(true);
    } catch (e) {
      setError("Images could not be uploaded.");
    } finally {
      setBusy(null);
    }
  };

  const selectSampleFile = (next: File | undefined) => {
    if (!next) return;
    const allowed = [".pdf", ".doc", ".docx", ".txt", ".md"];
    const ok = allowed.some((ext) => next.name.toLowerCase().endsWith(ext));
    if (!ok) {
      setError("Use a PDF, DOC, DOCX, TXT, or Markdown sample.");
      return;
    }
    if (next.size > 10 * 1024 * 1024) {
      setError("Sample reports must be smaller than 10 MB.");
      return;
    }
    setError(null);
    setSampleFile(next);
  };

  const uploadSampleFile = () => {
    if (!sampleFile) return;
    setBusy("sample");
    setError(null);
    uploadSample.mutate(
      { projectId, data: { file: sampleFile } },
      {
        onSuccess: () => {
          setSampleFile(null);
          invalidateInputs();
          setTimeout(loadChapters, 500);
        },
        onError: () => setError("The sample report could not be processed."),
        onSettled: () => setBusy(null),
      },
    );
  };

  const sampleReport = reportInputs.data?.sample_report;
  const sampleDone = Boolean(sampleReport?.uploaded);

  return (
    <section className="mt-6 overflow-hidden rounded-2xl border border-[#dbe4dc] bg-white shadow-sm transition-all duration-200 hover:shadow-md">
      <header className="border-b border-[#eef2eb] bg-[#f8fbf6] px-6 py-5">
        <div className="mb-1 flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-[#4d907e]">
          <Sparkles size={12} />
          Stage 2  Context
        </div>
        <h2 className="text-xl font-semibold tracking-tight text-[#0f2e2c]">
          Add the details that make the report yours.
        </h2>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-[#5a6b62]">
          Problem statement and project images are used verbatim. The sample
          report sets the structure only.
        </p>
      </header>

      <div className="grid gap-6 p-6 lg:grid-cols-2">
        {/* PROBLEM STATEMENT */}
        <div className="rounded-xl border border-[#e5ebe0] bg-[#fcfdf9] p-4 transition-colors hover:border-[#c9d9c5]">
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold text-[#41605e]">
              <FileText size={14} className="text-[#4ca189]" />
              Problem statement
            </div>
            {problemSaved && (
              <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#267967]">
                <Check size={11} /> Saved
              </span>
            )}
          </div>
          <p className="mb-3 text-xs leading-5 text-[#87918a]">
            Type or paste the problem statement. It becomes a chapter in the
            report.
          </p>
          <textarea
            value={problemText}
            onChange={(e) => {
              setProblemText(e.target.value);
              setProblemSaved(false);
            }}
            rows={6}
            placeholder="Describe the problem this project addresses..."
            className="w-full resize-y rounded-lg border border-[#dde4da] bg-white p-3 text-sm leading-6 text-[#3f5b57] outline-none transition-colors focus:border-[#8dc0ae]"
          />
          <button
            type="button"
            onClick={saveProblem}
            disabled={busy === "problem" || !problemText.trim()}
            className="mt-3 inline-flex items-center gap-2 rounded-lg bg-[#216e65] px-4 py-2 text-xs font-bold text-white transition-all hover:bg-[#185b54] hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy === "problem" && (
              <LoaderCircle size={13} className="animate-spin" />
            )}
            Save problem statement
          </button>
        </div>

        {/* PROJECT IMAGES */}
        <div className="rounded-xl border border-[#e5ebe0] bg-[#fcfdf9] p-4 transition-colors hover:border-[#c9d9c5]">
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold text-[#41605e]">
              <FileImage size={14} className="text-[#4ca189]" />
              Project images
            </div>
            {imagesSaved && (
              <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#267967]">
                <Check size={11} /> Uploaded
              </span>
            )}
          </div>
          <p className="mb-3 text-xs leading-5 text-[#87918a]">
            Screenshots, diagrams, or photos for the report. Multiple files.
          </p>
          <label className="flex min-h-[140px] cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-[#b9cec0] bg-white px-4 text-center transition-colors hover:border-[#5da38d] hover:bg-[#f4faf3]">
            <input
              type="file"
              accept="image/*"
              multiple
              className="hidden"
              onChange={(e) => {
                const files = Array.from(e.target.files ?? []);
                if (files.length) {
                  setImages((prev) => [...prev, ...files]);
                  setImagesSaved(false);
                }
                e.target.value = "";
              }}
            />
            <FileImage size={24} className="mb-2 text-[#68a28f]" strokeWidth={1.5} />
            <span className="text-sm font-bold text-[#41605e]">
              {images.length
                ? `${images.length} image${images.length > 1 ? "s" : ""} selected`
                : "Choose images"}
            </span>
            <span className="mt-1 text-xs text-[#9aa69e]">
              PNG, JPG, GIF, WEBP  Max 8 MB each
            </span>
          </label>
          {images.length > 0 && (
            <ul className="mt-3 space-y-1">
              {images.map((f, i) => (
                <li
                  key={`${f.name}-${i}`}
                  className="flex items-center justify-between gap-2 rounded-md border border-[#e5ebe0] bg-white px-2 py-1 text-xs text-[#41605e]"
                >
                  <span className="truncate">
                    {i + 1}. {f.name}{" "}
                    <span className="text-[#9aa69e]">({formatBytes(f.size)})</span>
                  </span>
                  <button
                    type="button"
                    onClick={() => {
                      setImages((prev) => prev.filter((_, idx) => idx !== i));
                      setImagesSaved(false);
                    }}
                    className="rounded px-1 text-[#934a39] hover:bg-[#fff4f0]"
                    aria-label={`Remove ${f.name}`}
                  >
                    â¬¢
                  </button>
                </li>
              ))}
              <li className="pt-1">
                <button
                  type="button"
                  onClick={() => {
                    setImages([]);
                    setImagesSaved(false);
                  }}
                  className="text-[11px] font-bold text-[#934a39] hover:underline"
                >
                  Clear all
                </button>
              </li>
            </ul>
          )}
          <button
            type="button"
            onClick={saveImages}
            disabled={busy === "images" || !images.length}
            className="mt-3 inline-flex items-center gap-2 rounded-lg bg-[#216e65] px-4 py-2 text-xs font-bold text-white transition-all hover:bg-[#185b54] hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy === "images" && (
              <LoaderCircle size={13} className="animate-spin" />
            )}
            Upload images
          </button>
        </div>
      </div>

      {/* CHAPTERS */}
      {(chapters.length > 0 || loadingChapters) && (
        <div className="border-t border-[#eef2eb] p-6">
          <div className="mb-2 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold text-[#41605e]">
              <List size={14} className="text-[#4ca189]" />
              Report chapters
            </div>
            {chaptersSaved && (
              <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#267967]">
                Saved
              </span>
            )}
          </div>
          <p className="mb-3 text-xs leading-5 text-[#87918a]">
            We detected these from your sample. Edit, remove, or add freely â€” the report uses this exact list.
          </p>
          {loadingChapters ? (
            <div className="flex items-center gap-2 text-xs text-[#41605e]">
              <LoaderCircle size={12} className="animate-spin" /> Detecting chapters...
            </div>
          ) : (
            <div className="space-y-2">
              {chapters.map((c, i) => (
                <div key={i} className="flex items-center gap-2">
                  <input
                    value={c}
                    onChange={(e) => {
                      const next = [...chapters];
                      next[i] = e.target.value;
                      setChapters(next);
                      setChaptersSaved(false);
                    }}
                    className="flex-1 rounded-md border border-[#dde4da] bg-white px-2 py-1 text-xs text-[#3f5b57] outline-none focus:border-[#8dc0ae]"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      setChapters(chapters.filter((_, idx) => idx !== i));
                      setChaptersSaved(false);
                    }}
                    className="rounded px-2 py-1 text-xs font-bold text-[#934a39] hover:bg-[#fff4f0]"
                  >
                    âœ•
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={() => { setChapters([...chapters, ""]); setChaptersSaved(false); }}
                className="text-[11px] font-bold text-[#216e65] hover:underline"
              >
                + Add chapter
              </button>
              <button
                type="button"
                onClick={saveChapters}
                disabled={busy === "chapters" || chapters.filter((c) => c.trim()).length === 0}
                className="ml-3 inline-flex items-center gap-2 rounded-lg bg-[#216e65] px-3 py-1.5 text-[11px] font-bold text-white disabled:opacity-50"
              >
                {busy === "chapters" && <LoaderCircle size={11} className="animate-spin" />}
                Save chapters
              </button>
            </div>
          )}
        </div>
      )}

      {/* SAMPLE REPORT */}
      <div className="border-t border-[#eef2eb] p-6">
        <div className="mb-2 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold text-[#41605e]">
            <FileUp size={14} className="text-[#4ca189]" />
            Sample report (structure only)
          </div>
          {sampleDone && (
            <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#267967]">
              <Check size={11} /> Processed
            </span>
          )}
        </div>
        <p className="mb-3 text-xs leading-5 text-[#87918a]">
          Upload the report format from your college. Its chapters and order
          become your report's structure.
        </p>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-stretch">
          <label className="flex min-h-[90px] flex-1 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-[#b9cec0] bg-[#fcfdf9] px-4 text-center transition-colors hover:border-[#5da38d] hover:bg-[#f4faf3]">
            <input
              type="file"
              accept=".pdf,.doc,.docx,.txt,.md"
              className="hidden"
              onChange={(e) => selectSampleFile(e.target.files?.[0])}
            />
            <FileText size={22} className="mb-2 text-[#68a28f]" strokeWidth={1.5} />
            <span className="text-sm font-bold text-[#41605e]">
              {sampleFile ? sampleFile.name : "Choose sample report"}
            </span>
            <span className="mt-1 text-xs text-[#9aa69e]">
              {sampleFile ? formatBytes(sampleFile.size) : "PDF, DOC, DOCX, TXT, MD"}
            </span>
          </label>
          <button
            type="button"
            onClick={uploadSampleFile}
            disabled={busy === "sample" || !sampleFile}
            className="inline-flex min-w-[170px] items-center justify-center gap-2 rounded-xl bg-[#216e65] px-5 py-3 text-sm font-bold text-white transition-all hover:bg-[#185b54] hover:scale-[1.02] active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy === "sample" ? (
              <LoaderCircle size={15} className="animate-spin" />
            ) : (
              <FileUp size={15} />
            )}
            Read sample report
          </button>
        </div>
      </div>

      {error && (
        <div className="mx-6 mb-6 flex items-start gap-2.5 rounded-lg border border-[#efc6ba] bg-[#fff4f0] p-3 text-xs text-[#934a39]">
          <AlertCircle className="mt-0.5 shrink-0" size={15} />
          <span>{error}</span>
        </div>
      )}
    </section>
  );
}

/* -------------------------------------------------------------- */
/* HOME                                                            */
/* -------------------------------------------------------------- */

export default function Home() {
  const [projectId, setProjectId] = useState<string | null>(null);
  const [profile, setProfile] = useState<ProjectProfile | null>(null);

  useLiquidCursor();

  return (
    <div className="min-h-screen bg-[#f6f9f4]">
      <WelcomeOverlay />
      <main className="mx-auto max-w-5xl px-4 py-16 sm:px-6 lg:px-8">
        <header className="mb-12 text-center">
          <div className="mb-3 text-[11px] font-bold uppercase tracking-[0.24em] text-[#4d907e]">
            Welcome to
          </div>
          <h1 className="text-4xl font-semibold tracking-tight text-[#0f2e2c] sm:text-5xl">
            CodeGuard AI
          </h1>
          <p className="mx-auto mt-3 max-w-xl text-base text-[#5a6b62]">
            AI-powered project report generator
          </p>
        </header>

        <ProjectStage
          profile={profile}
          onProjectAnalyzed={(id, nextProfile) => {
            setProjectId(id);
            setProfile(nextProfile);
          }}
        />

        {projectId && (
          <ContextStage projectId={projectId} />
        )}

        {projectId && (
          <div className="mt-6">
            <ReportStudio projectId={projectId} />
          </div>
        )}
      </main>
    </div>
  );
}