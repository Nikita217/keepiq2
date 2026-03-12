import { Card } from "../components/Card";
import { NoteItem, ReplyLaterItem, SavedItem } from "../types";

export function NotesPage({ notes, replyLater, saved }: { notes: NoteItem[]; replyLater: ReplyLaterItem[]; saved: SavedItem[] }) {
  return (
    <div className="pageGrid">
      <Card title="Notes & ideas" meta="цифровая память">
        <ul className="listClean">{notes.map((note) => <li key={note.id}>{note.title}</li>)}</ul>
      </Card>
      <Card title="Reply later" meta="черновики без автоотправки">
        <ul className="listClean">{replyLater.map((item) => <li key={item.id}>{item.title}</li>)}</ul>
      </Card>
      <Card title="Saved" meta="ссылки и материалы на потом">
        <ul className="listClean">{saved.map((item) => <li key={item.id}>{item.title}</li>)}</ul>
      </Card>
    </div>
  );
}
