// The whole explorer: experiments and their logs on the left, the chosen log on the right. The
// choice is in the URL (?experiment=...&log=...), and everything is read from disk on each request,
// so reloading shows lines added since.

import Link from "next/link";

import { type LogRecord, listExperiments, listLogs, readLog } from "../lib/logs";

const LONG = 500; // characters: longer lines are collapsed to one line, and expand when clicked

type SearchParams = Record<string, string | string[] | undefined>;

export default async function Page({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const params = await searchParams;
  // Only names that are actually in the logs folder are used, so a URL can't reach other files.
  const experiments = listExperiments();
  const experiment = oneOf(params.experiment, experiments);
  const logs = experiment ? listLogs(experiment) : [];
  const log = oneOf(params.log, logs);

  return (
    <div className="explorer">
      <nav className="sidebar">
        <h1>Logs</h1>
        {experiments.length === 0 && <p className="hint">No experiments in the logs folder yet.</p>}
        {experiments.map((name) => (
          <div key={name}>
            <Link
              href={{ pathname: "/", query: { experiment: name } }}
              className={name === experiment ? "experiment open" : "experiment"}
            >
              {name}
            </Link>
            {name === experiment && (
              <ul>
                {logs.map((file) => (
                  <li key={file}>
                    <Link
                      href={{ pathname: "/", query: { experiment: name, log: file } }}
                      className={file === log ? "selected" : undefined}
                      title={file}
                    >
                      {startTime(file)}
                    </Link>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </nav>
      <main>
        {experiment && log ? (
          <Log experiment={experiment} log={log} />
        ) : (
          <p className="hint">{experiment ? "Choose a log." : "Choose an experiment."}</p>
        )}
      </main>
    </div>
  );
}

function Log({ experiment, log }: { experiment: string; log: string }) {
  const lines = readLog(experiment, log);
  return (
    <>
      <h2>
        {experiment} / {log} <span className="count">{lines.length} lines</span>
      </h2>
      <ol className="lines">
        {lines.map(({ line, record }, i) => (
          <li key={i}>
            {line.length > LONG ? (
              <details>
                <summary>
                  <Tag record={record} />
                  <code className="preview">{line.slice(0, LONG)}</code>
                  <span className="size">{(line.length / 1024).toFixed(1)} KB</span>
                </summary>
                <pre>{record ? JSON.stringify(record, null, 2) : line}</pre>
              </details>
            ) : (
              <div className="short">
                <Tag record={record} />
                <code>{line}</code>
              </div>
            )}
          </li>
        ))}
      </ol>
    </>
  );
}

function Tag({ record }: { record: LogRecord | null }) {
  const type = record?.type ?? "unparsed";
  return <span className={`tag tag-${type}`}>{type}</span>;
}

// The value if it is one of the options, else null.
function oneOf(value: string | string[] | undefined, options: string[]): string | null {
  return typeof value === "string" && options.includes(value) ? value : null;
}

// "2026-10-20T06-15-59Z.jsonl" -> "2026-10-20 06:15:59"
function startTime(file: string): string {
  const match = file.match(/^(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2})Z\.jsonl$/);
  return match ? `${match[1]} ${match[2]}:${match[3]}:${match[4]}` : file;
}
