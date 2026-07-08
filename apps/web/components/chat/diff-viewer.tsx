"use client";

import { useMemo } from "react";

type DiffLine = {
  type: "add" | "del" | "ctx";
  content: string;
  lineOld: number | null;
  lineNew: number | null;
};

type Props = {
  diff: string;
  filename?: string;
};

export function DiffViewer({ diff, filename }: Props) {
  const lines = useMemo(() => {
    const result: DiffLine[] = [];
    let oldLine = 0;
    let newLine = 0;
    const raw = diff.replace(/\r\n/g, "\n").split("\n");
    for (const line of raw) {
      if (line.startsWith("@@")) {
        const m = line.match(/@@ -(\d+),?\d* \+(\d+),?\d* @@/);
        if (m) { oldLine = parseInt(m[1]) - 1; newLine = parseInt(m[2]) - 1; }
        result.push({ type: "ctx", content: line, lineOld: null, lineNew: null });
      } else if (line.startsWith("+")) {
        newLine++;
        result.push({ type: "add", content: line, lineOld: null, lineNew: newLine });
      } else if (line.startsWith("-")) {
        oldLine++;
        result.push({ type: "del", content: line, lineOld: oldLine, lineNew: null });
      } else {
        oldLine++;
        newLine++;
        result.push({ type: "ctx", content: line, lineOld: oldLine, lineNew: newLine });
      }
    }
    return result;
  }, [diff]);

  return (
    <div className="diff-viewer">
      {filename && <div className="diff-filename">{filename}</div>}
      <pre className="diff-content">
        {lines.map((l, i) => (
          <span key={i} className={`diff-line diff-${l.type}`}>
            <span className="diff-lineno">
              {l.type === "add" ? "" : l.lineOld ?? ""}
            </span>
            <span className="diff-lineno">
              {l.type === "del" ? "" : l.lineNew ?? ""}
            </span>
            <span className="diff-text">{l.content}</span>
          </span>
        ))}
      </pre>
    </div>
  );
}
