import { useEffect, useState } from "react";

import { DetailDraft, DetailEntity } from "../types";
import { formatLongDateTime, mergeDateAndTime, toDateInputValue, toTimeInputValue } from "../utils/date";
import { availableTypeOptions, canConvert, getTypeLabel } from "../utils/models";

function buildDraft(entity: DetailEntity): DetailDraft {
  if (entity.kind === "incoming") {
    return {
      title: entity.item.summary ?? "",
      description: entity.item.assistant_response ?? entity.item.raw_text ?? entity.item.transcript_text ?? entity.item.ocr_text ?? "",
      date: "",
      time: "",
      type: entity.item.proposed_type ?? "note",
      kind: "note",
      sourceUrl: entity.item.source_url ?? "",
      status: entity.item.parse_status,
      listItems: [],
    };
  }

  if (entity.kind === "task") {
    return {
      title: entity.item.title,
      description: entity.item.description ?? "",
      date: toDateInputValue(entity.item.due_at ?? entity.item.scheduled_for),
      time: toTimeInputValue(entity.item.due_at ?? entity.item.scheduled_for),
      type: entity.kind,
      kind: entity.item.priority,
      sourceUrl: "",
      status: entity.item.status,
      listItems: [],
    };
  }

  if (entity.kind === "event") {
    return {
      title: entity.item.title,
      description: entity.item.description ?? "",
      date: toDateInputValue(entity.item.starts_at),
      time: toTimeInputValue(entity.item.starts_at),
      type: entity.kind,
      kind: entity.item.place_name ?? "event",
      sourceUrl: "",
      status: entity.item.status,
      listItems: [],
    };
  }

  if (entity.kind === "reminder") {
    return {
      title: entity.item.title,
      description: "",
      date: toDateInputValue(entity.item.remind_at ?? entity.item.remind_on),
      time: toTimeInputValue(entity.item.remind_at),
      type: entity.kind,
      kind: "reminder",
      sourceUrl: "",
      status: entity.item.status,
      listItems: [],
    };
  }

  if (entity.kind === "reply_later") {
    return {
      title: entity.item.title,
      description: entity.item.conversation_summary ?? "",
      date: toDateInputValue(entity.item.reply_due_at),
      time: toTimeInputValue(entity.item.reply_due_at),
      type: entity.kind,
      kind: "reply_later",
      sourceUrl: "",
      status: entity.item.status,
      listItems: [],
    };
  }

  if (entity.kind === "note") {
    return {
      title: entity.item.title,
      description: entity.item.body ?? "",
      date: "",
      time: "",
      type: entity.kind,
      kind: entity.item.kind,
      sourceUrl: "",
      status: entity.item.status,
      listItems: [],
    };
  }

  if (entity.kind === "saved") {
    return {
      title: entity.item.title,
      description: entity.item.summary ?? "",
      date: "",
      time: "",
      type: entity.kind,
      kind: "saved",
      sourceUrl: entity.item.source_url ?? "",
      status: "saved",
      listItems: [],
    };
  }

  return {
    title: entity.item.title,
    description: entity.item.description ?? "",
    date: "",
    time: "",
    type: entity.kind,
    kind: entity.item.kind,
    sourceUrl: "",
    status: "active",
    listItems: entity.item.items.map((item) => ({ id: item.id, text: item.text, is_done: item.is_done })),
  };
}

function isTimedType(type: string): boolean {
  return ["task", "reminder", "event", "reply_later"].includes(type);
}

function getIncomingPreview(entity: DetailEntity | null): string | null {
  if (!entity || entity.kind !== "incoming") {
    return null;
  }
  return entity.item.raw_text ?? entity.item.transcript_text ?? entity.item.ocr_text ?? entity.item.source_url ?? null;
}

