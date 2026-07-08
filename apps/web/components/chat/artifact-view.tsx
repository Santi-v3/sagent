"use client";

import { ArrowsClockwise, Copy, File, FileCode, FileImage, FileText } from "@phosphor-icons/react";
import { SyntaxHighlight, detectLanguage } from "./syntax-highlight";

type Props = {
  path: string;
  content: string;
  sizeBytes: number;
};

function languageFromPath(path: string): string {
  const ext = path.split(".").pop()?.toLowerCase() || "";
  const map: Record<string, string> = {
    ts: "ts", tsx: "ts", js: "js", jsx: "js",
    py: "py", bash: "bash", sh: "bash", zsh: "bash",
    json: "json", yaml: "yaml", yml: "yaml",
    md: "markdown", html: "html", css: "css", scss: "css",
    rs: "rust", go: "go", java: "java", c: "c", cpp: "cpp",
  };
  return map[ext] || "";
}

function iconForPath(path: string) {
  const ext = path.split(".").pop()?.toLowerCase() || "";
  if (["png", "jpg", "jpeg", "gif", "svg", "webp", "ico"].includes(ext)) return <FileImage size={14} />;
  if (["ts", "tsx", "js", "jsx", "py", "rs", "go", "java", "c", "cpp", "css", "html"].includes(ext)) return <FileCode size={14} />;
  if (["md", "txt", "json", "yaml", "yml", "toml"].includes(ext)) return <FileText size={14} />;
  return <File size={14} />;
}

function fileName(path: string): string {
  return path.split("/").pop() || path;
}

export function ArtifactView({ path, content, sizeBytes }: Props) {
  const lang = languageFromPath(path);
  const detectedLang = lang || detectLanguage(content);

  return (
    <div className="artifact-view" data-path={path}>
      <div className="artifact-header">
        <div className="artifact-header-left">
          {iconForPath(path)}
          <span className="artifact-filename">{fileName(path)}</span>
          <span className="artifact-path">{path}</span>
        </div>
        <div className="artifact-header-right">
          <span className="artifact-lang">{detectedLang || "text"}</span>
          <span className="artifact-size">{sizeBytes > 1024 ? `${(sizeBytes / 1024).toFixed(1)} KB` : `${sizeBytes} B`}</span>
          <button
            type="button"
            className="artifact-copy-btn"
            onClick={() => navigator.clipboard.writeText(content)}
            title="Inhalt kopieren"
          >
            <Copy size={14} />
          </button>
        </div>
      </div>
      <div className="artifact-body">
        <SyntaxHighlight code={content} language={detectedLang} />
      </div>
    </div>
  );
}
