from db import crud
from db.models import (
    ChatSession,
    KnowledgeTag,
    Note,
    NoteTagMapping,
    Project,
    Question,
    QuestionEmbedding,
    QuestionTagMapping,
    ReviewEvent,
    UploadBatch,
)


def test_delete_project_cascades_project_contents(db):
    project = crud.create_project(db, name="可删除项目")
    batch = UploadBatch(project_id=project.id, original_filename="paper.pdf")
    tag = KnowledgeTag(tag_name="函数", subject="数学")
    db.add_all([batch, tag])
    db.flush()

    question = Question(
        project_id=project.id,
        batch_id=batch.id,
        content_hash="hash-1",
        question_type="选择题",
        content_json="[]",
    )
    note = Note(
        project_id=project.id,
        title="课堂笔记",
        subject="数学",
        content_markdown="函数笔记",
    )
    db.add_all([question, note])
    db.flush()

    db.add_all(
        [
            QuestionTagMapping(question_id=question.id, tag_id=tag.id),
            NoteTagMapping(note_id=note.id, tag_id=tag.id),
            QuestionEmbedding(
                question_id=question.id,
                model_name="test",
                text_hash="text-hash",
                vector_json="[0.1]",
            ),
            ReviewEvent(
                target_type="question",
                target_id=question.id,
                rating="good",
                quality=4,
            ),
            ReviewEvent(
                target_type="note",
                target_id=note.id,
                rating="good",
                quality=4,
            ),
            ChatSession(question_id=question.id, title="题目讲解"),
        ]
    )
    db.commit()
    project_id = project.id
    batch_id = batch.id
    question_id = question.id
    note_id = note.id

    assert crud.delete_project(db, project_id) is True

    assert db.query(Project).filter(Project.id == project_id).count() == 0
    assert db.query(Question).filter(Question.id == question_id).count() == 0
    assert db.query(Note).filter(Note.id == note_id).count() == 0
    assert db.query(UploadBatch).filter(UploadBatch.id == batch_id).count() == 0
    assert db.query(QuestionTagMapping).count() == 0
    assert db.query(NoteTagMapping).count() == 0
    assert db.query(QuestionEmbedding).count() == 0
    assert db.query(ReviewEvent).count() == 0

    chat = db.query(ChatSession).one()
    assert chat.question_id is None
