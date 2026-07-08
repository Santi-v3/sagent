"use client";

import { useMemo } from "react";

const KEYWORDS: Record<string, string[]> = {
  ts: ["import", "export", "from", "const", "let", "var", "function", "return", "if", "else", "for", "while", "class", "interface", "type", "extends", "implements", "async", "await", "new", "this", "typeof", "keyof", "in"],
  js: ["import", "export", "from", "const", "let", "var", "function", "return", "if", "else", "for", "while", "class", "async", "await", "new", "this", "typeof"],
  py: ["def", "return", "if", "elif", "else", "for", "while", "import", "from", "class", "async", "await", "with", "as", "try", "except", "finally", "raise", "pass", "None", "True", "False", "in", "not", "and", "or", "is", "lambda", "yield"],
  bash: ["if", "then", "else", "fi", "for", "while", "do", "done", "function", "return", "export", "local", "source", "exit"],
  json: ["true", "false", "null"],
};

function highlightLine(line: string, lang: string): React.ReactNode[] {
  const kw = KEYWORDS[lang] || [];
  const parts: React.ReactNode[] = [];
  const regex = /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|\b\d+\.?\d*\b|#.*$|\/\/.*$|\b[a-zA-Z_]\w*\b|[{}[\]();,:]|\S)/g;
  let match: RegExpExecArray | null;
  let lastIndex = 0;
  while ((match = regex.exec(line)) !== null) {
    const token = match[1];
    if (lastIndex < match.index) {
      parts.push(line.slice(lastIndex, match.index));
    }
    lastIndex = regex.lastIndex;
    if (token.startsWith('"') || token.startsWith("'")) {
      parts.push(<span key={match.index} className="hl-string">{token}</span>);
    } else if (/^\d/.test(token)) {
      parts.push(<span key={match.index} className="hl-number">{token}</span>);
    } else if (token.startsWith("#") || token.startsWith("//")) {
      parts.push(<span key={match.index} className="hl-comment">{token}</span>);
    } else if (kw.includes(token)) {
      parts.push(<span key={match.index} className="hl-keyword">{token}</span>);
    } else if (/^[{}[\]();,:]$/.test(token)) {
      parts.push(<span key={match.index} className="hl-punct">{token}</span>);
    } else {
      parts.push(token);
    }
  }
  if (lastIndex < line.length) {
    parts.push(line.slice(lastIndex));
  }
  return parts;
}

export function detectLanguage(code: string): string {
  const firstLine = code.split("\n")[0].toLowerCase();
  if (firstLine.startsWith("import ") || firstLine.startsWith("from ")) return isSvelteLike(code) ? "py" : "ts";
  if (/^(const|let|var|function|export|import|interface)\b/.test(firstLine)) return "ts";
  if (/^(def |class |import |from |print\b)/.test(firstLine)) return "py";
  if (firstLine.startsWith("#!") || /^(if |for |while |echo |curl |git )/.test(firstLine)) return "bash";
  if (firstLine.startsWith("{") || firstLine.startsWith("[")) return "json";
  return "ts";
}

function isSvelteLike(code: string): boolean {
  return /\bawait\b/.test(code) && /\bdef\b/.test(code);
}

type Props = {
  code: string;
  language?: string;
};

export function SyntaxHighlight({ code, language }: Props) {
  const lang = language || detectLanguage(code);
  const lines = useMemo(() => code.replace(/\r\n/g, "\n").split("\n"), [code]);
  return (
    <code className={`syntax-hl lang-${lang}`}>
      {lines.map((line, i) => (
        <span key={i} className="hl-line">
          {highlightLine(line, lang)}
          {i < lines.length - 1 ? "\n" : null}
        </span>
      ))}
    </code>
  );
}
