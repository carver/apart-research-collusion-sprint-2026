// Reading the run logs the experiments write: logs/<experiment>/<start time, UTC>.jsonl in the
// project root, one JSON record per line.

import fs from "node:fs";
import path from "node:path";

export const LOGS_DIR = process.env.LOGS_DIR ?? path.resolve(process.cwd(), "..", "logs");

export type LogRecord = { type?: string; [field: string]: unknown };

// One line of a log, with its record parsed. A line that isn't valid JSON (say, one still being
// written) has record null.
export type LogLine = { line: string; record: LogRecord | null };

export function listExperiments(): string[] {
  if (!fs.existsSync(LOGS_DIR)) return [];
  return fs
    .readdirSync(LOGS_DIR, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => entry.name)
    .sort();
}

// Newest first: the file names are UTC start times, so they sort by name.
export function listLogs(experiment: string): string[] {
  return fs
    .readdirSync(path.join(LOGS_DIR, experiment))
    .filter((name) => name.endsWith(".jsonl"))
    .sort()
    .reverse();
}

export function readLog(experiment: string, log: string): LogLine[] {
  const text = fs.readFileSync(path.join(LOGS_DIR, experiment, log), "utf8");
  return text
    .split("\n")
    .filter((line) => line.trim())
    .map((line) => {
      try {
        return { line, record: JSON.parse(line) as LogRecord };
      } catch {
        return { line, record: null };
      }
    });
}