export function DetailSheet({
  entity,
  busy,
  onClose,
  onSave,
  onDelete,
  onComplete,
}: {
  entity: DetailEntity | null;
  busy: boolean;
  onClose: () => void;
  onSave: (entity: DetailEntity, draft: DetailDraft) => Promise<void> | void;
  onDelete: (entity: DetailEntity) => Promise<void> | void;
  onComplete: (entity: DetailEntity) => Promise<void> | void;
}) {
  const [draft, setDraft] = useState<DetailDraft | null>(null);

  useEffect(() => {
    setDraft(entity ? buildDraft(entity) : null);
  }, [entity]);

  useEffect(() => {
    if (!entity) {
      return undefined;
    }

    const previousBodyOverflow = document.body.style.overflow;
    const previousHtmlOverflow = document.documentElement.style.overflow;
    const previousBodyPosition = document.body.style.position;
    const previousBodyTop = document.body.style.top;
    const previousBodyWidth = document.body.style.width;
    const scrollY = window.scrollY;

    document.body.style.overflow = "hidden";
    document.documentElement.style.overflow = "hidden";
    document.body.style.position = "fixed";
    document.body.style.top = `-${scrollY}px`;
    document.body.style.width = "100%";

    return () => {
      document.body.style.overflow = previousBodyOverflow;
      document.documentElement.style.overflow = previousHtmlOverflow;
      document.body.style.position = previousBodyPosition;
      document.body.style.top = previousBodyTop;
      document.body.style.width = previousBodyWidth;
      window.scrollTo(0, scrollY);
    };
  }, [entity]);

  if (!entity || !draft) {
    return null;
  }

  const options = availableTypeOptions(entity.kind);
  const sourceHint = entity.kind === "incoming"
    ? `\u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a: ${entity.item.incoming_type}`
    : entity.kind === "saved"
      ? entity.item.source_url
      : "source_incoming_item_id" in entity.item && entity.item.source_incoming_item_id
        ? `\u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a #${entity.item.source_incoming_item_id}`
        : null;
  const originalPreview = getIncomingPreview(entity);
  const hasTimeControls = isTimedType(draft.type) || draft.date.length > 0;
  const scheduledAt = mergeDateAndTime(draft.date, draft.time);
  const canComplete = entity.kind !== "incoming" && ["task", "reminder", "event", "reply_later"].includes(entity.kind) && draft.status !== "done";

  return (
    <div className="sheetOverlay" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="sheetCard" onClick={(event) => event.stopPropagation()}>
        <div className="sheetHeader">
          <div>
            <p className="screenEyebrow">{getTypeLabel(entity.kind)}</p>
            <h2>{entity.kind === "incoming" ? "\u0420\u0430\u0437\u043e\u0431\u0440\u0430\u0442\u044c \u0432\u0445\u043e\u0434\u044f\u0449\u0435\u0435" : "\u041a\u0430\u0440\u0442\u043e\u0447\u043a\u0430 \u043e\u0431\u044a\u0435\u043a\u0442\u0430"}</h2>
            {scheduledAt ? <p className="sheetSubtle">{formatLongDateTime(scheduledAt)}</p> : null}
          </div>
          <button type="button" className="ghost iconButton" onClick={onClose} aria-label="\u0417\u0430\u043a\u0440\u044b\u0442\u044c">{"\u00D7"}</button>
        </div>

        <div className="sheetScrollArea">
          {canConvert(entity.kind) ? (
            <div className="segmentWrap compact">
              {options.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={draft.type === option.value ? "segment active" : "segment"}
                  onClick={() => setDraft((current) => (current ? { ...current, type: option.value } : current))}
                >
                  {option.label}
                </button>
              ))}
            </div>
          ) : null}

          <label className="fieldBlock">
            <span>\u041d\u0430\u0437\u0432\u0430\u043d\u0438\u0435</span>
            <input value={draft.title} onChange={(event) => setDraft((current) => (current ? { ...current, title: event.target.value } : current))} />
          </label>

          <label className="fieldBlock">
            <span>{entity.kind === "list" ? "\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435 \u0441\u043f\u0438\u0441\u043a\u0430" : "\u041e\u043f\u0438\u0441\u0430\u043d\u0438\u0435"}</span>
            <textarea value={draft.description} onChange={(event) => setDraft((current) => (current ? { ...current, description: event.target.value } : current))} rows={4} />
          </label>

          {entity.kind === "note" || entity.kind === "list" ? (
            <label className="fieldBlock">
              <span>{entity.kind === "note" ? "\u0422\u0438\u043f \u0437\u0430\u043c\u0435\u0442\u043a\u0438" : "\u041a\u0430\u0442\u0435\u0433\u043e\u0440\u0438\u044f \u0441\u043f\u0438\u0441\u043a\u0430"}</span>
              <input value={draft.kind} onChange={(event) => setDraft((current) => (current ? { ...current, kind: event.target.value } : current))} />
            </label>
          ) : null}

          {entity.kind === "saved" ? (
            <label className="fieldBlock">
              <span>\u0421\u0441\u044b\u043b\u043a\u0430</span>
              <input value={draft.sourceUrl} onChange={(event) => setDraft((current) => (current ? { ...current, sourceUrl: event.target.value } : current))} />
            </label>
          ) : null}

          {hasTimeControls ? (
            <div className="sheetDateRow">
              <label className="fieldBlock compactField">
                <span>\u0414\u0430\u0442\u0430</span>
                <input type="date" value={draft.date} onChange={(event) => setDraft((current) => (current ? { ...current, date: event.target.value } : current))} />
              </label>
              <label className="fieldBlock compactField">
                <span>\u0412\u0440\u0435\u043c\u044f</span>
                <input type="time" value={draft.time} onChange={(event) => setDraft((current) => (current ? { ...current, time: event.target.value } : current))} />
              </label>
              <button
                type="button"
                className="ghost clearDateButton"
                onClick={() => setDraft((current) => (current ? { ...current, date: "", time: "" } : current))}
              >
                \u0423\u0431\u0440\u0430\u0442\u044c \u0434\u0430\u0442\u0443
              </button>
            </div>
          ) : null}

          {entity.kind === "list" ? (
            <div className="fieldBlock">
              <span>\u041f\u0443\u043d\u043a\u0442\u044b \u0441\u043f\u0438\u0441\u043a\u0430</span>
              <div className="listEditor">
                {draft.listItems.map((item, index) => (
                  <div key={`${item.id ?? index}`} className="listEditorRow">
                    <input
                      type="checkbox"
                      checked={item.is_done}
                      onChange={(event) => setDraft((current) => (current ? {
                        ...current,
                        listItems: current.listItems.map((entry, entryIndex) => (entryIndex === index ? { ...entry, is_done: event.target.checked } : entry)),
                      } : current))}
                    />
                    <input
                      value={item.text}
                      onChange={(event) => setDraft((current) => (current ? {
                        ...current,
                        listItems: current.listItems.map((entry, entryIndex) => (entryIndex === index ? { ...entry, text: event.target.value } : entry)),
                      } : current))}
                    />
                    <button
                      type="button"
                      className="ghost iconButton"
                      onClick={() => setDraft((current) => (current ? {
                        ...current,
                        listItems: current.listItems.filter((_, entryIndex) => entryIndex !== index),
                      } : current))}
                      aria-label="\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u043f\u0443\u043d\u043a\u0442"
                    >
                      {"-"}
                    </button>
                  </div>
                ))}
                <button
                  type="button"
                  className="ghost"
                  onClick={() => setDraft((current) => (current ? {
                    ...current,
                    listItems: [...current.listItems, { text: "", is_done: false }],
                  } : current))}
                >
                  \u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u043f\u0443\u043d\u043a\u0442
                </button>
              </div>
            </div>
          ) : null}

          {sourceHint ? <div className="sheetInfo">{sourceHint}</div> : null}

          {originalPreview ? (
            <div className="sheetInfo">
              <strong className="sheetInfoTitle">\u041e\u0440\u0438\u0433\u0438\u043d\u0430\u043b</strong>
              <div>{originalPreview}</div>
            </div>
          ) : null}
        </div>

        <div className="sheetFooter">
          {entity.kind !== "incoming" ? (
            <button type="button" className="ghost danger" onClick={() => onDelete(entity)} disabled={busy}>
              \u0423\u0434\u0430\u043b\u0438\u0442\u044c
            </button>
          ) : <span className="sheetFooterSpacer" />}

          <div className="sheetFooterActions">
            {canComplete ? (
              <button type="button" className="ghost" onClick={() => onComplete(entity)} disabled={busy}>
                \u041e\u0442\u043c\u0435\u0442\u0438\u0442\u044c \u0432\u044b\u043f\u043e\u043b\u043d\u0435\u043d\u043d\u044b\u043c
              </button>
            ) : null}
            <button type="button" onClick={() => onSave(entity, draft)} disabled={busy || !draft.title.trim()}>
              {busy ? "\u0421\u043e\u0445\u0440\u0430\u043d\u044f\u044e..." : entity.kind === "incoming" ? "\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u044c" : "\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}